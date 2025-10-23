#!/usr/bin/env python3
"""
Firebase Authentication Quick Setup
Opens Firebase Console and provides step-by-step guidance
"""

import webbrowser
import time

def open_firebase_console():
    """Open Firebase Console in browser"""
    
    print("🔥 Firebase Authentication Quick Setup")
    print("=" * 50)
    
    project_id = "infinity-ai-5ec7c"
    
    # URLs for setup
    urls = {
        "auth_main": f"https://console.firebase.google.com/project/{project_id}/authentication",
        "sign_in_methods": f"https://console.firebase.google.com/project/{project_id}/authentication/providers",
        "users": f"https://console.firebase.google.com/project/{project_id}/authentication/users"
    }
    
    print("🌐 Opening Firebase Console...")
    print("📝 Follow these steps in the browser that opens:\n")
    
    # Step-by-step instructions
    steps = [
        {
            "step": 1,
            "title": "Initialize Authentication",
            "url": urls["auth_main"],
            "instructions": [
                "Look for 'Get Started' button",
                "Click 'Get Started' to initialize Authentication",
                "Wait for initialization to complete"
            ]
        },
        {
            "step": 2, 
            "title": "Enable Email/Password Provider",
            "url": urls["sign_in_methods"],
            "instructions": [
                "Click on 'Sign-in method' tab",
                "Find 'Email/Password' in the list",
                "Click on 'Email/Password'",
                "Toggle 'Enable' to ON",
                "Click 'Save'"
            ]
        },
        {
            "step": 3,
            "title": "Create Test User (Optional)",
            "url": urls["users"],
            "instructions": [
                "Click on 'Users' tab",
                "Click 'Add User' button",
                "Email: raghu42620@gmail.com",
                "Password: Choose a secure password",
                "Click 'Add User'"
            ]
        }
    ]
    
    for step_info in steps:
        print(f"📋 STEP {step_info['step']}: {step_info['title']}")
        print(f"🌐 URL: {step_info['url']}")
        print("📝 Instructions:")
        for instruction in step_info['instructions']:
            print(f"   • {instruction}")
        print()
        
        if step_info['step'] == 1:
            # Open the first URL automatically
            print("🔄 Opening Firebase Console...")
            try:
                webbrowser.open(step_info['url'])
                print("✅ Browser opened to Firebase Authentication")
            except:
                print("❌ Could not open browser automatically")
                print(f"📖 Please manually go to: {step_info['url']}")
        
        input("⏳ Press ENTER when you've completed this step...")
        print()
    
    print("🎉 Setup Complete!")
    print("=" * 50)
    print("✅ Firebase Authentication should now be configured")
    print("🔄 Test your login at: https://infinity-ai-5ec7c.web.app/login")
    print("🔍 Run verification: python verify_firebase_auth.py")

def main():
    """Main setup function"""
    
    print("🚀 InfinityAI.Pro - Firebase Authentication Setup")
    print("=" * 60)
    print("This will guide you through setting up Firebase Authentication")
    print("to fix the 'auth/configuration-not-found' error.\n")
    
    response = input("🤔 Ready to start Firebase Auth setup? (y/n): ").lower()
    
    if response in ['y', 'yes']:
        print("\n🚀 Starting setup process...")
        open_firebase_console()
    else:
        print("\n📖 Manual Setup Instructions:")
        print("1. Go to: https://console.firebase.google.com/project/infinity-ai-5ec7c/authentication")
        print("2. Click 'Get Started' if shown")
        print("3. Enable Email/Password provider") 
        print("4. Test login at: https://infinity-ai-5ec7c.web.app/login")
        print("\n🔍 Run 'python verify_firebase_auth.py' to verify setup")

if __name__ == "__main__":
    main()