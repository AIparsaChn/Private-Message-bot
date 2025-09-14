import asyncio

from typing import Union, Optional
from redis.asyncio import Redis


class RedisDatabase():
    GROUP_CHAT_ID_KEY = "groups:chat_id"
    _pool = None

    @classmethod
    async def _connect(cls):
        if cls._pool is None:
            cls._pool = await Redis.from_url(
                url="redis://localhost:6379/0",
                decode_responses=True
            )
        return cls._pool

    @classmethod
    async def add_chat_id(cls, chat_id: Union[str, int]):
        connection: Redis = await cls._connect()
        if isinstance(chat_id, int):
            chat_id = str(chat_id)
        await connection.sadd(cls.GROUP_CHAT_ID_KEY, chat_id)
        return None

    @classmethod
    async def check_chat_id(cls, chat_id: Union[str, int]) -> bool:
        connection: Redis = await cls._connect()
        if isinstance(chat_id, int):
            chat_id = str(chat_id)
        result = await connection.sismember(cls.GROUP_CHAT_ID_KEY, chat_id)
        return result

    @classmethod
    async def store_private_message(cls, target_user_id: str, target_group_chat_id: str,
                private_message_id: str, private_message_text: str):
        connection: Redis = await cls._connect()

        key = f"reciever_user:{target_group_chat_id}:{target_user_id}:{private_message_id}"
        await connection.set(key, private_message_text, ex=86400) # Delete after 24 hours to reduce memory usage. '86400 = 1 day'
        return None




