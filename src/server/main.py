import asyncio
import websockets
import cv2
import base64

async def video_stream(websocket, path):
    cap = cv2.VideoCapture(0)  # Use your camera feed here
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        _, buffer = cv2.imencode('.jpg', frame)
        encoded_frame = base64.b64encode(buffer).decode('utf-8')
        
        await websocket.send(encoded_frame)
        await asyncio.sleep(0.05)  # Adjust based on your camera's FPS

start_server = websockets.serve(video_stream, "0.0.0.0", 9999)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()