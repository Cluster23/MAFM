from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .llm_model import api_key
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import List, Literal


def supervisor_agent(state, member_list: List[str]):
    llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")

    next_options = member_list + ["analyst"]

    class routeResponse(BaseModel):
        next: Literal[*(next_options)]

    system_prompt = (
        "당신은 사용자의 요청에 따라 디렉토리를 선택하는 감독자입니다."
        "3번 디렉토리를 선택했으면 'analyst'를 선택해주세요."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "선택할 수 있는 디렉토리는 다음과 같습니다: {members}. "
                "디렉토리를 선택해주세요. 절대로 같은 디렉토리를 두 번 선택하지 마세요.",
            ),
        ]
    ).partial(members=", ".join(member_list))

    supervisor_chain = prompt | llm.with_structured_output(routeResponse)
    return supervisor_chain.invoke(state)
