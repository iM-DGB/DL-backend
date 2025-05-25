from fastapi import APIRouter
from app.models.schema import UserRequest, KakaoRequest
from app.embedding.kosolar import embed_texts
from app.llm.gemini import generate_answer

router = APIRouter()

@router.post("/embed")
async def embed_endpoint(data: UserRequest):
    vector = embed_texts([data.utterance])[0]
    return {"length": len(vector), "sample": vector[:5]}

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

from app.vectorstore.sample_store import build_sample_vector_store, search_similar_sentence

# 서버 시작 시 한 번만 샘플 벡터 저장
build_sample_vector_store()

@router.post("/test-query")
async def test_query(data: UserRequest):
    result = search_similar_sentence(data.utterance)
    return {"result": result}
