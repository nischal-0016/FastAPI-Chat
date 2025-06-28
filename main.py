from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import init_db, get_db, UserDB, MessageDB
from auth import hash_password, create_access_token, get_current_user, verify_password
import time

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str

class Message(BaseModel):
    username: str
    content: str

init_db()

active_connections = []

@app.post("/users/", response_model=User)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(UserDB).filter(UserDB.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_password = hash_password(user.password)
    db_user = UserDB(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"username": db_user.username}

@app.post("/token")
async def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.websocket("/chat")
async def chat_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    user = get_current_user(token=token, db=db)
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            message = Message(username=user.username, content=data["content"])
            db_message = MessageDB(username=message.username, content=message.content, timestamp=time.time())
            db.add(db_message)
            db.commit()
            for connection in active_connections:
                await connection.send_json({"username": message.username, "content": message.content})
    except Exception as e:
        print("WebSocket disconnected:", e)
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        try:
            await websocket.close()
        except RuntimeError:
            pass  


@app.get("/messages/", response_model=list[Message])
async def get_messages(db: Session = Depends(get_db)):
    messages = db.query(MessageDB).all()
    return [{"username": m.username, "content": m.content} for m in messages]

@app.get("/")
async def root():
    return {"message": "Chat API"}