import functools
import operator
from typing import Sequence, TypedDict, Annotated, List

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph, START
from .agents import agent_node, supervisor_agent, analyst_agent
from rag.sqlite import get_directory_structure


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str


def graph(directory_path: str, prompt: str) -> List[str]:
    human_input = HumanMessage(content=prompt)

    members = get_directory_structure()
    output_list = []
    print(members)
    print(human_input)
    # graph 생성
    workflow = StateGraph(AgentState)
    supervisor_node = functools.partial(supervisor_agent, member_list=members)
    workflow.add_node("supervisor", supervisor_node)
    analyst_node = functools.partial(
        analyst_agent, input_prompt=human_input.content, output_list=output_list
    )
    workflow.add_node("analyst", analyst_node)
    for member in members:
        member_node = functools.partial(
            agent_node, directory_name=member, output_list=output_list
        )
        workflow.add_node(member, member_node)
        workflow.add_edge(member, "supervisor")
    conditional_map = {k: k for k in members}
    conditional_map["analyst"] = "analyst"
    workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)
    workflow.add_edge(START, "supervisor")
    workflow.add_edge("analyst", END)
    app = workflow.compile()

    # from IPython.display import Image, display
    # png_data = app.get_graph().draw_mermaid_png()
    # with open("graph_image.png", "wb") as file:
    #     file.write(png_data)

    previous_output = None
    for s in app.stream(
        {"messages": [human_input]},
        {"recursion_limit": 20},
    ):
        previous_output = s
        if "__end__" not in s:
            print(s)
            print("----")
    return previous_output["analyst"]["messages"]


# def graph():
#     for output in app.stream(human_input, stream_mode="updates"):
#         for key, value in output.items():
#             print(f"Output from node '{key}':")
#             print("---")
#             print(value["messages"][-1].pretty_print())
#         print("\n---\n")


if __name__ == "__main__":
    print(graph(""))
