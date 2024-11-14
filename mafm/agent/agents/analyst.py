from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .llm_model import api_key
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import List, Literal


def analyst_agent(state, input_prompt: str, output_list: List[str]):
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
                "주어진 파일 경로들 안에서 사용자 요청에 맞는 파일 경로만 뽑아주세요. 주어지지 않은 파일 경로는 뽑으면 안됩니다."
                "사용자 요청: {input_prompt}"
                "파일 경로: {output_list}",
            ),
        ]
    ).partial(input_prompt=input_prompt, output_list=", ".join(output_list))
    print(output_list)
    analyst_chain = prompt | llm.with_structured_output(listResponse)
    return analyst_chain.invoke(state)
