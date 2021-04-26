from abc import abstractmethod

import aioredis


class AbstractDB:
    """Abstract Key DB interface"""

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    @classmethod
    async def create(cls, connection: str):
        """Async DB initializer"""
        pass

    @abstractmethod
    async def create_user(self, user_id: int, username: str):
        """Creates telegram_id-username connection"""

    @abstractmethod
    async def create_key(self, user_id: int, publickey: str):
        """Records a public key for given telegram_id"""

    @abstractmethod
    async def is_registered(self, user_id: int):
        """Checks whether user is already registered"""

    @abstractmethod
    async def contains(self, username: str):
        """Checks whether given username is already taken"""

    @abstractmethod
    async def update_key(self, user_id: int, publickey: str):
        """Updates a public key for given telegram_id"""

    @abstractmethod
    async def get_username(self, user_id: int):
        """Gets username by telegram_id"""

    @abstractmethod
    async def get_publickey(self, user_id: int):
        """Gets publickey by telegram_id"""

    @abstractmethod
    async def close(self):
        """Closes connection to DB"""


class RedisDB(AbstractDB):
    def __init__(self):
        self.conn = None

    @classmethod
    async def create(cls, connection: str):
        """Async Redis backed initializer"""
        self = RedisDB()
        self.conn = await aioredis.create_redis_pool(connection)

    async def create_user(self, user_id: int, username: str):
        await self.conn.execute("set", f"user:{user_id}", username)

    async def close(self):
        """Closes connection to redis"""
        self.conn.close()
        await self.conn.wait_closed()
