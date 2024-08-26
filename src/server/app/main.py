from fastapi import FastAPI
from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

class Note(BaseModel):
    text: str


origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "https://transcendent-buttercream-429178.netlify.app",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Client(BaseModel):
    id: int
    socket: WebSocket

    class Config:
        arbitrary_types_allowed = True

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[Client] = []

    async def connect(self, client: Client):
        await client.socket.accept()
        self.active_connections.append(client)

    def disconnect(self, client: Client):
        self.active_connections.remove(client)

    async def send_personal_message(self, message: str, client_id: int):
        client = next((c for c in self.active_connections if c.id == client_id), None)
        if client:
            await client.socket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.socket.send_text(message)

    async def broadcast_even(self, message: str):
        for connection in self.active_connections:
            if connection.id % 2 == 0:
                await connection.socket.send_text(message)
     
    async def broadcast_odd(self, message: str):
        for connection in self.active_connections:
            if connection.id % 2 != 0:
                await connection.socket.send_text(message)

manager = ConnectionManager()


@app.get("/")
async def root():
    return {"message": "Hello World"}

def parse_note(note: str):
    if note == "Invalid key":
        return 0, "Invalid key"
    # 1/C4
    note = note.split("/")
    return int(note[0]), note[1]

@app.post("/conductor/receive")
async def receive(note: Note):
    n = parse_note(note.text)
    if n[0] % 2 == 0:
        await manager.broadcast_even(n[1])
    elif n[0] % 2 != 0:
        await manager.broadcast_odd(n[1])
    return {"note": n[1], "row": n[0]}

@app.websocket("/swarm/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    client = Client(id=client_id, socket=websocket)
    await manager.connect(client)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(client)
        await manager.broadcast(f"Client #{client_id} left the chat")

@app.get("/conductor/swarm/size")
def get_nodes():
    return {"nodes": len(manager.active_connections)}

@app.get("/conductor/swarm/nodes")
def get_clients():
    return {"clients": [c.id for c in manager.active_connections]}