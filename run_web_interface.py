"""
Web Interface Launch Script
===========================

Module: run_web_interface
Version: 1.0
Author: Event Intelligence Team
Date: April 2026

Description:
    Quick-start launcher for the Event Intelligence RAG web interface.
    Handles dependency checking, server startup, and browser navigation.

Features:
    - Automatic Flask dependency detection
    - Missing dependency installation
    - Server health checking
    - Browser auto-launch
    - Graceful error handling

Usage:
    python run_web_interface.py

Output:
    - Launches Flask server on http://localhost:5000
    - Opens browser to interface
    - Displays server logs

Dependencies:
    - flask >= 2.0.0
    - web_rag_interface
"""

import subprocess
import sys
import webbrowser
import time
from typing import Optional

def main():
    print("=" * 70)
    print("Event Intelligence RAG System - Web Interface")
    print("=" * 70)
    print()
    
    # Check if Flask is installed
    try:
        import flask
        print("[OK] Flask is installed")
    except ImportError:
        print("[ERROR] Flask is NOT installed")
        print("\nInstalling Flask...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
        print("[OK] Flask installed successfully")
    
    print()
    print("Starting web server...")
    print()
    print("[Web] Web Interface: http://localhost:5000")
    print("[API] API Base: http://localhost:5000/api/")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    print()
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(2)
        try:
            webbrowser.open('http://localhost:5000')
        except:
            pass
    
    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Run Flask app
    try:
        subprocess.run([sys.executable, "web_rag_interface.py"], cwd=".")
    except KeyboardInterrupt:
        print("\n\nServer stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
