from src.common.http.collections import HTTPError


class ChatNotFound(HTTPError): ...


class ChatMemberRequired(HTTPError): ...
