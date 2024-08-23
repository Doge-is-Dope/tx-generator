from langchain_chroma import Chroma

from case.case_loader import get_case_doc_loader
from case_code import CASE_TRANSFORMED_PATH
from utils.model_selector import get_embedding, get_chat_model


# Load the case documents
model_name = get_chat_model().name
loader = get_case_doc_loader(CASE_TRANSFORMED_PATH.format(model=model_name))
docs = loader.load()
# Create the embedding model
embedding_model = get_embedding()
# Update the vector database
db = Chroma.from_documents(documents=docs, embedding=embedding_model)


def get_retriever():
    return db.as_retriever()
