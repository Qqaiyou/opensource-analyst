"""验证 LangGraph 安装和基本功能。"""
import importlib.metadata

print(f"LangGraph version: {importlib.metadata.version('langgraph')}")

from langgraph.graph import StateGraph
from typing import TypedDict


class TestState(TypedDict):
    message: str


def hello(state: TestState) -> dict:
    return {"message": f"Hello, {state['message']}!"}


graph = StateGraph(TestState)
graph.add_node("hello", hello)
graph.set_entry_point("hello")
graph.set_finish_point("hello")

app = graph.compile()
result = app.invoke({"message": "LangGraph"})
print(f"Result: {result}")
print("LangGraph is working correctly! ✅")
