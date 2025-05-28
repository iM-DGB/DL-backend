from fastapi import APIRouter, Request, BackgroundTasks, Response, status
from app.models.schema import KakaoRequest
from app.llm.gemini import generate_answer
from app.llm.search import search_exact_product, get_relevant_chunks
from app.llm.prompt import build_prompt
import httpx

router = APIRouter()

# @router.post("/kakao/category-product")
# async def search_exact_product_api(data: KakaoRequest):
#     category = data.action.params.category
#     product_name = data.action.params.product_name
#     user_msg = data.userRequest.utterance

#     if not product_name:
#         result = get_relevant_chunks(
#             query=user_msg,
#             category=category,
#             top_k=1,
#             product_top_k=1
#         )
#         chunks = result.get("top_chunks", [])
#     else:
#         chunks = search_exact_product(category, product_name)

#     prompt = build_prompt(chunks, user_msg)
#     answer = generate_answer(prompt)

#     return {
#         "version": "2.0",
#         "template": {
#             "outputs": [
#                 {"simpleText": {"text": answer}}
#             ]
#         }
#     }

@router.post("/kakao/recommended-products")
async def get_recommended_products_with_callback(
    data: KakaoRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    response: Response
):
    body = await request.json()
    callback_url = body.get("callbackUrl")

    if not callback_url:
        response.status_code = 400
        return {"error": "Missing callbackUrl from Kakao"}

    query = data.userRequest.utterance
    category = data.action.params.category

    # 백그라운드로 처리 시작
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

# @router.post("/kakao/recommended-products")
# async def get_relevant_chunks_api(data: KakaoRequest):
#     query = data.userRequest.utterance
#     category = data.action.params.category

#     result = get_relevant_chunks(
#         query=query,
#         category=category,
#         top_k=5,
#         product_top_k=10
#     )

#     prompt = build_prompt(result.get("top_chunks", []), query)
#     answer = generate_answer(prompt)

#     return {
#         "version": "2.0",
#         "template": {
#             "outputs": [
#                 {
#                     "simpleText": {
#                         "text": answer
#                     }
#                 }
#             ]
#         }
#     }

@router.post("/kakao/skill")
async def kakao_skill_endpoint(
    data: KakaoRequest,
    background_tasks: BackgroundTasks,
    response: Response,
    request: Request
):

    body = await request.json()
    callback_url = body.get("callbackUrl")

    if not callback_url:
        response.status_code = 400
        return {"error": "Missing callbackUrl from Kakao"}

    user_msg = data.userRequest.utterance
    category = data.action.params.category

    background_tasks.add_task(
        process_and_callback,
        user_msg,
        category,
        callback_url
    )

    response.status_code = status.HTTP_202_ACCEPTED
    return {
        "version": "2.0",
        "useCallback": True,
        "data": {
            "text": "⏳ 답변을 생성하는 중이에요. 잠시만 기다려주세요 😊"
        }
    }

async def process_and_callback(user_msg: str, category: str, callback_url: str):
    # 🔍 데이터 검색
    result = get_relevant_chunks(user_msg, category, top_k=5, product_top_k=10)
    chunks = result["top_chunks"]

    # 🧠 프롬프트 구성 & 응답 생성
    prompt = build_prompt(chunks, user_msg)
    answer = generate_answer(prompt)

    # 📦 콜백 응답 포맷
    payload = {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": answer}}
            ]
        }
    }

    # 🔁 콜백 전송
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(callback_url, json=payload, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"❌ 콜백 전송 실패: {e}")

@router.post("/kakao/callback")
async def kakao_callback(data: dict):
    print("카카오 콜백 데이터:", data)
    return {"result": "ok"}