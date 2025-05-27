from fastapi import APIRouter
from app.models.schema import KakaoRequest, RelevantChunksRequest
from app.llm.gemini import generate_answer
from app.llm.search import search_exact_product, get_relevant_chunks
from app.llm.prompt import build_prompt
import httpx
from fastapi import BackgroundTasks, Response, status

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
@router.post("/kakao/skill")
async def kakao_skill_endpoint(
    data: KakaoRequest,
    background_tasks: BackgroundTasks,
    response: Response
):
    # Pydantic 모델 속성 접근으로 수정
    user_msg = data.userRequest.utterance
    category = data.action.params.category or "기본카테고리"
    product_name = data.action.params.product_name

    # 5초 이상 걸릴 경우 콜백 처리 위해 202 응답 반환 (빈 JSON)
    response.status_code = status.HTTP_202_ACCEPTED

    # 백그라운드 작업 예약 (비동기 처리)
    background_tasks.add_task(process_and_callback, user_msg, category, product_name)

    return {}  # 202 Accepted 이므로 빈 바디 반환

async def process_and_callback(user_msg: str, category: str, product_name: str):
    # 1) 데이터 처리 (검색, LLM 호출 등)
    if product_name:
        chunks = search_exact_product(category, product_name)
    else:
        result = get_relevant_chunks(user_msg, category, top_k=5, product_top_k=10)
        chunks = result["top_chunks"]

    prompt = build_prompt(chunks, user_msg)
    answer = generate_answer(prompt)

    # 2) 콜백 URL 정의
    callback_url = "https://chatbot-service-526438895194.asia-northeast3.run.app/kakao/callback"

    # 3) 콜백용 응답 JSON (카카오 스킬 응답 포맷)
    payload = {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": answer}}
            ]
        }
    }

    # 4) HTTP POST 요청으로 카카오 콜백 URL에 결과 전송
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(callback_url, json=payload, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"콜백 전송 실패: {e}")

@router.post("/kakao/callback")
async def kakao_callback(data: dict):
    # 카카오가 콜백으로 보내는 JSON 수신
    print("카카오 콜백 데이터:", data)

    # 반드시 200 OK를 반환해야 카카오가 정상 처리함
    return {"result": "ok"}