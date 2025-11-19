#!/usr/bin/env python3
"""
Quick WebSocket connectivity test
Run: python3 test_websocket.py

Before running this test, make sure the API server is running:
  python3 run_server.py
or
  uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
"""
import asyncio
import websockets
import json
import sys

async def test_dispatcher_websocket():
    """Test dispatcher WebSocket connection"""
    print("Testing /ws/dispatcher...")
    uri = "ws://localhost:8000/ws/dispatcher"
    
    try:
        async with websockets.connect(uri) as websocket:
            # Receive connection message
            msg = await asyncio.wait_for(websocket.recv(), timeout=2)
            data = json.loads(msg)
            print(f"✅ Connected! Server said: {data}")
            
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            pong = await asyncio.wait_for(websocket.recv(), timeout=2)
            print(f"✅ Ping/Pong works: {json.loads(pong)}")
            
            return True
    except asyncio.TimeoutError:
        print(f"❌ Timeout waiting for response from server")
        return False
    except ConnectionRefusedError:
        print(f"❌ WebSocket connection refused. Is the API running on localhost:8000?")
        print(f"   Start with: python3 run_server.py")
        return False
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        print(f"   Make sure the API is running on localhost:8000")
        return False

async def test_tech_websocket(tech_id: int = 1):
    """Test tech WebSocket connection"""
    print(f"\nTesting /ws/tech/{tech_id}...")
    uri = f"ws://localhost:8000/ws/tech/{tech_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            # Receive connection message
            msg = await asyncio.wait_for(websocket.recv(), timeout=2)
            data = json.loads(msg)
            print(f"✅ Connected! Server said: {data}")
            
            return True
    except asyncio.TimeoutError:
        print(f"❌ Timeout waiting for response")
        return False
    except ConnectionRefusedError:
        print(f"❌ Connection refused. Is the API running on localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

async def main():
    print("=" * 60)
    print("WebSocket Connectivity Test")
    print("=" * 60)
    
    dispatcher_ok = await test_dispatcher_websocket()
    tech_ok = await test_tech_websocket(1)
    
    print("\n" + "=" * 60)
    if dispatcher_ok and tech_ok:
        print("✅ All WebSocket tests passed!")
        sys.exit(0)
    else:
        print("❌ Some WebSocket tests failed")
        print("\nMake sure the API server is running:")
        print("  cd /Users/tanayshah/my_project/tech-to-customer")
        print("  source .venv/bin/activate")
        print("  python3 run_server.py")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

