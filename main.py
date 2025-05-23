import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

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


# embeding model 가져오기
# vector db 1문장 저장


# API - 사용자 문장 입력 (input text/output vector)
# output vector <-> vector db 비교

# RAG 검색

@app.post("/kakao/webhook")
async def kakao_webhook(data: KakaoRequest):
    user_msg = data.userRequest.utterance

    # ✅ Gemini 응답 생성
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(user_msg)

    gemini_answer = response.text.strip()  # 공백 제거
    
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
