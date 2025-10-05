#!/usr/bin/env python3
"""
Serve React Frontend from Backend
=================================

This script serves the React frontend build files directly from the backend
for production deployment.
"""

import os
import shutil
from pathlib import Path

def setup_static_files():
    """Copy React build files to backend static directory"""
    
    # Paths
    frontend_build = Path("frontend/build")
    backend_static = Path("static")
    
    # Create static directory if it doesn't exist
    backend_static.mkdir(exist_ok=True)
    
    if frontend_build.exists():
        # Remove existing static files
        if backend_static.exists():
            shutil.rmtree(backend_static)
        
        # Copy build files
        shutil.copytree(frontend_build, backend_static)
        print(f"✅ Copied React build files from {frontend_build} to {backend_static}")
        
        # List copied files
        static_files = list(backend_static.rglob("*"))
        print(f"📁 Total files copied: {len(static_files)}")
        
        return True
    else:
        print(f"❌ Frontend build directory not found: {frontend_build}")
        print("💡 Run 'cd frontend && npm run build' first")
        return False

if __name__ == "__main__":
    success = setup_static_files()
    if success:
        print("\n🚀 Frontend files ready for serving!")
        print("📱 React app will be available at the backend URL")
    else:
        print("\n❌ Setup failed!")