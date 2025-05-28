import os
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from sklearn.metrics.pairwise import cosine_similarity
from app.utils.logger import logger
from app.llm.embedding import embed_query_locally
from langchain_upstage import UpstageEmbeddings


def get_pg_connection():
    return psycopg2.connect(
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        sslmode="require"
    )


def get_relevant_chunks_pgvector(query: str, category: str, top_k=5):
    logger.info("🧠 로컬 임베딩 생성 중...")
    query_vector = embed_query_locally(query)

    logger.info("📡 PostgreSQL 내 유사도 정렬 수행 중...")
    conn = get_pg_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT document, cmetadata->>'product_name' AS product_name,
               1 - (embedding <=> %s::vector) AS score
        FROM langchain_pg_embedding
        WHERE collection_id = (
            SELECT uuid FROM langchain_pg_collection WHERE name = 'insurance_docs'
        )
        AND cmetadata->>'category' = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (query_vector.tolist(), category, query_vector.tolist(), top_k))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        logger.warning("⚠️ 검색 결과 없음.")
        return {
            "recommended_product": None,
            "top_chunks": [],
            "related_products": []
        }

    seen_chunks = set()
    top_chunks, top_names = [], []

    for row in rows:
        content = row["document"].strip()
        if content not in seen_chunks:
            seen_chunks.add(content)
            top_chunks.append(content)
            top_names.append(row["product_name"])
            logger.info(f"🔹 추천: {row['product_name']} | 유사도: {row['score']:.4f}")

    recommended_product = max(set(top_names), key=top_names.count)
    related_products = list(dict.fromkeys(top_names))

    logger.info(f"🏆 최종 추천 상품: {recommended_product}")
    return {
        "recommended_product": recommended_product,
        "top_chunks": top_chunks,
        "related_products": related_products
    }


def get_relevant_chunks_fast(query: str, category: str, top_k=5):
    logger.info("🧠 쿼리 임베딩 생성 중...")
    embedder = UpstageEmbeddings(
        model="solar-embedding-1-large",
        api_key=os.getenv("SOLAR_API_KEY")
    )
    query_vector = embedder.embed_query(query)

    logger.info("📡 PostgreSQL에서 벡터 검색 중...")
    conn = get_pg_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT page_content, product_name, embedding
        FROM langchain_pg_embedding
        WHERE collection_id = (
            SELECT uuid FROM langchain_pg_collection WHERE name = 'insurance_docs'
        )
        AND metadata ->> 'category' = %s
    """, (category,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        logger.warning("⚠️ 검색 결과가 없습니다.")
        return {
            "recommended_product": None,
            "top_chunks": [],
            "related_products": []
        }

    logger.info(f"📄 총 후보 청크 수: {len(rows)}")

    contents, vectors, names = [], [], []
    for row in rows:
        embedding_str = row['embedding']
        vector = np.array(embedding_str[1:-1].split(','), dtype=np.float32)
        vectors.append(vector)
        contents.append(row['page_content'])
        names.append(row['product_name'])

    similarities = cosine_similarity([query_vector], vectors)[0]
    ranked = sorted(zip(contents, names, similarities), key=lambda x: x[2], reverse=True)
    top_docs = ranked[:top_k]

    seen_chunks = set()
    top_chunks, top_names = [], []

    for text, pname, score in top_docs:
        if text not in seen_chunks:
            seen_chunks.add(text)
            top_chunks.append(text)
            top_names.append(pname)
            logger.info(f"🔹 추천: {pname} | 유사도: {score:.4f}")

    recommended_product = max(set(top_names), key=top_names.count)
    related_products = list(dict.fromkeys(top_names))

    logger.info(f"🏆 최종 추천 상품: {recommended_product}")
    return {
        "recommended_product": recommended_product,
        "top_chunks": top_chunks,
        "related_products": related_products
    }
