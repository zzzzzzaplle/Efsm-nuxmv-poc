from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from typing import Any

import requests

from .config import OLLAMA_HOST, OLLAMA_NUM_CTX, OLLAMA_TEMPERATURE, OLLAMA_TIMEOUT_SECONDS
from .schema import FSMOutput, fsm_json_schema


@dataclass
class GenerationResult:
    model: str
    system: str
    raw_text: str
    parsed: dict[str, Any] | None
    valid: bool
    error: str | None
    eval_count: int | None = None
    eval_duration_ns: int | None = None
    total_duration_ns: int | None = None


def list_installed_models(host: str = OLLAMA_HOST) -> set[str]:
    response = requests.get(f"{host}/api/tags", timeout=30)
    response.raise_for_status()
    payload = response.json()
    return {item["name"] for item in payload.get("models", [])}


def normalize_model_name(name: str) -> str:
    return name.split(":")[0] if ":" not in name else name


def is_model_installed(model: str, installed: set[str]) -> bool:
    if model in installed:
        return True
    if ":" not in model:
        return f"{model}:latest" in installed
    return False


def pull_model_command(model: str) -> str:
    return f"ollama pull {model}"


def extract_json_object(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")
    return text[start : end + 1]


def parse_fsm_response(raw_text: str) -> tuple[dict[str, Any] | None, bool, str | None]:
    try:
        json_text = extract_json_object(raw_text)
        payload = json.loads(json_text)
        validated = FSMOutput.model_validate(payload)
        return validated.model_dump(), True, None
    except Exception as exc:  # noqa: BLE001 - collect all parse/validation failures
        return None, False, str(exc)


def generate_fsm(
    model: str,
    messages: list[dict[str, str]],
    host: str = OLLAMA_HOST,
    use_structured_output: bool = True,
) -> GenerationResult:
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": OLLAMA_TEMPERATURE,
            "num_ctx": OLLAMA_NUM_CTX,
        },
    }
    if use_structured_output:
        body["format"] = fsm_json_schema()

    response = requests.post(
        f"{host}/api/chat",
        json=body,
        timeout=OLLAMA_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        return GenerationResult(
            model=model,
            system="",
            raw_text="",
            parsed=None,
            valid=False,
            error=str(payload["error"]),
        )
    raw_text = payload.get("message", {}).get("content", "")
    parsed, valid, error = parse_fsm_response(raw_text)

    return GenerationResult(
        model=model,
        system="",
        raw_text=raw_text,
        parsed=parsed,
        valid=valid,
        error=error,
        eval_count=payload.get("eval_count"),
        eval_duration_ns=payload.get("eval_duration"),
        total_duration_ns=payload.get("total_duration"),
    )


def generate_fsm_cli(
    model: str,
    messages: list[dict[str, str]],
    use_structured_output: bool = True,
) -> GenerationResult:
    """Fallback using the ollama CLI when the HTTP API is unavailable."""
    prompt_parts = [m["content"] for m in messages]
    prompt = "\n\n".join(prompt_parts)
    cmd = ["ollama", "run", model, prompt]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    raw_text = completed.stdout.strip()
    if completed.returncode != 0:
        return GenerationResult(
            model=model,
            system="",
            raw_text=raw_text or completed.stderr,
            parsed=None,
            valid=False,
            error=completed.stderr or f"ollama run exited with {completed.returncode}",
        )
    parsed, valid, error = parse_fsm_response(raw_text)
    return GenerationResult(
        model=model,
        system="",
        raw_text=raw_text,
        parsed=parsed,
        valid=valid,
        error=error,
    )
