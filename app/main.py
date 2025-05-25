from fastapi import FastAPI
from app.routers import chatbot

app = FastAPI()
app.include_router(chatbot.router)