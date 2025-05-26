import os
from dotenv import load_dotenv
from langchain_upstage import UpstageEmbeddings

load_dotenv()

api_key = os.getenv("SOLAR_API_KEY")

embedder = UpstageEmbeddings(model="solar-embedding-1-large", api_key=api_key)

# 테스트 문장
query = "해외여행자 보험의 보장 범위는 어떻게 되나요?"

# 임베딩 실행
embedding = embedder.embed_query(query)

# 결과 확인
print(f"✅ 임베딩 벡터 길이: {len(embedding)}")
print(f"🔢 임베딩 벡터 앞 5개 값: {embedding[:5]}")
