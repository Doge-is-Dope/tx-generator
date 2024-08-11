from langchain_community.document_loaders import JSONLoader


def _metadata_func(record: dict, metadata: dict) -> dict:
    """Function to extract metadata from the record"""
    metadata["case_id"] = record.get("id")
    metadata["total_steps"] = record.get("total_steps")
    # Convert the steps to string since chroma does not support list
    metadata["steps"] = str(record.get("steps"))
    metadata["source"] = record.get("source")
    return metadata


def get_case_doc_loader(file_path):
    return JSONLoader(
        file_path=file_path,
        jq_schema=".",
        content_key="description",
        json_lines=True,
        metadata_func=_metadata_func,
    )


if __name__ == "__main__":
    loader = get_case_doc_loader("data/case_gpt-4o-mini.jsonl")
    docs = loader.load()
    print(f"Total docs: {len(docs)}")
    print(f"Content: {docs[1].page_content[:100]}")
    print(f"Case ID: {docs[1].metadata['id']}")
    print(f"Source: {docs[1].metadata['source']}")
