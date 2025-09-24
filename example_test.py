#!/usr/bin/env python3
"""
Example script to demonstrate how to use the Darcy chatbot tester.

This script shows basic usage of the DarcyChatbotTester class for
testing the Darcy chatbot at https://aprender2teste.unb.br/my/.
"""

import sys
import os
from typing import List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.darcy_tester import DarcyChatbotTester


def run_basic_chatbot_test():
    """Run a basic test conversation with the Darcy chatbot."""
    print("🤖 Starting Darcy Chatbot Test...")
    
    # Test messages to send
    test_messages = [
        "Olá, Darcy!",
        "Qual é o seu nome?",
        "Como posso me matricular em disciplinas na UnB?",
        "Quais são os horários da biblioteca central?",
        "Obrigado pela ajuda!"
    ]
    
    # Initialize chatbot tester (set headless=False to see the browser)
    with DarcyChatbotTester(headless=True) as tester:
        print(f"🌐 Testing chatbot at: {tester.base_url}")
        
        # Run the conversation test
        results = tester.test_chatbot_conversation(test_messages)
        
        # Display results
        print(f"\n📊 Test Results:")
        print(f"Success: {'✅' if results['success'] else '❌'}")
        print(f"Total messages: {len(test_messages)}")
        print(f"Errors: {len(results['errors'])}")
        
        if results['errors']:
            print(f"\n❌ Errors encountered:")
            for error in results['errors']:
                print(f"  - {error}")
        
        print(f"\n💬 Conversation:")
        for i, turn in enumerate(results['conversation'], 1):
            print(f"\n{i}. User: {turn['message']}")
            if turn['response']:
                response_preview = turn['response'][:100] + "..." if len(turn['response']) > 100 else turn['response']
                print(f"   Bot: {response_preview}")
                print(f"   Status: {'✅' if turn['success'] else '❌'}")
            else:
                print(f"   Bot: No response received")
                print(f"   Status: ❌")
        
        print(f"\n🏁 Test completed!")
        return results['success']


def run_interactive_test():
    """Run an interactive test where user can type messages."""
    print("🤖 Interactive Darcy Chatbot Test")
    print("Type 'quit' to exit")
    
    with DarcyChatbotTester(headless=False) as tester:  # Show browser for interactive
        if not tester.navigate_to_chatbot():
            print("❌ Failed to navigate to chatbot page")
            return
        
        print("✅ Connected to chatbot! You can now type messages.")
        
        while True:
            message = input("\nYou: ").strip()
            
            if message.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not message:
                continue
            
            print("📤 Sending message...")
            if tester.send_message_to_chatbot(message):
                print("⏳ Waiting for response...")
                response = tester.get_chatbot_response()
                if response:
                    print(f"🤖 Darcy: {response}")
                else:
                    print("❌ No response received")
            else:
                print("❌ Failed to send message")


def main():
    """Main function to run tests."""
    print("=" * 60)
    print("🎓 DARCY CHATBOT TESTING SUITE")
    print("   Testing environment: https://aprender2teste.unb.br/my/")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        run_interactive_test()
    else:
        success = run_basic_chatbot_test()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()