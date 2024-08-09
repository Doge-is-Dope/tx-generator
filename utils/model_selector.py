from functools import lru_cache
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import ChatVertexAI


@lru_cache(maxsize=4)
def get_embedding(provider: str = "openai") -> Embeddings:
    normalized_provider = provider.strip().lower()
    chat_models = {
        "openai": OpenAIEmbeddings(
            # text-embedding-3-large
            # text-embedding-3-small
            model="text-embedding-3-large",
        )
    }
    try:
        return chat_models[normalized_provider]
    except KeyError:
        raise ValueError(f"Provider must be one of: {', '.join(chat_models.keys())}")


@lru_cache(maxsize=4)
def get_chat_model(provider: str = "openai", temperature: float = 0.3) -> BaseChatModel:
    normalized_provider = provider.strip().lower()
    chat_models = {
        "openai": ChatOpenAI(
            # gpt-4o-mini
            # gpt-4o-2024-08-06
            model="gpt-4o-2024-08-06",
            temperature=temperature,
        ),
        "anthropic": ChatAnthropic(
            model="claude-3-5-sonnet-20240620",
            temperature=temperature,
        ),
        "google": ChatVertexAI(
            model="gemini-1.5-pro",
            temperature=temperature,
        ),
    }
    try:
        return chat_models[normalized_provider]
    except KeyError:
        raise ValueError(f"Provider must be one of: {', '.join(chat_models.keys())}")
