import tkinter as tk
from tkinter import ttk
import threading
import time
import random
from chatbot_automator import ChatbotAutomator

class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Darcy Chatbot Stress Test")

        self.start_button = ttk.Button(root, text="Iniciar", command=self.start_bot)
        self.start_button.pack(pady=10)

        self.stop_button = ttk.Button(root, text="Parar", command=self.stop_bot, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.status_label = ttk.Label(root, text="Status: Parado")
        self.status_label.pack(pady=5)

        self.bot_thread = None
        self.running = False
        self.automator = None
        self.questions = self.load_questions()

    def load_questions(self):
        try:
            with open("..\\questions.txt", "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return ["Olá, como vai você?"] # Fallback question

    def start_bot(self):
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Rodando...")
        self.bot_thread = threading.Thread(target=self.run_chatbot_logic)
        self.bot_thread.start()

    def stop_bot(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Parando...")
        if self.bot_thread and self.bot_thread.is_alive():
            # The thread will check the `self.running` flag and exit the loop
            self.bot_thread.join() # Wait for the thread to finish
        if self.automator:
            self.automator.close()
            self.automator = None
        self.status_label.config(text="Status: Parado")

    def run_chatbot_logic(self):
        self.automator = ChatbotAutomator("https://aprender2teste.unb.br/my/")
        if not self.automator.start():
            self.status_label.config(text="Status: Erro ao iniciar o WebDriver")
            self.stop_bot()
            return

        while self.running:
            question = random.choice(self.questions)
            self.automator.send_message(question)
            time.sleep(3)
        
        # Clean up when the loop is stopped
        if self.automator:
            self.automator.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()
