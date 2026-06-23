"""
会话管理服务 —— 用内存字典保存每个用户会话的状态。

这是一个极简实现：用 Python dict 存储所有会话，key 是 session_id，
value 是完整的 TravelState dict。

局限性（后续可以扩展）：
- 服务重启后会话全部丢失（可升级为 Redis 持久化）
- 没有过期清理机制（可加 TTL）
- 不支持多进程共享（可升级为 Redis/数据库）

对于教学 Demo，这个实现足够清晰易懂。
"""

import uuid
from typing import Dict


class SessionService:
    """
    内存会话存储。

    使用方式：
        svc = SessionService()
        sid = svc.create_session()           # 创建新会话
        svc.update_state(sid, state_dict)    # 保存/更新状态
        state = svc.get_state(sid)           # 读取状态
        svc.delete_session(sid)              # 删除会话
    """

    def __init__(self):
        # _sessions 是一个普通 Python 字典
        # key: session_id（8位随机字符串）
        # value: TravelState 的完整 dict
        self._sessions: Dict[str, dict] = {}

    def create_session(self) -> str:
        """
        创建新会话，返回唯一的 session_id。

        uuid.uuid4() 生成一个全局唯一的随机ID，如 "a1b2c3d4-..."
        [:8] 取前8个字符，如 "a1b2c3d4"，足够短又足够唯一。
        """
        session_id = str(uuid.uuid4())[:8]
        self._sessions[session_id] = {}
        return session_id

    def get_state(self, session_id: str) -> dict:
        """
        读取指定会话的完整状态。

        如果 session_id 不存在，返回空字典 {} —— 不会报错。
        这是 Python 字典的 .get() 方法的默认行为。
        """
        return self._sessions.get(session_id, {})

    def update_state(self, session_id: str, state: dict) -> None:
        """
        更新（覆盖）指定会话的状态。

        注意：这是完全覆盖，不是合并。如果需要部分更新，
        调用方应该先 get_state 再合并后再 update_state。
        """
        self._sessions[session_id] = state

    def delete_session(self, session_id: str) -> None:
        """
        删除指定会话。

        pop(key, None) 在 key 不存在时返回 None 而不是报错。
        """
        self._sessions.pop(session_id, None)


# 全局单例 —— 整个应用共享同一个会话管理器
session_service = SessionService()
