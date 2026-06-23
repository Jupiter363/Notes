"""
CLI 命令行入口 —— 在终端中直接使用旅行规划助手。

这是最简入口，适合快速测试。完整的 Web 界面用 app.server。

使用方式：
    # 直接带参数
    python -m app.main "我想6月底去成都玩3天，预算3000，喜欢美食和轻松路线"

    # 交互式
    python -m app.main
"""

import sys
from app.services.planner_service import planner_service, session_service


def run_once(user_input: str, max_revision: int = 2):
    """
    执行一次完整的旅行规划。

    流程：
    1. 创建会话
    2. 调用 planner_service.plan()
    3. 如果信息不足，进入交互式追问循环
    4. 输出最终方案
    """

    print(f"\n{'='*60}")
    print(f"用户输入: {user_input}")
    print(f"{'='*60}\n")

    # 创建新会话（用于多轮追随）
    session_id = session_service.create_session()
    result = planner_service.plan(user_input, session_id=session_id, max_revision_count=max_revision)

    # 信息不足 → 进入追问循环
    if result["status"] == "need_user_clarification":
        print(result["message"])
        print()
        return _interactive_continue(session_id)

    # 信息完整 → 直接输出方案
    print(result["final_plan"])
    print(f"\n状态: {result['status']} | 修正轮次: {result['revision_count']}")
    return result


def _interactive_continue(session_id: str):
    """交互式追问循环 —— 持续问直到信息完整或用户退出。"""

    while True:
        user_input = input("\n请输入补充信息（或输入 'quit' 退出）: ").strip()
        if user_input.lower() == "quit":
            print("已退出。")
            return

        result = planner_service.continue_plan(session_id, user_input)

        # 还是不全 → 继续追问
        if result["status"] == "need_user_clarification":
            print(result["message"])
            continue

        # 全了 → 输出
        print(result["final_plan"])
        print(f"\n状态: {result['status']} | 修正轮次: {result.get('revision_count', 0)}")
        return


def main():
    """CLI 入口函数。"""

    # 如果命令行带了参数，直接用参数
    if len(sys.argv) > 1:
        # sys.argv[0] 是脚本名，[1:] 是用户输入的所有参数
        # join 把它们拼回一个字符串
        user_input = " ".join(sys.argv[1:])
    else:
        # 没有参数 → 交互式提示
        print("旅行规划助手 (LangChain + LangGraph)")
        print("-" * 40)
        user_input = input("请描述你的旅行需求: ").strip()

    # 用户直接回车 → 使用示例输入演示
    if not user_input:
        print("未输入任何需求，使用示例输入运行...")
        user_input = "我想6月底去成都玩3天，预算3000元，喜欢美食和轻松路线"

    run_once(user_input)


# Python 的惯用法：如果这个文件是直接运行的（python app/main.py），
# 就执行 main()；如果是从其他模块 import 的，就不执行。
if __name__ == "__main__":
    main()
