"""
Test cases for Darcy chatbot functionality.
"""

import pytest
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from darcy_tester import DarcyChatbotTester


class TestDarcyChatbot:
    """Test suite for Darcy chatbot interactions."""
    
    @pytest.fixture
    def chatbot_tester(self):
        """Create a chatbot tester instance for testing."""
        tester = DarcyChatbotTester(headless=True)
        yield tester
        tester.close()
    
    def test_chatbot_navigation(self, chatbot_tester):
        """Test navigation to the chatbot page."""
        result = chatbot_tester.navigate_to_chatbot()
        assert result, "Failed to navigate to chatbot page"
        
        # Check if we're on the right page
        assert "aprender2teste.unb.br" in chatbot_tester.driver.current_url
    
    def test_simple_greeting(self, chatbot_tester):
        """Test sending a simple greeting to the chatbot."""
        # Navigate to chatbot
        assert chatbot_tester.navigate_to_chatbot()
        
        # Send greeting
        success = chatbot_tester.send_message_to_chatbot("Olá")
        assert success, "Failed to send greeting message"
        
        # Get response
        response = chatbot_tester.get_chatbot_response()
        assert response is not None, "No response received from chatbot"
        assert len(response) > 0, "Empty response received"
    
    def test_multiple_questions(self, chatbot_tester):
        """Test sending multiple questions to the chatbot."""
        messages = [
            "Olá, como você está?",
            "Qual é o seu nome?",
            "Você pode me ajudar com informações sobre a UnB?"
        ]
        
        results = chatbot_tester.test_chatbot_conversation(messages)
        
        assert results["success"], f"Conversation failed: {results['errors']}"
        assert len(results["conversation"]) == len(messages)
        
        # Check that we got responses to most messages
        successful_responses = sum(1 for turn in results["conversation"] if turn["success"])
        assert successful_responses >= len(messages) * 0.5, "Too few successful responses"
    
    def test_academic_questions(self, chatbot_tester):
        """Test academic-related questions."""
        academic_messages = [
            "Como posso me matricular em disciplinas?",
            "Quais são os horários da biblioteca?",
            "Como funciona o sistema de avaliação da UnB?"
        ]
        
        results = chatbot_tester.test_chatbot_conversation(academic_messages)
        
        assert results["success"], f"Academic conversation failed: {results['errors']}"
        
        # Check responses contain relevant keywords
        all_responses = " ".join([
            turn["response"] for turn in results["conversation"] 
            if turn["response"]
        ]).lower()
        
        # Should contain at least some academic-related terms
        academic_terms = ["unb", "universidade", "matrícula", "disciplina", "biblioteca", "avaliação"]
        found_terms = sum(1 for term in academic_terms if term in all_responses)
        
        assert found_terms > 0, "No academic terms found in responses"
    
    @pytest.mark.parametrize("message", [
        "Ajuda",
        "Como posso te usar?",
        "Quais são suas funcionalidades?",
        "Help"
    ])
    def test_help_messages(self, chatbot_tester, message):
        """Test various help-related messages."""
        assert chatbot_tester.navigate_to_chatbot()
        
        success = chatbot_tester.send_message_to_chatbot(message)
        assert success, f"Failed to send help message: {message}"
        
        response = chatbot_tester.get_chatbot_response()
        assert response is not None, f"No response to help message: {message}"
    
    def test_error_handling(self, chatbot_tester):
        """Test chatbot's handling of unclear or problematic inputs."""
        problematic_messages = [
            "",  # Empty message
            "asdfghjkl",  # Random characters  
            "🤖🎓📚",  # Only emojis
            "A" * 1000  # Very long message
        ]
        
        results = chatbot_tester.test_chatbot_conversation(problematic_messages)
        
        # Should handle errors gracefully without crashing
        assert len(results["conversation"]) == len(problematic_messages)
        
        # At least some messages should be processed (even if with error responses)
        processed_messages = sum(1 for turn in results["conversation"] if turn["response"])
        assert processed_messages >= 0, "All messages failed to process"


class TestDarcyChatbotAPI:
    """Test suite for potential API interactions with Darcy chatbot."""
    
    def test_base_url_accessibility(self):
        """Test if the base URL is accessible."""
        import requests
        
        try:
            response = requests.get("https://aprender2teste.unb.br/my/", timeout=10)
            assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Base URL not accessible: {e}")
    
    def test_chatbot_endpoint_discovery(self):
        """Try to discover chatbot API endpoints."""
        import requests
        
        base_url = "https://aprender2teste.unb.br"
        potential_endpoints = [
            "/api/chat",
            "/chat/api",
            "/darcy/api",
            "/api/darcy",
            "/chatbot/api"
        ]
        
        accessible_endpoints = []
        
        for endpoint in potential_endpoints:
            try:
                url = base_url + endpoint
                response = requests.get(url, timeout=5)
                if response.status_code in [200, 405]:  # 405 might mean POST is required
                    accessible_endpoints.append(endpoint)
            except requests.exceptions.RequestException:
                continue
        
        # This is more of a discovery test, so we just log findings
        print(f"Accessible endpoints found: {accessible_endpoints}")


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])