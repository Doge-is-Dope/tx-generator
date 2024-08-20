from functools import lru_cache

from langchain_core.pydantic_v1 import BaseModel
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import ChatVertexAI


def _get_provider() -> str:
    import os
    from dotenv import load_dotenv

    load_dotenv()
    return os.getenv("MODEL_PROVIDER", "openai")


@lru_cache(maxsize=4)
def get_embedding() -> Embeddings:
    normalized_provider = _get_provider().strip().lower()
    embeddings = {
        "openai": OpenAIEmbeddings(
            # text-embedding-3-large
            # text-embedding-3-small
            model="text-embedding-3-large",
        )
    }
    try:
        return embeddings[normalized_provider]
    except KeyError:
        raise ValueError(f"Provider must be one of: {', '.join(embeddings.keys())}")


class ChatModelProvider(BaseModel):
    model: BaseChatModel
    name: str


@lru_cache(maxsize=4)
def get_chat_model(
    provider: str | None = None,
    temperature: float = 0,
) -> ChatModelProvider:
    normalized_provider = provider or _get_provider().strip().lower()

    # gpt-4o-mini
    # gpt-4o
    # gpt-4o-2024-08-06
    openai_model = "gpt-4o-mini"
    # claude-3-5-sonnet-20240620
    anthropic_model = "claude-3-5-sonnet-20240620"
    # gemini-1.5-pro
    google_model = "gemini-1.5-pro"

    chat_models = {
        "openai": ChatModelProvider(
            model=ChatOpenAI(model=openai_model, temperature=temperature),
            name=openai_model,
        ),
        "anthropic": ChatModelProvider(
            model=ChatAnthropic(model=anthropic_model, temperature=temperature),
            name=anthropic_model,
        ),
        "google": ChatModelProvider(
            model=ChatVertexAI(model=google_model, temperature=temperature),
            name=google_model,
        ),
    }
    try:
        return chat_models[normalized_provider]
    except KeyError:
        raise ValueError(f"Provider must be one of: {', '.join(chat_models.keys())}")
