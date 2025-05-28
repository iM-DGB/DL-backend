# app/llm/embedding.py

from sentence_transformers import SentenceTransformer
import numpy as np

# 🔹 모델 로딩 (최초 1회)
solar_model = SentenceTransformer("upstage/solar-embedding-1-large")

# 🔍 키워드 기반 태그 사전
SEARCH_HINTS = {
    "부칙": "[부칙 관련 내용]",
    "청약철회": "[청약철회 규정]",
    "면책사항": "[면책사항 안내]",
    # ... 생략 ...
}

def embed_query_locally(text: str) -> np.ndarray:
    for keyword, tag in SEARCH_HINTS.items():
        if keyword in text:
            text = f"{tag} {text}"
            break
    return solar_model.encode(text, normalize_embeddings=True)
