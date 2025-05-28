from langchain_upstage import UpstageEmbeddings
import numpy as np
import os
from dotenv import load_dotenv

# 🔐 환경변수 로딩
load_dotenv()
api_key = os.getenv("SOLAR_API_KEY")

# 🔹 모델 로딩 (최초 1회)
solar_model = UpstageEmbeddings(
    model="solar-embedding-1-large",
    api_key=api_key
)

# 🔍 키워드 기반 태그 사전
SEARCH_HINTS = {
    # 🔹 공통 약관 키워드
    "부칙": "[부칙 관련 내용]",
    "청약철회": "[청약 철회 안내]",
    "계약해지": "[계약 해지 규정]",
    "면책": "[보장 제외 사항]",
    "예외": "[보장 제외 사항]",
    "보장": "[보장 항목]",
    "가입조건": "[가입 조건]",
    "가입나이": "[가입 가능 연령]",
    "납입": "[납입 조건]",
    "금리": "[금리 조건]",
    "이율": "[금리 조건]",
    
    # 🔹 예금
    "정기예금": "[예금 상품]",
    "예치금": "[예금 상품]",
    "이자지급": "[예금 상품 이자 지급 방식]",
    
    # 🔹 적금
    "정기적금": "[적금 상품]",
    "자동이체": "[적금 자동이체]",
    "만기": "[만기 조건]",
    
    # 🔹 통장
    "입출금": "[입출금 통장]",
    "자유입출금": "[입출금 통장]",
    "수수료": "[통장 수수료 혜택]",
    "비대면개설": "[통장 개설 방식]",
    
    # 🔹 대출
    "신용대출": "[신용대출 상품]",
    "담보대출": "[담보대출 상품]",
    "금리": "[대출 금리]",
    "상환": "[대출 상환 방식]",
    "한도": "[대출 한도]",
    "대출조건": "[대출 조건]",
}

def embed_query_locally(text: str) -> np.ndarray:
    # 🔎 사전 태그 삽입
    for keyword, tag in SEARCH_HINTS.items():
        if keyword in text:
            text = f"{tag} {text}"
            break

    # 🔄 임베딩 수행
    vector = solar_model.embed_query(text)
    return np.array(vector)
