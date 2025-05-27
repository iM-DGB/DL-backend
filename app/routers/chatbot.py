from fastapi import APIRouter
from app.models.schema import KakaoRequest, RelevantChunksRequest
from app.llm.gemini import generate_answer
from app.llm.search import search_exact_product, get_relevant_chunks
from app.llm.prompt import build_prompt

router = APIRouter()

@router.post("/kakao/rag-webhook")
async def kakao_rag_webhook(data: KakaoRequest):
    category = data.action.params.category
    product_name = data.action.params.product_name
    user_msg = data.userRequest.utterance

    # 🔍 RAG 검색
    if product_name:
        chunks = search_exact_product(category, product_name)
    else:
        result = get_relevant_chunks(
            query=user_msg,
            category=category,
            top_k=5,
            product_top_k=10
        )
        chunks = result["top_chunks"]

    # 🧠 Prompt 조립
    prompt = build_prompt(chunks, user_msg)

     # ✨ Gemini 호출
    answer = generate_answer(prompt)

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": answer}}
            ]
        }
    }

# @router.post("/kakao/get-relevant-chunks")
# async def get_relevant_chunks_api(data: RelevantChunksRequest):
#     result = get_relevant_chunks(
#         query=data.query,
#         category=data.category,
#         top_k=data.top_k,
#         product_top_k=data.product_top_k
#     )
#     return result



from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.llm.search import get_relevant_chunks

router = APIRouter()

# 카카오 챗봇 요청 스키마
class UserRequest(BaseModel):
    utterance: str

class ActionParams(BaseModel):
    category: Optional[str]
    product_name: Optional[str] = None

class Action(BaseModel):
    params: ActionParams

class KakaoRequest(BaseModel):
    action: Action
    userRequest: UserRequest

@router.post("/kakao/get-relevant-chunks")
async def get_relevant_chunks_api(data: KakaoRequest):
    query = data.userRequest.utterance
    category = data.action.params.category or "기본카테고리"

    result = get_relevant_chunks(
        query=query,
        category=category,
        top_k=5,
        product_top_k=10
    )

    recommended = result.get("recommended_product") or "추천 상품이 없습니다."
    chunks_preview = "\n\n".join(result.get("top_chunks", [])[:3]) or "관련 정보가 없습니다."

    answer = f"추천 상품: {recommended}\n\n{chunks_preview}"

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": answer
                    }
                }
            ]
        }
    }

class SimpleRequest(BaseModel):
    category: Optional[str] = None
    product_name: Optional[str] = None
    message: Optional[str] = None

@router.post("/test/simple-response")
async def simple_response(data: SimpleRequest):
    cat = data.category or "카테고리 없음"
    pname = data.product_name or "상품명 없음"
    msg = data.message or "메시지 없음"

    text = f"카테고리: {cat}\n상품명: {pname}\n메시지: {msg}"

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": text
                    }
                }
            ]
        }
    }