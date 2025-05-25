import os
from dotenv import load_dotenv
from langchain_upstage import UpstageEmbeddings

load_dotenv()

def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    주어진 텍스트 리스트를 KoSOLAR 임베딩 벡터로 변환합니다.
    
    Args:
        texts (list[str]): 임베딩할 문장 리스트

    Returns:
        list[list[float]]: 각 문장에 대한 임베딩 벡터 리스트
    """
    api_key = os.getenv("SOLAR_API_KEY")
    if not api_key:
        raise ValueError("환경변수 'SOLAR_API_KEY'가 설정되어 있지 않습니다.")
    
    model_name = "solar-embedding-1-large-query"

    embeddings = UpstageEmbeddings(
        api_key=api_key,
        model=model_name
    )

    return embeddings.embed_documents(texts)

# 테스트 실행용
if __name__ == "__main__":
    sample_texts = [
        "안녕하세요. 이것은 테스트 문장입니다.",
        "이 문장은 임베딩 벡터로 변환됩니다."
    ]
    vectors = embed_texts(sample_texts)

    for i, vec in enumerate(vectors):
        print(f"[문장 {i+1}] 벡터 길이: {len(vec)}")
        print(vec[:5], "...\n")

# # 1. API 키 및 모델 설정
# api_key = SOLAR_API_KEY  # 👉 본인의 API 키로 교체
# model_name = "solar-embedding-1-large-query"

# # UpstageEmbeddings 객체 생성
# embeddings = UpstageEmbeddings(
#     api_key=api_key,
#     model=model_name
# )

# # 임베딩할 텍스트 예시
# texts = [
#     "안녕하세요. 이것은 테스트 문장입니다.",
#     "이 문장은 임베딩 벡터로 변환됩니다."
# ]

# # 임베딩 생성
# embedding_vectors = embeddings.embed_documents(texts)

# # 결과 출력
# for i, vec in enumerate(embedding_vectors):
#     print(f"문장 {i+1} 임베딩 벡터 크기: {len(vec)}")
#     print(vec[:5], "...")  # 벡터 앞부분 일부만 출력
