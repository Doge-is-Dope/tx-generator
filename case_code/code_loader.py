import os
import glob
from typing import List, Iterator
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from case_code import RAW_DIR


class CodeLoader(BaseLoader):
    """
    Loads code snippets from the batch case codebase.
    """

    def _get_cases(self):
        import json

        with open("raw_data/meta.json", "r") as f:
            cases = json.load(f)
            # Transform the list of dictionaries into the desired dictionary format

        transformed_data = {
            case["id"]: {
                "chain_id": case["chain_id"],
                "preview_txn_count": case["preview_txn_count"],
            }
            for case in cases
        }
        return transformed_data

    def _extract_case_name(self, file_path: str) -> tuple[str, str]:
        path_components = file_path.split(os.sep)
        case_index = path_components.index("cases")
        return path_components[case_index + 1], path_components[-1]

    def load(self) -> List[Document]:
        """Load data into Document objects."""
        return list(self.lazy_load())

    def lazy_load(self) -> Iterator[Document]:
        case_dir_path = os.path.join(RAW_DIR, "cases")
        file_pattern = os.path.join(case_dir_path, "**", "*")
        for file_path in glob.iglob(file_pattern, recursive=True):
            if os.path.isfile(file_path):
                with open(file_path, "r") as file:
                    content = file.read()
                    case_name, file_name = self._extract_case_name(file_path)
                    yield Document(
                        page_content=content,
                        metadata={"case": case_name, "file": file_name},
                    )


async def async_code_loader():
    loader = CodeLoader()
    async for doc in loader.alazy_load():
        print()
        print(type(doc))
        print(doc.metadata)


if __name__ == "__main__":
    import asyncio

    loader = CodeLoader()
    asyncio.run(async_code_loader())
