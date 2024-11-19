import asyncio
import websockets 
import json 

#in memory list for managing connected websocket clients in this cluster 

subscribers = set() 

async def handle_client(websocket, path):
    subscribers.add(websocket)
    try:
        while True:
            await asyncio.sleep(3000) #stimulating active connection 
    
    except websockets.exceptions.ConnectionClosed:
        pass

    finally:
        subscribers.remove(websocket)

async def broadcast_emoji_data(emoji_data):
    for websocket in subscribers:
        try: 
            await websocket.send(json.dumps(emoji_data))
        except websockets.exceptions.ConnectionClosed:
            subscribers.remove(websocket)

async def start_websocket_server():
    server = await websockets.serve(handle_client, "localhost", 8765)
    print("Websockets server started!\n")
    await server.wait_closed()

"""
This could be used if multiple servers needed: 
    
async def start_multiple_websocket_servers():
    server1 = await websockets.serve(handle_client, "localhost", 8765)
    server2 = await websockets.serve(handle_client, "localhost", 8766)
    await server1.wait_closed()
    await server2.wait_closed()
"""

if __name__ == "__main__":
    asyncio.run(start_websocket_server())
    # asyncio.run(start_multiple_websocket_servers()) this can be used if multiple servers again. 
