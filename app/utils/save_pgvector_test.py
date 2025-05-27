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
print(f"📡 연결 확인 → {CONNECTION_STRING}")

# ✅ 임베딩 모델 설정
embedder = UpstageEmbeddings(
    model="solar-embedding-1-large",
    api_key=SOLAR_API_KEY
)

# ✅ 단일 텍스트 파일 경로
file_path = "app/utils/data/예금/복리회전예금.txt"

# ✅ 메타 정보 추출
category = os.path.basename(os.path.dirname(file_path))           # 상위 폴더명
product_name = os.path.splitext(os.path.basename(file_path))[0]   # 파일명 (확장자 제외)

# ✅ 텍스트 불러오기
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# ✅ 문단 단위 분리 (빈 줄 기준)
paragraphs = re.split(r"\n\s*\n", content.strip())

# ✅ "부칙"이 포함된 문단 인덱스 찾기
split_idx = None
for i, para in enumerate(paragraphs):
    if "부 칙" in para:
        split_idx = i
        break

# ✅ 문단 분할 (기준 문단은 '약관'에 포함, 이후는 '상품설명')
texts, metadatas = [], []
print("\n📄 임베딩할 문단 및 메타데이터\n" + "-" * 40)

for idx, para in enumerate(paragraphs):
    para = para.strip()
    if not para:
        continue

    # type 결정
    if split_idx is not None and idx > split_idx:
        section_type = "상품설명"
    else:
        section_type = "약관"

    # ✅ 임베딩 텍스트 및 메타데이터 저장
    texts.append(para)
    metadata = {
        "category": category,
        "product_name": product_name,
        "type": section_type
    }
    metadatas.append(metadata)

    # ✅ 출력
    print(f"\n🧩 문단 {idx + 1}")
    print("내용:", (para[:200] + "..." if len(para) > 200 else para))
    print("메타데이터:", metadata)

# ✅ 벡터 저장
try:
    vectorstore = PGVector.from_texts(
        texts=texts,
        embedding=embedder,
        metadatas=metadatas,
        collection_name="insurance_docs",
        connection_string=CONNECTION_STRING,
    )
    print("\n✅ 문단 단위 벡터 저장 완료!")

except Exception as e:
    print("❌ 오류 발생:", e)
