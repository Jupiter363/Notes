"""
全局配置 —— 从 .env 文件读取环境变量，集中管理。

Python 的 os.getenv() 从环境变量中读取值，如果不存在则用默认值。
python-dotenv 的 load_dotenv() 会自动把 .env 文件中的 KEY=VALUE
加载到环境变量中，这样敏感信息（API Key）不用写死在代码里。

使用方式：任何模块只需要 from app.config.settings import settings
就能拿到所有配置。
"""

import os
from dotenv import load_dotenv

# 自动读取项目根目录的 .env 文件
# .env 文件示例：
#   OPENAI_API_KEY=sk-xxxx
#   OPENAI_BASE_URL=https://api.deepseek.com/v1
#   MODEL_NAME=deepseek-chat
load_dotenv()


class Settings:
    """
    集中管理所有配置项。

    为什么用类而不是散落的 os.getenv()？
    - 一处修改，全局生效
    - IDE 有自动补全
    - 修改配置时不会漏掉某个文件
    """

    # ── LLM API 配置 ──
    # 支持所有 OpenAI 兼容的 API：OpenAI、DeepSeek、Qwen、Moonshot 等
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")

    # temperature=0 表示"不要创造性，严格按指令输出"
    # 对于结构化数据提取任务，temperature=0 是最佳选择
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0"))

    # Reflection 最大修正次数 —— 防止无限循环
    # Stage 2 §5.8：max_reflection_rounds 限制反思次数
    MAX_REVISION_COUNT: int = int(os.getenv("MAX_REVISION_COUNT", "2"))


# 单例 —— 整个项目共享这唯一一个配置对象
settings = Settings()
