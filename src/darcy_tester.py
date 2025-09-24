"""
Base class for Darcy chatbot interactions and utilities.

This module provides the foundation for testing the Darcy chatbot
with web automation capabilities.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests
import logging
from typing import Optional, Dict, Any
import time


class DarcyChatbotTester:
    """
    Main class for testing the Darcy chatbot at https://aprender2teste.unb.br/my/
    """
    
    def __init__(self, headless: bool = False, timeout: int = 10):
        """
        Initialize the chatbot tester.
        
        Args:
            headless (bool): Run browser in headless mode
            timeout (int): Default timeout for web elements
        """
        self.base_url = "https://aprender2teste.unb.br/my/"
        self.timeout = timeout
        self.driver: Optional[webdriver.Chrome] = None
        self.setup_logging()
        self.setup_driver(headless)
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self, headless: bool = False):
        """
        Setup Chrome WebDriver with appropriate options.
        
        Args:
            headless (bool): Run browser in headless mode
        """
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def navigate_to_chatbot(self) -> bool:
        """
        Navigate to the Darcy chatbot page.
        
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            self.driver.get(self.base_url)
            self.logger.info(f"Navigated to {self.base_url}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to navigate to chatbot: {e}")
            return False
    
    def wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> Any:
        """
        Wait for an element to be present and return it.
        
        Args:
            by (By): Selenium By locator type
            value (str): Element locator value
            timeout (int, optional): Custom timeout
            
        Returns:
            WebElement or None if not found
        """
        wait_time = timeout or self.timeout
        try:
            wait = WebDriverWait(self.driver, wait_time)
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
        except Exception as e:
            self.logger.warning(f"Element not found: {by}='{value}' - {e}")
            return None
    
    def send_message_to_chatbot(self, message: str) -> bool:
        """
        Send a message to the Darcy chatbot.
        
        Args:
            message (str): Message to send
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            # Common chatbot input selectors to try
            input_selectors = [
                "input[type='text']",
                "textarea",
                "[data-testid='chat-input']",
                ".chat-input",
                "#chat-input",
                "[placeholder*='message']",
                "[placeholder*='pergunta']"
            ]
            
            input_element = None
            for selector in input_selectors:
                input_element = self.wait_for_element(By.CSS_SELECTOR, selector, 2)
                if input_element:
                    break
            
            if not input_element:
                self.logger.error("Could not find chat input element")
                return False
            
            # Clear and send message
            input_element.clear()
            input_element.send_keys(message)
            
            # Try to find and click send button
            send_selectors = [
                "button[type='submit']",
                ".send-button",
                "#send-button",
                "[data-testid='send-button']",
                "button:contains('Enviar')",
                "button:contains('Send')"
            ]
            
            send_button = None
            for selector in send_selectors:
                send_button = self.wait_for_element(By.CSS_SELECTOR, selector, 2)
                if send_button:
                    break
            
            if send_button:
                send_button.click()
            else:
                # Try pressing Enter key
                from selenium.webdriver.common.keys import Keys
                input_element.send_keys(Keys.RETURN)
            
            self.logger.info(f"Message sent: {message}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    def get_chatbot_response(self, timeout: Optional[int] = None) -> Optional[str]:
        """
        Get the latest response from the chatbot.
        
        Args:
            timeout (int, optional): Custom timeout
            
        Returns:
            str or None: Latest chatbot response
        """
        wait_time = timeout or self.timeout
        try:
            # Common response selectors
            response_selectors = [
                ".chat-response",
                ".bot-message",
                "[data-testid='bot-response']",
                ".message.bot",
                ".chat-message:last-child"
            ]
            
            time.sleep(2)  # Wait for response to appear
            
            for selector in response_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    response = elements[-1].text.strip()
                    if response:
                        self.logger.info(f"Received response: {response}")
                        return response
            
            self.logger.warning("No chatbot response found")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get chatbot response: {e}")
            return None
    
    def test_chatbot_conversation(self, messages: list) -> Dict[str, Any]:
        """
        Test a full conversation with the chatbot.
        
        Args:
            messages (list): List of messages to send
            
        Returns:
            dict: Test results with messages and responses
        """
        results = {
            "success": False,
            "conversation": [],
            "errors": []
        }
        
        try:
            if not self.navigate_to_chatbot():
                results["errors"].append("Failed to navigate to chatbot")
                return results
            
            for message in messages:
                conversation_turn = {
                    "message": message,
                    "response": None,
                    "success": False
                }
                
                if self.send_message_to_chatbot(message):
                    response = self.get_chatbot_response()
                    conversation_turn["response"] = response
                    conversation_turn["success"] = response is not None
                else:
                    results["errors"].append(f"Failed to send message: {message}")
                
                results["conversation"].append(conversation_turn)
                
                # Small delay between messages
                time.sleep(1)
            
            results["success"] = len(results["errors"]) == 0
            return results
            
        except Exception as e:
            results["errors"].append(f"Conversation test failed: {e}")
            return results
    
    def close(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
            self.logger.info("WebDriver closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()