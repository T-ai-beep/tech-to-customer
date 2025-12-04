#!/usr/bin/env python3
import subprocess
import sys
import os

def main():
    # Make sure we're in the right directory
    project_root = "/Users/tanayshah/my_project/tech-to-customer"
    os.chdir(project_root)
    
    print("Starting HVAC Dispatch API...")
    print(f"  📖 Swagger UI: http://127.0.0.1:8000/docs")
    print(f"  🔌 WebSocket: ws://127.0.0.1:8000/ws/dispatcher")
    
    cmd = [
        "uvicorn",
        "backend.api:app",  # Note: backend.api, not just api
        "--host=127.0.0.1",
        "--port=8000",
        "--reload"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n✋ Server stopped.")

if __name__ == "__main__":
    main()