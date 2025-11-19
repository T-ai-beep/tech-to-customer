import asyncio
import websockets
import json

async def test_dispatcher_websocket():
    uri = "ws://localhost:8000/ws/dispatcher"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to dispatcher WebSocket")
            
            # Receive welcome message
            message = await websocket.recv()
            print(f"📨 Received: {message}")
            
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            print("📤 Sent: ping")
            
            # Receive pong
            message = await websocket.recv()
            print(f"📨 Received: {message}")
            
            # Keep connection alive for 30 seconds
            print("\n⏳ Keeping connection alive for 30 seconds...")
            print("   (In another terminal, try: curl -X POST http://localhost:8000/jobs/1/auto-assign)")
            print("   You should see the broadcast here!\n")
            
            for i in range(30):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"📨 Broadcast received: {message}")
                except asyncio.TimeoutError:
                    pass  # No message, that's okay
            
            print("✅ Test complete")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_dispatcher_websocket())

