# ws_test.py
import asyncio
import websockets

async def test_ws():
    uri = "ws://localhost:8000/ws/dispatcher"
    async with websockets.connect(uri) as websocket:
        await websocket.send('{"type": "ping"}')
        resp = await websocket.recv()
        print(resp)

asyncio.run(test_ws())
