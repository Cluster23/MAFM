from typing import Annotated
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from rag.vectorDb import search


@tool("get_file_list")
def get_file_list(
    query: Annotated[str, "query"], member: Annotated[str, "directory name"]
) -> Annotated[list, "file_list"]:
    """
    get file list from user input
    """
    return search(member + ".db", query)
