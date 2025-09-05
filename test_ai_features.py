#!/usr/bin/env python3
"""
Interactive test script to demonstrate Gemini AI edge case handling
"""

from medical_agent_simple import EnhancedMedicalAgent

def test_conversation_flow():
    """Test the complete conversation flow with edge cases"""
    
    print("🤖 Interactive Gemini AI Edge Case Demo")
    print("=" * 50)
    
    agent = EnhancedMedicalAgent()
    
    # Simulate a complete conversation flow
    print("\n🎭 SCENARIO 1: User with complex symptoms")
    print("-" * 30)
    
    # Step 1: Greeting
    response = agent.process_conversation("Hello, I need help")
    print(f"Agent: {response[:100]}...")
    
    # Step 2: Provide name
    response = agent.process_conversation("My name is John Smith")
    print(f"Agent: {response[:100]}...")
    
    # Step 3: Provide complex symptoms (Edge Case Test)
    response = agent.process_conversation("I have chest pain, difficulty breathing, and heart palpitations")
    print(f"Agent: {response[:200]}...")
    
    # Check if AI recommendations are working
    if 'cardiology' in response.lower():
        print("✅ AI correctly identified need for cardiology!")
    
    print("\n🎭 SCENARIO 2: Testing 'show all doctors' edge case")
    print("-" * 30)
    
    # Reset agent
    agent = EnhancedMedicalAgent()
    agent.conversation_context['step'] = 'showing_doctors'
    agent.conversation_context['patient_info'] = {
        'first_name': 'Jane',
        'symptoms': 'general checkup'
    }
    
    # Test edge case: user asks to see all doctors
    response = agent.process_conversation("show me all available doctors please")
    doctor_count = response.count("Dr.")
    print(f"Agent showed {doctor_count} doctors")
    print("✅ Enhanced doctor display working!" if doctor_count > 10 else "❌ Limited doctor display")
    
    print("\n🎭 SCENARIO 3: Testing specialty matching edge case")
    print("-" * 30)
    
    # Test specialty request handling
    response = agent.handle_specialty_request("I need someone for my heart problems")
    if 'cardiology' in response.lower():
        print("✅ AI specialty matching working!")
    print(f"Specialty response: {response[:150]}...")
    
    print("\n🎭 SCENARIO 4: Testing confused user edge case")
    print("-" * 30)
    
    # Test general query with AI
    response = agent._handle_general_query("I'm completely lost and don't know what I need")
    print(f"AI Response: {response[:200]}...")
    
    if any(word in response.lower() for word in ['help', 'options', 'schedule']):
        print("✅ AI providing helpful guidance!")
    
    print("\n📋 MANUAL TESTING GUIDE for Streamlit App:")
    print("=" * 50)
    print("1. Start the app: streamlit run app.py")
    print("2. Test these specific edge cases in order:")
    print()
    print("   🔸 EDGE CASE 1: Complex symptoms")
    print("   Type: 'Hello' → Enter your name → Enter: 'chest pain and breathing issues'")
    print("   Expected: Should recommend cardiology specialists")
    print()
    print("   🔸 EDGE CASE 2: All doctors request")
    print("   After symptoms, type: 'show me all doctors'")
    print("   Expected: Should display all 28 doctors by specialty")
    print()
    print("   🔸 EDGE CASE 3: Confused user")
    print("   Type: 'I don't know what I need help'")
    print("   Expected: AI should provide helpful options")
    print()
    print("   🔸 EDGE CASE 4: Specialty request")
    print("   Type: 'I need a heart doctor'")
    print("   Expected: Should show cardiology specialists")
    print()
    print("   🔸 EDGE CASE 5: Misspelled medical terms")
    print("   Type: 'I need a dermatoligist for skinn problems'")
    print("   Expected: AI should understand and suggest dermatology")
    
    print("\n🔍 HOW TO VERIFY GEMINI AI IS WORKING:")
    print("=" * 40)
    print("✅ Look for detailed, context-aware responses (>100 words)")
    print("✅ Check if AI explains why certain specialists are recommended")
    print("✅ Verify that all 28 doctors are shown when requested")
    print("✅ Test if AI understands misspelled or complex medical terms")
    print("✅ Confirm AI provides helpful options when user is confused")
    print("✅ Check if emergency/urgent language gets appropriate responses")

if __name__ == "__main__":
    test_conversation_flow()
