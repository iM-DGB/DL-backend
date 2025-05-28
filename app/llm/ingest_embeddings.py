import os
import re
from dotenv import load_dotenv
from langchain_upstage import UpstageEmbeddings
from langchain_community.vectorstores.pgvector import PGVector

# ✅ .env 로드
load_dotenv(dotenv_path=".env", override=True)

# ✅ 환경변수 불러오기
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")
SOLAR_API_KEY = os.getenv("SOLAR_API_KEY")

# ✅ 연결 문자열
CONNECTION_STRING = (
    f"postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}?sslmode=require"
)
print(f"\U0001F4E1 연결 확인 → {CONNECTION_STRING}")

# ✅ Solar API 기반 임베딩 모델 설정
embedder = UpstageEmbeddings(
    model="solar-embedding-1-large",
    api_key=SOLAR_API_KEY
)

# ✅ 루트 폴더
BASE_DIR = "app/utils/data"
texts, metadatas = [], []

# ✅ 모든 하위 폴더 및 파일 순회
for category in os.listdir(BASE_DIR):
    category_path = os.path.join(BASE_DIR, category)
    if not os.path.isdir(category_path):
        continue

    for filename in os.listdir(category_path):
        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(category_path, filename)
        product_name = os.path.splitext(filename)[0]

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"❌ 파일 열기 실패: {file_path} → {e}")
            continue

        # ✅ 문단 분리
        paragraphs = re.split(r"\n\s*\n", content.strip())

        # ✅ 부칙 기준 인덱스 찾기
        split_idx = None
        for i, para in enumerate(paragraphs):
            if "부 칙" in para or "부칙" in para:
                split_idx = i
                break

        # ✅ 각 문단 처리
        for idx, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue

            section_type = "상품설명" if split_idx is not None and idx > split_idx else "약관"

            texts.append(para)
            metadatas.append({
                "category": category,
                "product_name": product_name,
                "type": section_type
            })

print(f"\n📦 총 문단 수: {len(texts)}")

# ✅ 벡터 저장
try:
    vectorstore = PGVector.from_texts(
        texts=texts,
        embedding=embedder,
        metadatas=metadatas,
        collection_name="insurance_docs",
        connection_string=CONNECTION_STRING,
    )
    print("\n✅ 모든 텍스트 문단 벡터 저장 완료!")

except Exception as e:
    print("❌ 벡터 저장 중 오류 발생:", e)