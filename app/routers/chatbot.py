from fastapi import APIRouter, Request, BackgroundTasks, Response
from fastapi.responses import JSONResponse
from app.models.schema import KakaoRequest
from app.llm.gemini import generate_answer
from app.llm.search import get_relevant_chunks_pgvector as get_relevant_chunks
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
    # ✅ 콜백 URL을 동적으로 요청 body에서 추출
    body = await request.json()
    callback_url = body.get("userRequest", {}).get("callbackUrl")
    query = data.action.params.utterance or data.userRequest.utterance or ""
    category = data.action.params.category

    if not callback_url:
        logger.error("❌ callbackUrl이 누락되어 콜백 설정 불가")
        return JSONResponse(status_code=400, content={"error": "Missing callbackUrl"})

    if not query.strip():
        logger.warning("❌ 질문이 비어 있습니다.")
        return JSONResponse(
            status_code=200,
            content={
                "version": "2.0",
                "template": {
                    "outputs": [{"simpleText": {"text": "❌ 질문이 입력되지 않았습니다."}}]
                }
            }
        )

    logger.info(f"📨 질문 접수: '{query}' / 카테고리: '{category}'")

    background_tasks.add_task(
        process_and_callback,
        user_msg=query,
        category=category,
        callback_url=callback_url
    )

    logger.info("⏳ 비동기 처리 시작, useCallback 응답 반환")

    return JSONResponse(
        status_code=200,
        content={
            "version": "2.0",
            "useCallback": True,
            "data": {
                "text": "⏳ 추천 상품을 분석 중입니다. 잠시만 기다려주세요 😊"
            }
        }
    )


@router.post("/kakao/recommended-products-direct")
async def get_recommended_products_direct(data: KakaoRequest):
    query = data.action.params.utterance or data.userRequest.utterance or ""
    category = data.action.params.category

    if not query.strip():
        return {
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": "❌ 질문이 입력되지 않았습니다."}}]
            }
        }

    result = get_relevant_chunks(query=query, category=category, top_k=5)
    chunks = result["top_chunks"]

    prompt = build_prompt(chunks, query)
    answer = generate_answer(prompt)

    return {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": answer[:1000]}}]
        }
    }


@router.post("/kakao/callback")
async def kakao_callback(request: Request):
    data = await request.json()
    logger.info("✅ 콜백 수신 완료")

    try:
        text = data.get("template", {}).get("outputs", [])[0].get("simpleText", {}).get("text", "")
    except Exception as e:
        logger.error(f"❌ 콜백 응답 파싱 실패: {e}")
        text = "추천 결과를 받아오지 못했습니다."

    return JSONResponse(content={
        "version": "2.0",
        "data": {
            "answer": text.strip()[:1000]
        }
    })


async def process_and_callback(user_msg: str, category: str, callback_url: str):
    try:
        logger.info("🔍 유사 상품 검색 중...")
        result = get_relevant_chunks(user_msg, category, top_k=5)
        chunks = result["top_chunks"]
        logger.info(f"🔎 검색된 청크 수: {len(chunks)}")

        logger.info("✍️ 프롬프트 작성 중...")
        prompt = build_prompt(chunks, user_msg)
        logger.info(f"🧾 프롬프트 예시: {prompt[:100]}...")

        logger.info("🧠 Gemini 응답 생성 중...")
        answer = generate_answer(prompt)
        logger.info(f"📨 생성된 답변: {answer[:100]}...")

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
            logger.warning(f"⚠️ 콜백 실패: {resp.status_code}, 응답: {resp.text}")
        else:
            logger.info(f"📤 추천 결과 전송 완료 ✅ 코드: {resp.status_code}")

    except Exception as e:
        logger.error(f"🚨 추천 처리 중 예외 발생: {e}")
