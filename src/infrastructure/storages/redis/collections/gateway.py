from .enums import Channel
from .enums import Namespace


class Gateway:
    @classmethod
    def presence_node_users(cls, node_id: str) -> str:
        return f"{Namespace.presence}:node:{node_id}:users"

    @classmethod
    def presence_user_nodes(cls, user_id: str) -> str:
        return f"{Namespace.presence}:user:{user_id}:nodes"

    @classmethod
    def node_events(cls, node_id: str) -> str:
        return f"{Namespace.gateway}:node:{node_id}:{Channel.events}"
