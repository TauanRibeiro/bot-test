import threading
import time
import random
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from chatbot_automator import ChatbotAutomator
import csv

logger = logging.getLogger(__name__)

class BotManager:
    """Manages lifecycle of the stress bot (start/stop, loop, resilience)."""

    def __init__(self,
                 url: str,
                 questions_file: str,
                 interval_seconds: float = 3.0,
                 jitter: float = 0.5,
                 restart_delay: float = 10.0,
                 headless: bool = False,
                 wait_for_manual_login: bool = True,
                 manual_login_wait_seconds: int = 120,
                 capture_responses: bool = True,
                 log_dir: str = "logs",
                 messages_csv: str = "messages.csv",
                 selectors: Optional[dict] = None):
        self.url = url
        self.questions_file = Path(questions_file)
        self.interval_seconds = interval_seconds
        self.jitter = jitter
        self.restart_delay = restart_delay
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._automator: Optional[ChatbotAutomator] = None
        self._messages_sent = 0
        self._last_error: Optional[str] = None
        self._last_message: Optional[str] = None
        self._last_response: Optional[str] = None
        self._started_at: Optional[datetime] = None
        self._questions_cache: List[str] = []
        self._errors_count: int = 0
        self._last_sent_at: Optional[datetime] = None
        self.headless = headless
        self.wait_for_manual_login = wait_for_manual_login
        self.manual_login_wait_seconds = manual_login_wait_seconds
        self.capture_responses = capture_responses
        self.log_dir = Path(log_dir)
        self.messages_csv = self.log_dir / messages_csv
        self.selectors = selectors or {}
        self.log_dir.mkdir(parents=True, exist_ok=True)
        if not self.messages_csv.exists():
            with self.messages_csv.open('w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp_utc","message","response"])  # header

    def load_questions(self) -> List[str]:
        try:
            lines = [l.strip() for l in self.questions_file.read_text(encoding='utf-8').splitlines() if l.strip()]
            if lines:
                self._questions_cache = lines
            return self._questions_cache
        except Exception as e:
            logger.error(f"Failed to load questions: {e}")
            return self._questions_cache or ["Olá, tudo bem?"]

    def start(self) -> bool:
        with self._lock:
            if self.is_running:
                return False
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            self._started_at = datetime.utcnow()
            logger.info("BotManager started")
            return True

    def stop(self) -> None:
        with self._lock:
            self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        self._cleanup_driver()
        logger.info("BotManager stopped")

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._stop_event.is_set()

    def status(self) -> dict:
        uptime = None
        if self._started_at:
            uptime = (datetime.utcnow() - self._started_at).total_seconds()
        return {
            "running": self.is_running,
            "messages_sent": self._messages_sent,
            "last_message": self._last_message,
            "last_error": self._last_error,
            "last_response": self._last_response,
            "uptime_seconds": uptime,
            "interval_seconds": self.interval_seconds,
            "jitter": self.jitter,
            "errors_count": self._errors_count,
            "last_sent_at": self._last_sent_at.isoformat() if self._last_sent_at else None,
        }

    def _init_driver(self) -> bool:
        try:
            self._automator = ChatbotAutomator(
                self.url,
                headless=self.headless,
                selectors=self.selectors,
                wait_for_manual_login=self.wait_for_manual_login,
                manual_login_wait_seconds=self.manual_login_wait_seconds
            )
            return self._automator.start()
        except Exception as e:
            self._last_error = f"Driver init failed: {e}"
            logger.exception(self._last_error)
            return False

    def _cleanup_driver(self):
        if self._automator:
            try:
                self._automator.close()
            except Exception:
                pass
            self._automator = None

    def _run_loop(self):
        self.load_questions()
        if not self._init_driver():
            time.sleep(self.restart_delay)
        while not self._stop_event.is_set():
            try:
                if not self._automator:
                    if not self._init_driver():
                        time.sleep(self.restart_delay)
                        continue
                q_list = self.load_questions()
                message = random.choice(q_list)
                response = self._automator.send_message(message)
                self._messages_sent += 1
                self._last_message = message
                self._last_sent_at = datetime.utcnow()
                if self.capture_responses:
                    self._last_response = response
                    try:
                        with self.messages_csv.open('a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                datetime.utcnow().isoformat(),
                                message,
                                (response or '').replace('\n',' ').strip()
                            ])
                    except Exception as log_err:
                        logger.error(f"Erro gravando CSV: {log_err}")
                base = self.interval_seconds
                jitter = random.uniform(-self.jitter, self.jitter)
                delay = max(0.5, base + jitter)
                for _ in range(int(delay * 10)):
                    if self._stop_event.is_set():
                        break
                    time.sleep(0.1)
            except Exception as e:
                self._last_error = str(e)
                self._errors_count += 1
                logger.exception(f"Loop error: {e}")
                self._cleanup_driver()
                time.sleep(self.restart_delay)
        self._cleanup_driver()

    def metrics(self) -> dict:
        now = datetime.utcnow()
        uptime_sec = (now - self._started_at).total_seconds() if self._started_at else 0
        avg_interval = (uptime_sec / self._messages_sent) if self._messages_sent > 0 else None
        messages_per_min = (self._messages_sent / (uptime_sec / 60)) if uptime_sec > 0 and self._messages_sent > 0 else 0
        return {
            "uptime_seconds": uptime_sec,
            "messages_sent": self._messages_sent,
            "errors_count": self._errors_count,
            "avg_interval_seconds": avg_interval,
            "messages_per_min": messages_per_min,
            "last_sent_at": self._last_sent_at.isoformat() if self._last_sent_at else None,
            "running": self.is_running
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = BotManager(url="https://aprender2teste.unb.br/my/", questions_file="questions.txt")
    manager.start()
    try:
        while True:
            time.sleep(5)
            print(manager.status())
    except KeyboardInterrupt:
        manager.stop()
