from functools import lru_cache
from pydantic import BaseModel
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


# List of supported models for each provider.
# The first model is the default one.
model_names = {
    "openai": [
        "gpt-4o-mini",
        "gpt-4o-2024-08-06",
        "gpt-4o",
    ],
    "anthropic": [
        "claude-3-5-sonnet-20240620",
    ],
    "google": [
        "gemini-1.5-pro",
        "gemini-1.0-pro",
        # gemini-1.5-flash (not supported)
    ],
}


@lru_cache(maxsize=4)
def get_chat_model(
    provider: str | None = None,
    temperature: float = 0,
) -> ChatModelProvider:
    normalized_provider = provider or _get_provider().strip().lower()
    try:
        # Use the first model as default
        model_name = model_names[normalized_provider][0]
        chat_models = {
            "openai": ChatModelProvider(
                model=ChatOpenAI(model=model_name, temperature=temperature),
                name=model_name,
            ),
            "anthropic": ChatModelProvider(
                model=ChatAnthropic(model=model_name, temperature=temperature),
                name=model_name,
            ),
            "google": ChatModelProvider(
                model=ChatVertexAI(model=model_name, temperature=temperature),
                name=model_name,
            ),
        }
        return chat_models[normalized_provider]
    except KeyError:
        raise ValueError(
            f"Provider must be one of the following: {', '.join(model_names.keys())}"
        )
