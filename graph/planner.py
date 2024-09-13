import os

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "planner"

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from case.case_retriever import get_retriever
from models.case import BatchCase


system_prompt = """
You are an expert case generator specializing in EVM blockchain transactions. Your task is to convert a description into the simplest possible set of actionable steps.

Rules:
- Ensure the output is concise and limited to the essential action.
- Avoid unnecessary technical details (e.g., creating a transaction, signing, broadcasting) unless explicitly requested by the user.
- Focus on the high-level intent of the task, not the technical implementation.
- If the user's intent is unclear, refine it as needed to generate a coherent set of steps.
- Do not include steps that require user interaction (e.g., asking for confirmations or actions on the blockchain).
- Only generate steps directly relevant to EVM blockchain transactions and in line with the user's high-level request.

Context:
{context}"""


def format_docs(docs) -> str:
    return "\n\n".join(str(doc.metadata) for doc in docs)


retriever = get_retriever()

user_intent = "Description: {description}"

planner_prompt = ChatPromptTemplate.from_messages([system_prompt, user_intent])

planner_model = ChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)

planner = (
    {"context": retriever | format_docs, "description": RunnablePassthrough()}
    | planner_prompt
    | planner_model.with_structured_output(BatchCase)
)
