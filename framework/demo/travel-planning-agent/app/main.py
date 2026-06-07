"""
旅行规划助手 CLI 入口。

用法:
    # 单次规划
    python -m app.main

    # 或指定输入
    python -m app.main "我想6月底去成都玩3天，预算3000，喜欢美食和轻松路线"
"""

import sys
from app.services.planner_service import planner_service, session_service


def run_once(user_input: str, max_revision: int = 2):
    print(f"\n{'='*60}")
    print(f"用户输入: {user_input}")
    print(f"{'='*60}\n")

    session_id = session_service.create_session()
    result = planner_service.plan(user_input, session_id=session_id, max_revision_count=max_revision)

    if result["status"] == "need_user_clarification":
        print(result["message"])
        print()
        return _interactive_continue(session_id)

    print(result["final_plan"])
    print(f"\n状态: {result['status']} | 修正轮次: {result['revision_count']}")
    return result


def _interactive_continue(session_id: str):
    while True:
        user_input = input("\n请输入补充信息（或输入 'quit' 退出）: ").strip()
        if user_input.lower() == "quit":
            print("已退出。")
            return

        result = planner_service.continue_plan(session_id, user_input)

        if result["status"] == "need_user_clarification":
            print(result["message"])
            continue

        print(result["final_plan"])
        print(f"\n状态: {result['status']} | 修正轮次: {result.get('revision_count', 0)}")
        return


def main():
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
    else:
        print("旅行规划助手 (LangChain + LangGraph)")
        print("-" * 40)
        user_input = input("请描述你的旅行需求: ").strip()

    if not user_input:
        print("未输入任何需求，使用示例输入运行...")
        user_input = "我想6月底去成都玩3天，预算3000元，喜欢美食和轻松路线"

    run_once(user_input)


if __name__ == "__main__":
    main()
