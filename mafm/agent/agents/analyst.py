from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .llm_model import api_key
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import List, Literal


def analyst_agent(state, input_prompt: str, output_dict: List[str]):
    llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")

    class listResponse(BaseModel):
        messages: List[str]

    system_prompt = (
        "당신은 구성원들이 답변한 파일의 경로들을 받고 정리하는 감독자입니다."
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "주어진 사용자 요청과 파일 경로들을 보고 최대 10개의 파일 경로를 뽑아주세요"
                "사용자 요청: {input_prompt}"
                "파일 경로: {output_dict}",
            ),
        ]
    ).partial(input_prompt=input_prompt, output_dict=", ".join(output_dict))
    print(output_dict)
    analyst_chain = prompt | llm.with_structured_output(listResponse)
    return analyst_chain.invoke(state)
