#!/usr/bin/env python3
"""
Installation script for AI Document Auditing System dependencies.
This script installs all required dependencies for both backend and frontend.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def install_python_dependencies():
    """Install Python dependencies."""
    print("🐍 Installing Python dependencies...")
    
    # Install from requirements.txt
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", 
                      "Installing Python packages from requirements.txt"):
        return False
    
    # Install spaCy model
    if not run_command(f"{sys.executable} -m spacy download en_core_web_sm", 
                      "Downloading spaCy English model"):
        print("⚠️  Warning: spaCy model download failed. You may need to install it manually.")
    
    return True


def install_frontend_dependencies():
    """Install frontend dependencies."""
    print("🌐 Installing frontend dependencies...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Check if npm is available
    try:
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ npm not found. Please install Node.js and npm first.")
        return False
    
    # Install npm dependencies
    if not run_command("cd frontend && npm install", 
                      "Installing npm packages"):
        return False
    
    return True


def create_directories():
    """Create necessary directories."""
    print("📁 Creating necessary directories...")
    
    directories = [
        "data",
        "data/knowledge_bases",
        "data/generated_articles", 
        "data/validation_results",
        "data/logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def check_environment():
    """Check if the environment is properly set up."""
    print("🔍 Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Check if key packages are importable
    try:
        import fastapi
        print("✅ FastAPI is available")
    except ImportError:
        print("❌ FastAPI not found")
        return False
    
    try:
        import spacy
        print("✅ spaCy is available")
    except ImportError:
        print("❌ spaCy not found")
        return False
    
    return True


def main():
    """Main installation function."""
    print("🚀 AI Document Auditing System - Dependency Installation")
    print("=" * 60)
    
    # Create directories
    create_directories()
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Python dependency installation failed")
        sys.exit(1)
    
    # Install frontend dependencies
    if not install_frontend_dependencies():
        print("❌ Frontend dependency installation failed")
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Installation completed successfully!")
    print("=" * 60)
    
    print("\n📋 Next Steps:")
    print("1. Configure your API keys in .env file")
    print("2. Start the backend server: python backend_server.py")
    print("3. Start the frontend: cd frontend && npm run dev")
    print("4. Visit http://localhost:3000 to use the application")
    
    print("\n🔧 Alternative CLI usage:")
    print("python -m src.cli.main --help")


if __name__ == "__main__":
    main()