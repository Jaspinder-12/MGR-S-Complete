#!/usr/bin/env python3
import subprocess
import time
import os
import sys

def test_ui():
    print("Testing MGR-S UI...")
    
    try:
        # Start the UI in headless mode (for testing)
        if sys.platform == 'win32':
            # On Windows, we can use a virtual display or just check if the process starts
            ui_process = subprocess.Popen(["python", "mgrs_gui.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="ui", creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            ui_process = subprocess.Popen(["python", "mgrs_gui.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="ui")
        
        # Wait for UI to start
        time.sleep(2)
        
        # Check if process is running
        if ui_process.poll() is not None:
            print("UI failed to start")
            return False
        
        # Stop the UI
        ui_process.terminate()
        try:
            ui_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            ui_process.kill()
        
        print("UI test passed")
        return True
    
    except Exception as e:
        print(f"Error testing UI: {e}")
        return False

if __name__ == "__main__":
    test_ui()
