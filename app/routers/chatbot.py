from fastapi import APIRouter
from app.models.schema import KakaoRequest
from app.llm.gemini import generate_answer


router = APIRouter()

@router.post("/kakao/webhook")
async def kakao_webhook(data: KakaoRequest):
    user_msg = data.userRequest.utterance
    gemini_answer = generate_answer(user_msg)
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {"text": gemini_answer}
                }
            ]
        }
    }
