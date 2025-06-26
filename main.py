from fastapi import FastAPI
from pydantic import BaseModel

app =FastAPI()

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str

class Message(BaseModel):
    username: str
    content: str

@app.get("/")
async def root():
    return {"message": "Chatbox API"}