from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from .database import init_db, get_db, UserDB
from sqlalchemy.orm import Session
from .auth import hash_password,create_access_token,get_current_user, verify_password
import time

app =FastAPI()

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str

class Message(BaseModel):
    username: str
    content: str

init_db()

@app.get("/")
async def create_user(user: UserCreate,db: Session = Depends(get_db)):
    if db.query(UserDB).filter(UserDB.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    hash
    db_user = UserDB(username=user.username, hashed_password=hash_password)
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

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Chat"}