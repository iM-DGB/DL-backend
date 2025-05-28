import os
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from app.utils.logger import logger
from app.llm.embedding import embed_query_locally

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

    # 🔍 필터링 조건 추가 (카테고리 필터)
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

    # 🔢 유사도 계산
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

# def get_vector_db():
#     embedder = UpstageEmbeddings(
#         model="solar-embedding-1-large",
#         api_key=os.getenv("SOLAR_API_KEY")
#     )
#     connection_string = (
#         f"postgresql+psycopg://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
#         f"@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_DB')}?sslmode=require"
#     )
#     db = PGVector(
#         collection_name="insurance_docs",
#         connection_string=connection_string,
#         embedding_function=embedder,
#     )
#     return db, embedder



# def search_exact_product(category: str, product_name: str):
#     db, _ = get_vector_db()
#     filter = {"category": category, "product_name": product_name}
#     docs = db.similarity_search(query="해당 상품 설명", k=1, filter=filter)
#     return [doc.page_content for doc in docs]


# def search_similar_product(query: str, category: str, top_k=5, fetch_k=30):
#     db, _ = get_vector_db()
#     filter = {"category": category}
#     docs = db.similarity_search(query, k=fetch_k, filter=filter)

#     seen = set()
#     product_names = []
#     for doc in docs:
#         pname = doc.metadata.get("product_name")
#         if pname and pname not in seen:
#             seen.add(pname)
#             product_names.append(pname)
#         if len(product_names) >= top_k:
#             break

#     logger.info(f"🎯 유사 상품 후보: {product_names}")
#     return product_names



# def get_relevant_chunks(query: str, category: str, top_k=5, product_top_k=10):
#     db, embedder = get_vector_db()

#     product_names = search_similar_product(query, category, top_k=product_top_k)
#     if not product_names:
#         return {
#             "recommended_product": None,
#             "top_chunks": [],
#             "related_products": [],
#             "similarity_avg": 0.0
#         }

#     all_docs = []
#     seen_chunks = set()

#     for pname in product_names:
#         docs = db.similarity_search(query, k=10, filter={"category": category, "product_name": pname})
#         for doc in docs:
#             chunk = doc.page_content.strip()
#             if chunk not in seen_chunks:
#                 seen_chunks.add(chunk)
#                 all_docs.append(doc)

#     if not all_docs:
#         return {
#             "recommended_product": None,
#             "top_chunks": [],
#             "related_products": [],
#             "similarity_avg": 0.0
#         }

#     query_vector = embedder.embed_query(query)
#     doc_texts = [doc.page_content for doc in all_docs]
#     doc_vectors = embedder.embed_documents(doc_texts)
#     similarities = cosine_similarity([query_vector], doc_vectors)[0]

#     ranked = sorted(zip(all_docs, similarities), key=lambda x: x[1], reverse=True)
#     top_docs = ranked[:top_k]

#     top_chunks = []
#     top_product_names = []
#     top_similarities = []
#     chunk_seen = set()

#     for i, (doc, score) in enumerate(top_docs):
#         pname = doc.metadata.get("product_name", "알 수 없음")
#         logger.info(f"🔹 Top{i+1} | 상품명: {pname}, 유사도: {score:.4f}")

#         content = doc.page_content.strip()
#         if content not in chunk_seen:
#             chunk_seen.add(content)
#             top_chunks.append(content)
#             top_product_names.append(pname)
#             top_similarities.append(score)

#     recommended_product = max(set(top_product_names), key=top_product_names.count)
#     related_products = list(dict.fromkeys(top_product_names))
#     similarity_avg = sum(top_similarities) / len(top_similarities) if top_similarities else 0.0

#     logger.info(f"🏆 최종 추천 상품: {recommended_product}")
#     logger.info(f"📦 관련 상품 후보: {related_products}")
#     logger.info(f"📈 평균 유사도 점수: {similarity_avg:.4f}")

#     return {
#         "recommended_product": recommended_product,
#         "top_chunks": top_chunks,
#         "related_products": related_products,
#         "similarity_avg": round(similarity_avg, 4)
#     }
