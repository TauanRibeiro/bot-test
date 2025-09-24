from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class ChatbotAutomator:
    """Encapsula a interação com o chatbot via Selenium."""

    def __init__(self, url: str, *, headless: bool = False, selectors: Optional[Dict] = None,
                 wait_for_manual_login: bool = False, manual_login_wait_seconds: int = 120):
        self.url = url
        self.driver: Optional[webdriver.Chrome] = None
        self.headless = headless
        self.selectors = selectors or {}
        self.wait_for_manual_login = wait_for_manual_login
        self.manual_login_wait_seconds = manual_login_wait_seconds

    def start(self) -> bool:
        try:
            options = Options()
            if self.headless:
                options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(60)
            self.driver.get(self.url)
            logger.info("Página carregada: %s", self.url)
            if self.wait_for_manual_login:
                logger.info("Aguardando login manual (até %s s)...", self.manual_login_wait_seconds)
                self._countdown(self.manual_login_wait_seconds)
            return True
        except Exception as e:
            logger.exception("Erro iniciando WebDriver: %s", e)
            return False

    def _countdown(self, seconds: int):
        for _ in range(seconds):
            if not self.driver:
                break
            time.sleep(1)

    def _switch_into_iframe(self):
        iframe_id = self.selectors.get('iframe_id', 'tool_content')
        WebDriverWait(self.driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, iframe_id))
        )

    def send_message(self, message: str) -> Optional[str]:
        if not self.driver:
            logger.warning("Driver não iniciado.")
            return None
        response_text = None
        try:
            self.driver.switch_to.default_content()
            self._switch_into_iframe()
            input_tag = self.selectors.get('input_tag', 'textarea')
            chat_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, input_tag))
            )
            chat_input.send_keys(message)
            chat_input.send_keys(Keys.RETURN)
            logger.info("Mensagem enviada: %s", message)
            # Tentar capturar resposta se configurado
            if self.selectors:
                response_text = self._capture_last_response()
            return response_text
        except Exception as e:
            logger.exception("Erro enviando mensagem: %s", e)
            return None
        finally:
            try:
                self.driver.switch_to.default_content()
            except Exception:
                pass

    def _capture_last_response(self) -> Optional[str]:
        try:
            messages_container_css = self.selectors.get('messages_container_css')
            message_item_css = self.selectors.get('message_item_css')
            if not (messages_container_css and message_item_css):
                return None
            # Já estamos dentro do iframe
            container = self.driver.find_elements(By.CSS_SELECTOR, messages_container_css)
            if not container:
                return None
            items = self.driver.find_elements(By.CSS_SELECTOR, message_item_css)
            if not items:
                return None
            last = items[-1]
            text = last.text.strip()
            logger.debug("Última resposta capturada: %s", text)
            return text
        except Exception:
            return None

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser fechado.")
            finally:
                self.driver = None

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    automator = ChatbotAutomator(
        "https://aprender2teste.unb.br/my/",
        headless=False,
        selectors={
            'iframe_id': 'tool_content',
            'input_tag': 'textarea'
        },
        wait_for_manual_login=True,
        manual_login_wait_seconds=30
    )
    if automator.start():
        automator.send_message("Olá, Darcy!")
        time.sleep(5)
        automator.close()
