from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_DIR = PROJECT_ROOT / "dataset"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
RAW_DIR = OUTPUTS_DIR / "raw"
CLEANED_DIR = OUTPUTS_DIR / "cleaned"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"

MODELS: list[str] = [
    "qwen2.5-coder:7b",
    "qwen2.5-coder:14b",
    "llama3.1:8b",
    "mistral-nemo:12b",
    "gemma2:9b",
    "phi3:14b",
]

OPTIONAL_MODELS: list[str] = [
    "qwen2.5-coder:32b",
]

OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_TIMEOUT_SECONDS = 600
OLLAMA_TEMPERATURE = 0.0
OLLAMA_NUM_CTX = 8192

REQUIREMENT_ID_PATTERN = r"R\d+"
