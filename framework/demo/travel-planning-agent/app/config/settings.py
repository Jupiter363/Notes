import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0"))

    MAX_REVISION_COUNT: int = int(os.getenv("MAX_REVISION_COUNT", "2"))

    # json_schema (OpenAI strict) / json_mode (DeepSeek, Qwen, etc.) / function_calling
    STRUCTURED_OUTPUT_METHOD: str = os.getenv("STRUCTURED_OUTPUT_METHOD", "json_mode")


settings = Settings()
