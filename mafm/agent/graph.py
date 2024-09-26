import functools
import operator
from typing import Sequence, TypedDict, Annotated

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import create_react_agent
from agents import agent_node, supervisor_agent, llm
from tools import print_abc


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str


members = ["Dir1", "Dir2", "Dir3"]

workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_agent)
agents = {}
for member in members:
    agents[member] = create_react_agent(llm, tools=[print_abc])
    research_node = functools.partial(agent_node, agent=agents[member], name=member)
    workflow.add_node(member, agents[member])
    workflow.add_edge(member, "supervisor")

conditional_map = {k: k for k in members}
conditional_map["FINISH"] = END
workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)
workflow.add_edge(START, "supervisor")

graph = workflow.compile()

for s in graph.stream(
    {
        "messages": [
            HumanMessage(content="Code hello world and print it to the terminal")
        ]
    }
):
    if "__end__" not in s:
        print(s)
        print("----")
