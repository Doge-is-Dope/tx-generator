import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from case.case_retriever import get_retriever
from models.case import BatchCase

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "planner"

system_prompt = """
You are an expert in EVM (Ethereum Virtual Machine) blockchain transactions.

Your role is to convert user-provided descriptions into a clear and concise set of actionable steps related to EVM transactions.

Instructions for creating steps:
- Begin each step with an action verb such as “Stake,” “Approve,” or “Transfer.”
- Ensure prompts and outputs are as concise as possible while retaining necessary details.
- Always include exact amounts or token names where relevant (e.g., “Approve 100 USDT for Uniswap”).
- Focus on essential steps only, omitting unnecessary details or user interactions.
- Limit response length by avoiding detailed technical explanations unless explicitly requested.
- Use default options (e.g., Uniswap for swaps) when no alternatives are specified.

When describing swap operations, default to using Uniswap unless otherwise specified.
"""

user_prompt = """
Context: 
{context}

Description: {description}
"""


def format_docs(docs) -> str:
    return "\n\n".join(str(doc.metadata) for doc in docs)


retriever = get_retriever()

planner_prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), ("user", user_prompt)]
)

planner_model = ChatOpenAI(model="gpt-4o", temperature=0)

planner = (
    {"context": retriever | format_docs, "description": RunnablePassthrough()}
    | planner_prompt
    | planner_model.with_structured_output(BatchCase)
)
