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
import os

from rag.vectorDb import search

global current_directory_name


class queryResponse(BaseModel):
    query: str = Field(description="query sentence")


def get_file_list(query: queryResponse) -> List[str]:
    """
    get file list from user input
    """
    global current_directory_name

    print("current_directory_name: ", current_directory_name)
    print("query: ", query)
    return search(
        current_directory_name + "/" + os.path.basename(current_directory_name) + ".db",
        [query.query],
    )


def agent_node(state, directory_name: str, output_list: List[str]):
    global current_directory_name
    current_directory_name = directory_name

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
                "current directory name: {directory_name} "
                "사용자에 요청에 따라서 디렉토리에서 파일을 검색하려고 합니다 쿼리를 문장으로 정리해주세요",
            ),
        ]
    ).partial(
        directory_name=directory_name,
    )
    query_chain = prompt | llm.with_structured_output(queryResponse)
    chain = query_chain | get_file_list
    res = chain.invoke(state)
    if res:
        output_list.extend(res)
        return {"messages": res}
    else:
        return {"messages": []}
