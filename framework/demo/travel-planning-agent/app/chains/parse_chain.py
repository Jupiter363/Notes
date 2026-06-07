import json
from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda

from app.config.settings import settings
from app.prompts.parse_prompt import parse_prompt
from app.schemas.travel_request import TravelRequest


_stream_queue = None


def set_stream_queue(queue):
    global _stream_queue
    _stream_queue = queue


@lru_cache(maxsize=1)
def _get_model():
    return init_chat_model(
        settings.MODEL_NAME,
        model_provider="openai",
        openai_api_key=settings.OPENAI_API_KEY,
        openai_api_base=settings.OPENAI_BASE_URL,
        temperature=settings.TEMPERATURE,
    )


def _build_parse_chain():
    parser = PydanticOutputParser(pydantic_object=TravelRequest)
    prompt_with_format = parse_prompt.partial(format_instructions=parser.get_format_instructions())
    return prompt_with_format | _get_model() | parser


def _invoke(input_dict: dict):
    q = _stream_queue
    if q is None:
        return _build_parse_chain().invoke(input_dict)

    model = _get_model()
    parser = PydanticOutputParser(pydantic_object=TravelRequest)
    prompt_with_format = parse_prompt.partial(format_instructions=parser.get_format_instructions())
    messages = prompt_with_format.invoke(input_dict)

    full_text = ""
    for chunk in model.stream(messages):
        token = chunk.content if hasattr(chunk, 'content') else str(chunk)
        if token:
            full_text += token
            try:
                q.put_nowait(json.dumps({"type": "token", "token": token}, ensure_ascii=False))
            except Exception:
                pass

    return parser.parse(full_text)


parse_chain = RunnableLambda(_invoke)
