import os
from dotenv import load_dotenv
from langchain_upstage import UpstageEmbeddings
from langchain_community.vectorstores.pgvector import PGVector

# ✅ .env 파일 강제 로드
load_dotenv(dotenv_path=".env", override=True)

# ✅ 환경변수 불러오기
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")

# ✅ 연결 문자열 (transaction pooler + SSL)
CONNECTION_STRING = (
    f"postgresql+psycopg://{PG_USER}:{PG_PASSWORD}"
    f"@{PG_HOST}:{PG_PORT}/{PG_DB}?sslmode=require"
)
print(f"📡 연결 확인 → {CONNECTION_STRING}")

# ✅ SOLAR 임베딩 설정
embedder = UpstageEmbeddings(
    model="solar-embedding-1-large",
    api_key=os.getenv("SOLAR_API_KEY")
)

# ✅ 입력 텍스트 및 메타데이터
texts = [
    "해외여행자 보험은 질병 및 상해 치료비를 보장합니다.",
    "휴대품 손해는 항목당 최대 20만원까지 보장됩니다."
]

metadatas = [
    {
        "category": "여행자보험",
        "product_name": "글로벌케어",
        "type": "실손",
        "clause": "3조 1항"
    },
    {
        "category": "여행자보험",
        "product_name": "글로벌케어",
        "type": "실손",
        "clause": "3조 2항"
    }
]

# ✅ 벡터 저장
try:
    vectorstore = PGVector.from_texts(
        texts=texts,
        embedding=embedder,
        metadatas=metadatas,
        collection_name="insurance_docs",            # 컬렉션 이름 (UUID 자동 생성)
        connection_string=CONNECTION_STRING,
    )
    print("✅ Supabase(pgvector)에 벡터 저장 완료!")

except Exception as e:
    print("❌ 오류 발생:", e)
