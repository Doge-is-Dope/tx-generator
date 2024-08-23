import os
import json
import time
from enum import Enum
from typing import Dict, Optional
from tqdm.asyncio import tqdm_asyncio

from langchain_core.documents import Document
from langchain_core.document_loaders import BaseLoader
from langchain_core.runnables import RunnablePassthrough, Runnable
from langchain_core.prompts import ChatPromptTemplate

from case_code.code_downloader import get_metadata
from models.case import CaseOutput
from utils.model_selector import ChatModelProvider, get_chat_model, model_names


from case_code import CASE_CONVERTED_PATH, CASE_METADATA_PATH, CASE_STATS_PATH


class ConversionMetadata(Enum):
    TotalCases = "Total cases"
    NotFoundError = "Skipped: case not found"
    ParseError = "Skipped: parse error"


async def process_document(
    doc: Document,
    chain: Runnable,
    output_path: str,
    conversion_metadata: Dict[ConversionMetadata, int],
):
    metadata = doc.metadata
    meta_str = f"{metadata['case']}/{metadata['file']}"
    # Skip documents that do not match the criteria
    if "PartialBatchCase" not in doc.page_content:
        conversion_metadata[ConversionMetadata.NotFoundError] += 1
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

            conversion_metadata[ConversionMetadata.TotalCases] += 1
    except Exception:
        conversion_metadata[ConversionMetadata.ParseError] += 1


async def convert(
    loader: BaseLoader,
    model_provider: ChatModelProvider = get_chat_model(),
    save_stats: bool = True,
) -> Dict[ConversionMetadata, int]:
    """
    Asynchronously convert code documents into structured case outputs.

    This function processes documents loaded by the given loader, uses a language model
    to interpret the code, and saves the structured outputs to a JSONL file.

    Args:
        loader (BaseLoader): The document loader to use for fetching code documents.
        model (BaseChatModel, optional): The chat model to use for code interpretation.
            Defaults to the model returned by get_chat_model().

    Returns:
        Dict[ConversionMetadata, int]: A dictionary containing metadata about the conversion process,
        including total cases processed, cases not found, and parse errors.
    """

    # Set the output path based on the model name
    output_path = CASE_CONVERTED_PATH.format(model=model_provider.name)
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

    conversion_stats: Dict[ConversionMetadata, int] = {}
    conversion_stats[ConversionMetadata.TotalCases] = 0
    conversion_stats[ConversionMetadata.NotFoundError] = 0
    conversion_stats[ConversionMetadata.ParseError] = 0

    # Get the total number of downloads
    total = get_metadata()["total_files"]

    print(f"Start converting with {model_provider.name}...")

    start_time = int(time.time())

    async for doc in tqdm_asyncio(
        loader.alazy_load(), desc="Converting", unit="file", total=total
    ):
        await process_document(doc, chain, output_path, conversion_stats)

    duration = int(time.time()) - start_time
    if save_stats:
        save_conversion_stats(duration)

    return conversion_stats


def save_conversion_stats(duration: int):
    # Initialize model and JSONL file path
    model = get_chat_model()
    jsonl_file = CASE_CONVERTED_PATH.format(model=model.name)

    # Extract case IDs from the JSONL file
    with open(jsonl_file, "r") as file:
        converted_cases = {
            json.loads(line)["id"] for line in file if "id" in json.loads(line)
        }

    # Read case_metadata.json
    with open(CASE_METADATA_PATH, "r") as file:
        metadata = json.load(file)
        metadata_cases = [case["id"] for case in metadata["cases"]]

    stats = {}
    # Last updated date
    stats["last_updated"] = int(time.time())
    # Total time taken to convert
    stats["total_time_taken"] = duration
    # Total number of cases
    stats["total_cases"] = metadata["total_cases"]
    # Total number of failed cases
    stats["failed_cases"] = 0
    # Create a list of cases with their convertible status
    stats["cases"] = []
    for case in metadata_cases:
        convertible = case in converted_cases
        stats["cases"].append({"id": case, "convertible": convertible})
        if not convertible:
            stats["failed_cases"] += 1
    # Save the stats to a JSON file
    with open(CASE_STATS_PATH.format(model=model.name), "w") as file:
        json.dump(stats, file)

    return stats


def get_conversion_stats(model_name: Optional[str] = None):
    """Get the stats of the converted cases for a given model."""
    name = model_name or get_chat_model().name

    with open(CASE_STATS_PATH.format(model=name), "r") as file:
        stats = json.load(file)
    return stats


def get_all_conversion_stats():
    """Get the stats of the converted cases for all models."""
    stats = {}
    names = [name for names in model_names.values() for name in names]
    for name in names:
        file_path = CASE_STATS_PATH.format(model=name)
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                model_stats = json.load(file)
                stats[name] = model_stats
    return stats


def sort_converted_cases(model_name: Optional[str] = None):
    """Sort the converted cases for a given model."""
    name = model_name or get_chat_model().name
    file_path = CASE_CONVERTED_PATH.format(model=name)
    with open(file_path, "r") as file:
        lines = [json.loads(line) for line in file]
    sorted_lines = sorted(lines, key=lambda x: x["id"])
    with open(file_path, "w") as file:
        for line in sorted_lines:
            file.write(json.dumps(line) + "\n")
