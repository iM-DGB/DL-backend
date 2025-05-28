import os
from langchain_community.vectorstores.pgvector import PGVector
from langchain_upstage import UpstageEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
from app.utils.logger import logger

def get_vector_db():
    embedder = UpstageEmbeddings(
        model="solar-embedding-1-large",
        api_key=os.getenv("SOLAR_API_KEY")
    )

    connection_string = (
        f"postgresql+psycopg://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
        f"@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_DB')}?sslmode=require"
    )

    db = PGVector(
        collection_name="insurance_docs",
        connection_string=connection_string,
        embedding_function=embedder,
    )
    return db, embedder


def search_exact_product(category: str, product_name: str):
    db, _ = get_vector_db()
    filter = {
        "category": category,
        "product_name": product_name
    }
    docs = db.similarity_search(query="해당 상품 설명", k=1, filter=filter)
    return [doc.page_content for doc in docs]


def search_similar_product(query: str, category: str, top_k=5, fetch_k=30):
    db, _ = get_vector_db()
    filter = {"category": category}
    docs = db.similarity_search(query, k=fetch_k, filter=filter)

    product_scores = {}
    seen = set()

    for doc in docs:
        pname = doc.metadata.get("product_name")
        if pname and pname not in seen:
            seen.add(pname)
            product_scores[pname] = doc.metadata.get("score", 1.0)
        if len(product_scores) >= top_k:
            break   

    product_names = list(product_scores.keys())            
    logger.info(f"🎯 유사 상품 후보: {product_names}")

    return product_names


def get_relevant_chunks(query: str, category: str, top_k=5, product_top_k=10):
    db, embedder = get_vector_db()

    # Step 1: 유사 상품 후보 추출
    product_names = search_similar_product(query, category, top_k=product_top_k)
    if not product_names:
        return {
            "recommended_product": None,
            "top_chunks": [],
            "related_products": []
        }

    # Step 2: 각 상품의 청크 수집 (query 기반 검색)
    all_docs = []
    seen_chunks = set()

    for pname in product_names:
        docs = db.similarity_search(
            query=query,
            k=10,
            filter={"category": category, "product_name": pname}
        )
        for doc in docs:
            chunk = doc.page_content.strip()
            if chunk not in seen_chunks:
                seen_chunks.add(chunk)
                all_docs.append(doc)

    if not all_docs:
        return {
            "top_chunks": [],
            "recommended_product": None,
            "related_products": []
        }

    # Step 3: 의미 기반 임베딩 및 유사도 정렬
    query_vector = embedder.embed_query(query)
    doc_texts = [doc.page_content for doc in all_docs]
    doc_vectors = embedder.embed_documents(doc_texts)
    similarities = cosine_similarity([query_vector], doc_vectors)[0]

    ranked = sorted(zip(all_docs, similarities), key=lambda x: x[1], reverse=True)

    # Step 4: 상위 청크 및 추천 상품명 결정
    top_docs = ranked[:top_k]
    top_chunks = []
    top_product_names = []
    chunk_seen = set()

    for doc, _ in top_docs:
        content = doc.page_content.strip()
        if content not in chunk_seen:
            chunk_seen.add(content)
            top_chunks.append(content)
            top_product_names.append(doc.metadata.get("product_name"))

    recommended_product = max(set(top_product_names), key=top_product_names.count)
    related_products = list(dict.fromkeys(top_product_names))

    return {
        "recommended_product": recommended_product,
        "top_chunks": top_chunks,
        "related_products": related_products
    }