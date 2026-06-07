from datetime import date
from typing import Any


def fallback_tool_result(source: str, error: str) -> dict:
    return {
        "data": {},
        "source": source,
        "updated_at": str(date.today()),
        "confidence": "low",
        "error": error,
    }


def safe_tool_call(tool, args: dict, fallback_source: str) -> tuple[dict, dict | None]:
    try:
        if hasattr(tool, "invoke"):
            result = tool.invoke(args)
        else:
            result = tool(args)
        return result, None
    except Exception as e:
        error = {
            "tool": getattr(tool, "name", str(tool)),
            "args": args,
            "error": str(e),
        }
        return fallback_tool_result(fallback_source, str(e)), error
