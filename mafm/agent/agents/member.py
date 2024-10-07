from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from typing import Literal, List
from .llm_model import api_key

# from .tools import get_file_list
from langchain_openai import ChatOpenAI
from langgraph.store.base import BaseStore
from langchain.output_parsers import PydanticOutputParser
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_core.messages import HumanMessage

from rag.vectorDb import search


class routeResponse(BaseModel):
    messages: List[str] = Field(description="list of file path")


class queryResponse(BaseModel):
    query: str = Field(description="query string")
    directory_name: str = Field(description="directory name")


def get_file_list(query: queryResponse) -> List[str]:
    """
    get file list from user input
    """
    print(query)
    return search(query.directory_name + ".db", [query.query])


def agent_node(state, directory_name: str, output_dict: List[str]):
    llm = ChatOpenAI(
        api_key=api_key,
        model="gpt-4o-mini",
        temperature=0,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "directory_name: {directory_name} "
                "함수에 접근해서 파일 경로들을 리스트로 만들어주세요.",
            ),
        ]
    ).partial(
        directory_name=directory_name,
    )
    query_chain = prompt | llm.with_structured_output(queryResponse)
    chain = query_chain | get_file_list
    res = chain.invoke(state)
    print("RES", res, "\n\n\n\n")
    if res:
        output_dict.extend(res)
        return {"messages": res}
    else:
        return {"messages": []}
