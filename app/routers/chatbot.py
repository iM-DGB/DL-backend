from fastapi import APIRouter, Request, BackgroundTasks, Response, status
from fastapi.responses import JSONResponse
from app.models.schema import KakaoRequest
from app.llm.gemini import generate_answer
from app.llm.search import get_relevant_chunks
from app.llm.prompt import build_prompt
import httpx
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

@router.post("/kakao/recommended-products")
async def get_recommended_products_with_callback(
    data: KakaoRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    response: Response
):
    callback_url = "https://chatbot-service-526438895194.asia-northeast3.run.app/kakao/callback"
    query = data.action.params.utterance or data.userRequest.utterance or ""
    category = data.action.params.category

    if not query.strip():
        response.status_code = 400
        logger.warning("❌ 사용자 질문(utterance)이 비어있습니다.")
        return {"error": "질문이 전달되지 않았습니다."}

    logger.info(f"📨 고객님의 질문을 접수했어요! 🔍 질문: '{query}', 카테고리: '{category}'")

    if not callback_url:
        response.status_code = 400
        logger.warning("⚠️ 콜백 URL이 누락되었습니다. 서버 설정을 확인해주세요.")
        return {"error": "Missing callbackUrl from Kakao"}

    background_tasks.add_task(
        process_and_callback,
        user_msg=query,
        category=category,
        callback_url=callback_url
    )

    response.status_code = status.HTTP_202_ACCEPTED
    return {
        "version": "2.0",
        "useCallback": True,
        "data": {
            "text": "⏳ 추천 상품을 분석 중입니다. 잠시만 기다려주세요 😊"
        }
    }


@router.post("/kakao/recommended-products-direct")
async def get_recommended_products_direct(data: KakaoRequest):
    query = data.action.params.utterance or data.userRequest.utterance or ""
    category = data.action.params.category

    if not query.strip():
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {"simpleText": {"text": "❌ 질문이 입력되지 않았습니다."}}
                ]
            }
        }

    result = get_relevant_chunks(query=query, category=category, top_k=5, product_top_k=10)
    chunks = result["top_chunks"]

    prompt = build_prompt(chunks, query)
    answer = generate_answer(prompt)

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": answer[:1000]
                    }
                }
            ]
        }
    }


@router.post("/kakao/callback")
async def kakao_callback(request: Request):
    data = await request.json()
    logger.info("✅ 챗봇에서 추천 답변을 잘 전달받았습니다!")

    text = data.get("template", {}).get("outputs", [])[0].get("simpleText", {}).get("text", "죄송합니다. 답변을 받아오지 못했습니다.")

    return JSONResponse(content={
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": text[:1000]
                    }
                }
            ]
        }
    })


async def process_and_callback(user_msg: str, category: str, callback_url: str):
    try:
        logger.info("🔍 유사 상품 검색 중...")
        result = get_relevant_chunks(user_msg, category, top_k=5, product_top_k=10)
        chunks = result["top_chunks"]
        logger.info(f"🔎 검색된 청크 개수: {len(chunks)}")

        logger.info("✍️ 프롬프트 생성 중...")
        prompt = build_prompt(chunks, user_msg)
        logger.info(f"🧾 생성된 프롬프트 일부: {prompt[:100]}...")

        logger.info("🧠 Gemini 응답 생성 중...")
        answer = generate_answer(prompt)
        logger.info(f"📨 생성된 응답 일부: {answer[:100]}...")

        payload = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {"simpleText": {"text": answer[:1000]}}
                ]
            }
        }

        logger.info("📬 콜백 URL로 전송 중...")
        async with httpx.AsyncClient() as client:
            resp = await client.post(callback_url, json=payload, timeout=10)

        if resp.status_code != 200:
            logger.warning(f"⚠️ 콜백 실패 - 상태코드: {resp.status_code}, 응답: {resp.text}")
        else:
            logger.info(f"📤 고객님께 추천 결과를 전달했어요! ✅ 응답 코드: {resp.status_code}")

    except Exception as e:
        logger.error(f"🚨 추천 결과 전달 중 문제가 발생했어요. 내용: {e}")
