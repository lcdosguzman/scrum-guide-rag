from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_DIR = PROJECT_ROOT / "chroma_db"

CHAT_MODEL = "llama3.2"
EMBEDDING_MODEL = "nomic-embed-text"

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
RETRIEVAL_K = 6
