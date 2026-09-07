from typing import Literal

from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START
from langgraph.graph.state import CompiledStateGraph, StateGraph
from pydantic import ValidationError

from graph.prompts import SYSTEM_PROMPT
from graph.state import State
from graph.tools import TOOLS, TOOLS_BY_NAME
from graph.utils import load_llm

llm_with_tools = load_llm().bind_tools(TOOLS)

def call_llm(state: State) -> State:


    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"]
    ]

    result = llm_with_tools.invoke(messages)

    return {"messages": [result]}


def tool_node(state: State) -> State:
    print("> tool node")
    llm_response = state["messages"][-1]

    # for message in state["messages"]:
    #     print(message)

    if not isinstance(llm_response, AIMessage) or not getattr(
        llm_response, "tool_calls", None
    ):
        return state

    call = llm_response.tool_calls[-1]
    name, args, id_ = call["name"], call["args"], call["id"]

    try:
        content = TOOLS_BY_NAME[name].invoke(args)
        # print(name, args, id_)
        status = "success"
    except (KeyError, IndexError, TypeError, ValidationError, ValueError) as error:
        content = f"Please, fix your mistakes: {error}"
        status = "error"

    tool_message = ToolMessage(content=content, tool_call_id=id_, status=status)

    return {"messages": [tool_message]}


def router(state: State) -> Literal["tool_node", "__end__"]:
    print("> router")

    llm_response = state["messages"][-1]

    print("TOOL CALLS:", llm_response.tool_calls)

    if llm_response.tool_calls:
        print("→ indo para tool_node")
        return "tool_node"

    print("→ resposta direta")
    return "__end__"


def build_graph() -> CompiledStateGraph[State, None, State, State]:
    builder = StateGraph(State)

    builder.add_node("call_llm", call_llm)
    builder.add_node("tool_node", tool_node)

    builder.add_edge(START, "call_llm")
    builder.add_conditional_edges("call_llm", router, ["tool_node", "__end__"])
    builder.add_edge("tool_node", "call_llm")

    return builder.compile(checkpointer=InMemorySaver())
