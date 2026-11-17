import os
from dotenv import load_dotenv

# Read the .env file and load its lines into environment variables
load_dotenv()

# Read the key by name. Returns None if it doesn't exist.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Stop early with a clear message if the key is missing
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Add it to your .env file.")

# Model settings (we'll confirm the exact names in Part B)
CHAT_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODEL = "gemini-3.1-flash-lite"
TEMPERATURE = 0.2

# Embeddings and vector database
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 768

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma")