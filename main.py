import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, FastAPI with Poetry!"}

class UserRequest(BaseModel):
    utterance: str

class KakaoRequest(BaseModel):
    userRequest: UserRequest

@app.post("/kakao/webhook")
async def kakao_webhook(data: KakaoRequest):
    user_msg = data.userRequest.utterance
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": f"서버가 받았어요! 메시지: {user_msg}"
                    }
                }
            ]
        }
    }
