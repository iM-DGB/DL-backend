import numpy as np
from app.embedding.kosolar import embed_texts
from sklearn.metrics.pairwise import cosine_similarity

# 샘플 문장
SAMPLE_TEXTS = [
    "반려동물 보험에 대해 알고 싶어요.",
    "자동차 사고 처리 절차가 궁금합니다.",
    "해외여행자 보험의 보장 범위는 어떻게 되나요?",
    "청약 철회가 가능한가요?",
    "적금 상품의 이자율은 얼마나 되나요?"
]

# 벡터 저장소
vector_store = []

def build_sample_vector_store():
    vectors = embed_texts(SAMPLE_TEXTS)
    for i in range(len(SAMPLE_TEXTS)):
        vector_store.append({
            "text": SAMPLE_TEXTS[i],
            "vector": vectors[i]
        })

def search_similar_sentence(query: str, top_k: int = 1):
    if not vector_store:
        raise ValueError("Vector store is empty. Run build_sample_vector_store() first.")
    
    query_vec = embed_texts([query])[0]
    
    vectors = np.array([v["vector"] for v in vector_store])
    similarities = cosine_similarity([query_vec], vectors)[0]

    ranked = sorted(zip(similarities, vector_store), key=lambda x: -x[0])
    return [{
        "text": r[1]["text"],
        "similarity": round(r[0], 4)
    } for r in ranked[:top_k]]
