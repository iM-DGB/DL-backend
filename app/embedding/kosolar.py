from app.config import SOLAR_API_KEY
from langchain_upstage import UpstageEmbeddings

def embed_texts(texts: list[str]) -> list[list[float]]:
    if not SOLAR_API_KEY:
        raise ValueError("SOLAR_API_KEY is not set.")
    embeddings = UpstageEmbeddings(api_key=SOLAR_API_KEY, model="solar-embedding-1-large-query")
    return embeddings.embed_documents(texts)
