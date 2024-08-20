import os
import json
from enum import Enum
from typing import Dict
import time
from tqdm.asyncio import tqdm_asyncio
from langchain_core.documents import Document
from langchain_core.document_loaders import BaseLoader
from langchain_core.runnables import RunnablePassthrough, Runnable
from langchain_core.prompts import ChatPromptTemplate

from case_code.code_downloader import get_metadata
from models.case import CaseOutput
from utils.model_selector import ChatModelProvider, get_chat_model


from case_code import CASE_TRANSFORMED_PATH, CASE_METADATA_PATH, CASE_STATS_PATH


class TransformMetadata(Enum):
    TotalCases = "Total cases"
    NotFoundError = "Skipped: case not found"
    ParseError = "Skipped: parse error"


async def process_document(
    doc: Document,
    chain: Runnable,
    output_path: str,
    transform_metadata: Dict[TransformMetadata, int],
):
    metadata = doc.metadata
    meta_str = f"{metadata['case']}/{metadata['file']}"
    # Skip documents that do not match the criteria
    if "PartialBatchCase" not in doc.page_content:
        transform_metadata[TransformMetadata.NotFoundError] += 1
        return
    try:
        # Run the chain on the document
        result = await chain.ainvoke(doc.page_content)
        # Add the source metadata to the result
        rd = result.dict()
        for case in rd["cases"]:
            case["source"] = meta_str
            with open(output_path, "a") as f:
                f.write(json.dumps(case) + "\n")

            transform_metadata[TransformMetadata.TotalCases] += 1
    except Exception:
        transform_metadata[TransformMetadata.ParseError] += 1


async def transform(
    loader: BaseLoader,
    model_provider: ChatModelProvider = get_chat_model(),
    save_stats: bool = True,
) -> Dict[TransformMetadata, int]:
    """
    Asynchronously transform code documents into structured case outputs.

    This function processes documents loaded by the given loader, uses a language model
    to interpret the code, and saves the structured outputs to a JSONL file.

    Args:
        loader (BaseLoader): The document loader to use for fetching code documents.
        model (BaseChatModel, optional): The chat model to use for code interpretation.
            Defaults to the model returned by get_chat_model().

    Returns:
        Dict[TransformMetadata, int]: A dictionary containing metadata about the transformation process,
        including total cases processed, cases not found, and parse errors.
    """

    # Set the output path based on the model name
    output_path = CASE_TRANSFORMED_PATH.format(model=model_provider.name)
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a blockchain expert with extensive knowledge in TypeScript and blockchain transactions.\
Your task is to generate a structured output by following these specific guidelines.\
RULES:\
1. Use the user-provided code snippets to create a structured output.
2. The steps are typically detailed in the `previewTx` field.
3. Ensure that the number of steps in the `previewTx` matches the number specified in the `txn_count`.
4. If the data cannot be parsed, set it to `unknown`.
Follow these rules to provide accurate responses.""",
            ),
            ("human", "{code}"),
        ]
    )
    chain = (
        {"code": RunnablePassthrough()}
        | prompt
        | model_provider.model.with_structured_output(CaseOutput)
    )

    # Check if the file exists, and delete it if it does
    if os.path.exists(output_path):
        os.remove(output_path)

    transform_stats: Dict[TransformMetadata, int] = {}
    transform_stats[TransformMetadata.TotalCases] = 0
    transform_stats[TransformMetadata.NotFoundError] = 0
    transform_stats[TransformMetadata.ParseError] = 0

    # Get the total number of downloads
    total = get_metadata()["total_files"]

    print("Start processing files...")
    async for doc in tqdm_asyncio(
        loader.alazy_load(), desc="Processing files", unit="file", total=total
    ):
        await process_document(doc, chain, output_path, transform_stats)

    if save_stats:
        save_transformed_stats()

    return transform_stats


def save_transformed_stats():
    # Initialize model and JSONL file path
    model = get_chat_model()
    jsonl_file = CASE_TRANSFORMED_PATH.format(model=model.name)

    # Extract case IDs from the JSONL file
    with open(jsonl_file, "r") as file:
        transformed_cases = {
            json.loads(line)["id"] for line in file if "id" in json.loads(line)
        }

    # Read case_metadata.json
    with open(CASE_METADATA_PATH, "r") as file:
        metadata = json.load(file)
        metadata_cases = [case["id"] for case in metadata["cases"]]

    stats = {}
    # Last updated date
    stats["last_updated"] = int(time.time())
    # Total number of cases
    stats["total_cases"] = metadata["total_cases"]
    # Total number of failed cases
    stats["total_failed_cases"] = 0
    # Create a list of cases with their transformable status
    stats["cases"] = []
    for case in metadata_cases:
        transformable = case in transformed_cases
        stats["cases"].append({"id": case, "transformable": transformable})
        if not transformable:
            stats["total_failed_cases"] += 1

    # Save the stats to a JSON file
    with open(CASE_STATS_PATH.format(model=model.name), "w") as file:
        json.dump(stats, file)

    return stats


def get_transformed_stats():
    import pandas as pd

    model = get_chat_model()

    with open(CASE_STATS_PATH.format(model=model.name), "r") as file:
        stats = json.load(file)
    data = {
        "Title": ["total_cases", "total_failed_cases"],
        "Count": [stats["total_cases"], stats["total_failed_cases"]],
    }
    df = pd.DataFrame(data)
    return df
