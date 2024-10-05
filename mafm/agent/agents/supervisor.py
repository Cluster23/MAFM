from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .llm_model import api_key
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import List, Literal


def supervisor_agent(state, member_list: List[str]):
    llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")

    next_options = member_list + ["analyst"]

    class routeResponse(BaseModel):
        messages: List[str]
        next: Literal[*(next_options)]

    system_prompt = (
        "각각의 디렉토리는 다양한 정보가 포함된 파일들에 대한 정보를 가지고 있습니다: {members}. "
        "당신은 사용자의 요청에 따라 어떤 정보가 필요할지 결정하는 감독자입니다."
        "더 이상 정보를 원하지 않는다면 'analyst'를 선택해주세요."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "선택할 수 있는 디렉토리는 다음과 같습니다: {members}. "
                "디렉토리들을 골라주세요.",
            ),
        ]
    ).partial(members=", ".join(member_list))

    supervisor_chain = prompt | llm.with_structured_output(routeResponse)
    return supervisor_chain.invoke(state)
