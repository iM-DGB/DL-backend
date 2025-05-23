from langchain_upstage import UpstageEmbeddings
import re

# 1. API 키 및 모델 설정
api_key = SOLAR_API_KEY  # 👉 본인의 API 키로 교체
model_name = "solar-embedding-1-large-query"

# UpstageEmbeddings 객체 생성
embeddings = UpstageEmbeddings(
    api_key=api_key,
    model=model_name
)

# 임베딩할 텍스트 예시
texts = [
    "안녕하세요. 이것은 테스트 문장입니다.",
    "이 문장은 임베딩 벡터로 변환됩니다."
]

# 임베딩 생성
embedding_vectors = embeddings.embed_documents(texts)

# 결과 출력
for i, vec in enumerate(embedding_vectors):
    print(f"문장 {i+1} 임베딩 벡터 크기: {len(vec)}")
    print(vec[:5], "...")  # 벡터 앞부분 일부만 출력
