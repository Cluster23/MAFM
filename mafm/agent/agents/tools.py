# # Legacy
# from typing import Annotated
# from pydantic import BaseModel, Field
# from langchain_core.tools import tool
# from rag.vectorDb import search


# @tool("get_file_list")
# def get_file_list(
#     query: Annotated[str, "query"], directory_name: Annotated[str, "directory name"]
# ) -> Annotated[list, "file_list"]:
#     """
#     get file list from user input
#     """
#     # return search(member + ".db", query)
#     return [
#         f"file1_{directory_name}.txt",
#         f"file2_{directory_name}.txt",
#         f"file3_{directory_name}.txt",
#     ]
