from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel
from typing import Literal, List
from .llm_model import api_key
from .tools import get_file_list
from langchain_openai import ChatOpenAI
from langgraph.store.base import BaseStore
from langchain.output_parsers import PydanticOutputParser
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_core.messages import HumanMessage


class routeResponse(BaseModel):
    messages: List[str]
    next: Literal["supervisor"]


def agent_node(state, agent, directory_name):
    prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "함수에 접근해서 디렉토리들을 골라주세요.",
            ),
        ]
    )
    result = agent.invoke(state)
    return {
        "messages": [
            HumanMessage(content=result["messages"][-1].content, name=directory_name)
        ]
    }


# def agent_node(state, agent_name: str):
#     llm = ChatOpenAI(
#         api_key=api_key,
#         model="gpt-4o-mini",
#         temperature=0,
#     )

#     function = convert_to_openai_function(get_file_list)

#     # Prepare the prompt
#     prompt = ChatPromptTemplate.from_messages(
#         [
#             MessagesPlaceholder(variable_name="messages"),
#             (
#                 "system",
#                 "함수에 접근해서 디렉토리들을 골라주세요.",
#             ),
#         ]
#     )

#     chain = prompt | llm.with_structured_output(routeResponse)
#     res = chain.invoke(state)

#     print("RES", res, "\n\n\n\n")
#     # store.put((agent_name), "restrict", res.messages)
#     return res
