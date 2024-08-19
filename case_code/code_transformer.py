import os
import json
from enum import Enum
from typing import Dict
from tqdm.asyncio import tqdm_asyncio
from langchain_core.documents import Document
from langchain_core.document_loaders import BaseLoader
from langchain_core.runnables import RunnablePassthrough, Runnable
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

from models import CaseOutput
from case_code.code_downloader import get_metadata
from utils.model_selector import get_chat_model


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
    model: BaseChatModel = get_chat_model(),
    output_dir: str = "data",
) -> Dict[TransformMetadata, int]:
    output_path = f"{output_dir}/case_{model.model_name}.jsonl"
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a blockchain expert with extensive knowledge in TypeScript and blockchain transactions. 
                Your task is to generate a structured output by following these specific guidelines.
                RULES:
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
        | model.with_structured_output(CaseOutput)
    )

    # Check if the file exists, and delete it if it does
    if os.path.exists(output_path):
        os.remove(output_path)

    transform_metadata: Dict[TransformMetadata, int] = {}
    transform_metadata[TransformMetadata.TotalCases] = 0
    transform_metadata[TransformMetadata.NotFoundError] = 0
    transform_metadata[TransformMetadata.ParseError] = 0

    # Get the total number of downloads
    total = get_metadata()["total_downloads"]

    print("Start processing files...")
    async for doc in tqdm_asyncio(
        loader.alazy_load(), desc="Processing files", unit="file", total=total
    ):
        await process_document(doc, chain, output_path, transform_metadata)

    return transform_metadata


def get_transformation_result():
    import pandas as pd

    # Read the CSV file into a DataFrame
    csv_file = "raw_data/cases.csv"
    df = pd.read_csv(csv_file)

    # Initialize model and JSONL file path
    model = get_chat_model()
    jsonl_file = f"data/case_{model.model_name}.jsonl"

    # Extract case IDs from the JSONL file
    with open(jsonl_file, "r") as file:
        case_ids = {json.loads(line)["id"] for line in file if "id" in json.loads(line)}

    # Update the 'transformable' column based on whether 'id' is in case_ids
    df["transformable"] = df["id"].isin(case_ids) | df["transformable"]

    # Save the updated DataFrame back to the CSV file
    df.to_csv(csv_file, index=False)

    return df
