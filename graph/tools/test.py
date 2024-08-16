from langchain_core.tools import tool


@tool
async def get_weather(location: str) -> str:
    """Get the weather of a location"""
    return (
        "Low clouds followed by sunshine; breezy this afternoon, high 97F and low 81F."
    )
