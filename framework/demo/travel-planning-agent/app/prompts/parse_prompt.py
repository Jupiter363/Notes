from langchain_core.prompts import ChatPromptTemplate

parse_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个旅行需求解析器。请从用户输入中抽取结构化旅行需求。
如果某个字段没有明确出现，请返回 null 或空列表，不要编造。

偏好类型包括：美食、轻松、自然风光、历史文化、购物、亲子、拍照
节奏类型包括：轻松、适中、紧凑

{format_instructions}"""),
    ("human", "用户输入：{user_input}")
])
