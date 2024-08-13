"""
This script initializes and configures the components required for a blockchain expert assistant application. 
The assistant leverages various tools and a state machine to guide the user through the process.

Function:
- `get_app`: Returns the compiled graph representing the blockchain expert assistant application.
"""

from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START
from langgraph.graph.graph import CompiledGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from graph.state import State
from graph.assistant import Assistant
from graph.tools import tools
from utils.model_selector import get_chat_model


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful blockchain expert for composing transactions. "
            "Use the provided tools to search for protocols to assist the user in composing transactions. "
            "When searching, be persistent. Expand your query bounds if the first search returns no results. "
            "If a search comes up empty, expand your search before giving up."
            "\n\nCurrent user: {user_account}\n"
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

# Retrieve the model
llm = get_chat_model(temperature=0.7)

# Chain the prompt with the LLM and bind the available tools
assistant_runnable = prompt | llm.bind_tools(tools)

# Initialize the state graph to define the assistant's workflow
builder = StateGraph(State)
builder.add_node("assistant", Assistant(assistant_runnable))
builder.add_node("tools", ToolNode(tools))

# Define the workflow of the assistant.
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

# Set up a memory saver to handle checkpointing for state persistence
memory = MemorySaver()
app = builder.compile(checkpointer=memory)


def get_app() -> CompiledGraph:
    """
    Returns the compiled graph.
    Returns:
        app (CompiledGraph): The blockchain assistant.
    """
    return app
