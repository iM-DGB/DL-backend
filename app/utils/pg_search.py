from langchain_community.vectorstores.pgvector import PGVector
from langchain_upstage import UpstageEmbeddings
import os

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
    return db

def search_similar_chunks(query: str, top_k=3, filter: dict = None):
    db = get_vector_db()
    docs = db.similarity_search(query, k=top_k, filter=filter)
    return [doc.page_content for doc in docs]

def search_exact_product(category: str, product_name: str):
    db = get_vector_db()
    filter = {
        "category": category,
        "product_name": product_name
    }
    docs = db.similarity_search(query="해당 상품 설명", k=1, filter=filter)
    return [doc.page_content for doc in docs]
