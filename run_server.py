#!/usr/bin/env python3
"""
Simple script to run the FastAPI backend server with uvicorn.
Usage: python run_server.py [--port PORT] [--host HOST]
"""
import subprocess
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run HVAC Dispatch API")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    args = parser.parse_args()
    
    print(f"Starting HVAC Dispatch API on {args.host}:{args.port}...")
    print(f"  📖 Swagger UI: http://{args.host}:{args.port}/docs")
    print(f"  📚 ReDoc: http://{args.host}:{args.port}/redoc")
    print(f"  🔌 WebSocket (dispatcher): ws://{args.host}:{args.port}/ws/dispatcher")
    print(f"  🔌 WebSocket (tech): ws://{args.host}:{args.port}/ws/tech/{{tech_id}}")
    print()
    
    reload_flag = ["--reload"] if args.reload else []
    cmd = [
        "uvicorn",
        "backend.api:app",
        f"--host={args.host}",
        f"--port={args.port}",
    ] + reload_flag
    
    try:
        subprocess.run(cmd, cwd="/Users/tanayshah/my_project/tech-to-customer")
    except KeyboardInterrupt:
        print("\n\n✋ Server stopped.")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
