# Findings & Decisions

## Requirements
- Full LangChain + LangGraph travel planning agent
- Structured output with Pydantic schemas
- Reflection loop with revision control
- Tool adapter pattern with mock providers
- CLI interface for testing
- Comprehensive test suite

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Python >= 3.11 | Document requirement, modern type hints |
| langchain >= 1.1, langgraph >= 1.0 | Document specified versions |
| Dict-based state convention | Document: model_dump() stored in state |
| max_revision_count = 2 | Document recommendation |
| OpenAI-compatible API | Supports multiple providers |

## Resources
- Design document: 基于_LangChain_LangGraph_旅行规划助手技术方案_工程闭环版.md
- LangChain docs: https://docs.langchain.com/oss/python/langchain/overview
- LangGraph docs: https://docs.langchain.com/oss/python/langgraph/overview
