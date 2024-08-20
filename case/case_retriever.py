from langchain_chroma import Chroma
from case.case_loader import get_case_doc_loader
from utils.model_selector import get_embedding, get_chat_model


model_name = get_chat_model().name
loader = get_case_doc_loader(f"data/case_{model_name}.jsonl")
docs = loader.load()
embedding_model = get_embedding()
db = Chroma.from_documents(documents=docs, embedding=embedding_model)


def get_retriever():
    return db.as_retriever()


if __name__ == "__main__":
    import json

    retriever = get_retriever()
    query = "Stake ETH with Lido and deposit to Eigenpie"
    results = retriever.invoke(query)
    print(f"[0] page_content: {results[0].page_content}")
    print(f"[0] case_id: {results[0].metadata['case_id']}")
    steps = results[0].metadata["steps"].replace("'", '"')
    print(f"[0] steps: {json.loads(steps)}")
