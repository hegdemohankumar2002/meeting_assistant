import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Processing limits for long meetings
MAX_AUDIO_DURATION_MINUTES = 120  # 2 hours max
CHUNK_SIZE_TOKENS = 1000  # Increased from 350 words
CHUNK_OVERLAP_TOKENS = 100  # Context preservation between chunks
USE_HIERARCHICAL_SUMMARIZATION_THRESHOLD = 5000  # Words threshold for hierarchical summarization

# Model selection
# Model selection
SUMMARIZATION_BACKEND = os.getenv("SUMMARIZATION_BACKEND", "ollama")  # "auto", "bart", "langchain", "ollama"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Fast and cost-effective
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama") # Ollama often doesn't need a key, but good to have
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1")

# Performance tuning
ENABLE_GPU = True
BATCH_SIZE_INTELLIGENCE = 10  # Process 10 sentences at once for intelligence extraction
MAX_WORKERS = 4  # For parallel processing
