import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


def build_model() -> ChatOpenAI:
    load_dotenv()
    config = {name: os.environ.get(name) for name in (
        "LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY"
    )}
    missing = [name for name, value in config.items() if not value or not value.strip()]
    if missing:
        raise RuntimeError(f"Missing LLM configuration: {', '.join(missing)}. Set these values in .env or the environment.")

    return ChatOpenAI(
        base_url=config["LLM_BASE_URL"],
        model=config["LLM_MODEL"],
        api_key=config["LLM_API_KEY"],
        max_retries=2,
        timeout=180,
    )
