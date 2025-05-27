from fastapi import APIRouter
from app.models.schema import KakaoRequest
from app.llm.gemini import generate_answer
from app.utils.pg_search import search_similar_chunks, search_exact_product
from app.utils.prompt import build_prompt

router = APIRouter()

@router.post("/kakao/rag-webhook")
async def kakao_rag_webhook(data: KakaoRequest):
    category = data.action.params.category
    product_name = data.action.params.product_name
    user_msg = data.userRequest.utterance

    # 🔀 분기
    if product_name:
        chunks = search_exact_product(category, product_name)
    else:
        chunks = search_similar_chunks(user_msg, filter={"category": category})

    prompt = build_prompt(chunks, user_msg)
    answer = generate_answer(prompt)

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": answer}}
            ]
        }
    }

# @router.post("/kakao/rag-webhook")
# async def kakao_rag_webhook(data: KakaoRequest):
#     user_msg = data.userRequest.utterance

#     # 🔍 RAG 검색
#     context_chunks = search_similar_chunks(user_msg, top_k=3)

#     # 🧠 Prompt 조립
#     prompt = build_prompt(context_chunks, user_msg)

#     # ✨ Gemini 호출
#     gemini_answer = generate_answer(prompt)

#     # 📦 카카오 응답 형식
#     return {
#         "version": "2.0",
#         "template": {
#             "outputs": [
#                 {"simpleText": {"text": gemini_answer}}
#             ]
#         }
#     }

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
