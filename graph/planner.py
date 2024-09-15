import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from case.case_retriever import get_retriever
from models.case import BatchCase

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "planner"

system_prompt = """
You are a blockchain expert in EVM transactions.
Your task is to convert a description into the simplest possible set of actionable steps.

Guidelines:
- Keep the output concise and focused on the essential action.
- Avoid unnecessary technical details (e.g., creating a transaction, signing, broadcasting) unless explicitly requested by the user.
- Emphasize the high-level intent of the task over its technical implementation.
- Start each step with a verb to clearly define the action. (e.g. "Stake", "Approve", "Transfer")
- If the user's intent is unclear, refine it to create a coherent set of steps.
- Avoid including user interaction steps (e.g., confirmations or blockchain actions).
- Only include steps directly relevant to EVM blockchain transactions and aligned with the user's request.

Actions:
- For 'swap', use 'Uniswap' as the default decentralized exchange.
"""

user_prompt = """
Context: 
{context}

Description: 
{description}
"""


def format_docs(docs) -> str:
    return "\n\n".join(str(doc.metadata) for doc in docs)


retriever = get_retriever()

planner_prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), ("user", user_prompt)]
)

planner_model = ChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)

planner = (
    {"context": retriever | format_docs, "description": RunnablePassthrough()}
    | planner_prompt
    | planner_model.with_structured_output(BatchCase)
)
