import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Paths to the JSON files
CURRICULUM_PATH = BASE_DIR / "curriculum.json"
CANDIDATES_PATH = BASE_DIR / "candidates.json"

# Load curriculum once at startup
if CURRICULUM_PATH.exists():
    with open(CURRICULUM_PATH, "r", encoding="utf-8") as f:
        CURRICULUM_DATA = json.load(f)
else:
    CURRICULUM_DATA = {"modules": [], "days": []}

# Load candidates once at startup (useful for verification or references)
if CANDIDATES_PATH.exists():
    with open(CANDIDATES_PATH, "r", encoding="utf-8") as f:
        CANDIDATES_DATA = json.load(f)
else:
    CANDIDATES_DATA = {"candidates": []}

# API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # e.g., gemini, mock
