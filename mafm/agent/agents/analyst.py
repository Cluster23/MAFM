from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .llm_model import api_key
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import List, Literal


def analyst_agent(state, input_prompt: str):
    llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")

    class listResponse(BaseModel):
        messages: List[str]
        next: Literal["END"]

    system_prompt = (
        "당신은 구성원들이 답변한 파일의 경로들을 받고 정리하는 감독자입니다."
        "주어진 사용자 요청에 따라, 선택된 파일의 경로들을 리스트로 제공하십시오."
        "그리고 END를 입력하여 종료하십시오"
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "이전에 나온 파일의 경로들을 통합해서 사용자의 요청에 맞게 정리해주세요."
                "사용자 요청: {input_prompt}"
                "디렉토리: ",
            ),
        ]
    ).partial(input_prompt=input_prompt)
    analyst_chain = prompt | llm.with_structured_output(listResponse)
    return analyst_chain.invoke(state)
