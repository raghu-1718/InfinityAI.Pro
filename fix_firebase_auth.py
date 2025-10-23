#!/usr/bin/env python3
"""
Firebase Authentication Configuration Checker and Setup
"""

import requests
import json
import subprocess
import os

def check_firebase_auth_config():
    """Check Firebase Authentication configuration"""
    
    print("🔥 Firebase Authentication Configuration Check")
    print("=" * 60)
    
    project_id = "infinity-ai-5ec7c"
    
    # Check if Firebase Auth API is enabled
    print("1. Checking Firebase Auth API status...")
    
    try:
        # Try to get Firebase project info
        result = subprocess.run([
            "gcloud", "services", "list", 
            "--filter=name:identitytoolkit.googleapis.com",
            "--project", project_id,
            "--format=json"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            services = json.loads(result.stdout)
            if services:
                print("   ✅ Identity Toolkit API is enabled")
            else:
                print("   ❌ Identity Toolkit API is NOT enabled")
                print("   🔧 Need to enable Identity Toolkit API")
                return False
        else:
            print("   ⚠️ Could not check API status")
            
    except Exception as e:
        print(f"   ❌ Error checking API: {e}")
        
    # Check Authentication configuration
    print("\n2. Checking Authentication providers...")
    
    try:
        # Try to list auth providers
        result = subprocess.run([
            "gcloud", "identity", "providers", "list",
            "--project", project_id,
            "--format=json"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ Can access Identity providers")
        else:
            print("   ❌ Cannot access Identity providers")
            print("   🔧 Authentication may not be properly configured")
            
    except Exception as e:
        print(f"   ⚠️ Could not check providers: {e}")
        
    # Check Firebase config
    print("\n3. Checking Firebase project configuration...")
    
    try:
        result = subprocess.run([
            "firebase", "projects:list", "--json"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            projects = json.loads(result.stdout)
            target_project = None
            for project in projects:
                if project.get('projectId') == project_id:
                    target_project = project
                    break
                    
            if target_project:
                print("   ✅ Firebase project found and accessible")
                print(f"   📝 Project: {target_project.get('displayName', 'Unknown')}")
                print(f"   🆔 Project ID: {target_project.get('projectId')}")
            else:
                print("   ❌ Firebase project not found")
                
        else:
            print("   ❌ Cannot access Firebase projects")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        
    print("\n🎯 RECOMMENDATIONS:")
    print("To fix the auth/configuration-not-found error:")
    print("1. 🌐 Go to Firebase Console: https://console.firebase.google.com/")
    print(f"2. 📂 Select project: {project_id}")
    print("3. 🔐 Go to Authentication > Sign-in method")
    print("4. ✅ Enable Email/Password provider")
    print("5. ✅ Enable any other required providers")
    print("6. 💾 Save configuration")
    print("\nAfter enabling, try the frontend login again.")

def enable_firebase_auth_api():
    """Enable Firebase Authentication API"""
    
    print("\n🔧 Attempting to enable Firebase Authentication API...")
    
    project_id = "infinity-ai-5ec7c"
    
    try:
        # Enable Identity Toolkit API
        result = subprocess.run([
            "gcloud", "services", "enable", 
            "identitytoolkit.googleapis.com",
            "--project", project_id
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("   ✅ Identity Toolkit API enabled successfully")
            return True
        else:
            print(f"   ❌ Failed to enable API: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error enabling API: {e}")
        return False

def main():
    """Main function"""
    
    # Check current configuration
    check_firebase_auth_config()
    
    # Try to enable the API
    print("\n" + "=" * 60)
    if enable_firebase_auth_api():
        print("\n✅ Firebase Authentication API has been enabled!")
        print("🔄 Please now go to Firebase Console to enable sign-in methods.")
    else:
        print("\n⚠️ Could not automatically enable API.")
        print("🌐 Please manually enable in Firebase Console.")

if __name__ == "__main__":
    main()