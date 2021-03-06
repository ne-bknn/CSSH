from abc import abstractmethod

import aioredis


class AbstractDB:
    """Abstract Key DB interface"""

    @abstractmethod
    def __init__(self):
        pass

    @classmethod
    @abstractmethod
    async def create(cls, connection: str):
        """Async DB initializer"""

    @classmethod
    @abstractmethod
    async def create_tmp(cls, connection: str):
        """Async DB initializer without threadpool (for one-shot connections without access to global connection"""

    @abstractmethod
    async def create_user(self, user_id: int, username: str):
        """Creates telegram_id-username connection"""

    @abstractmethod
    async def create_key(self, user_id: int, secret: str):
        """Records a secret for given telegram_id"""

    @abstractmethod
    async def is_registered(self, user_id: int):
        """Checks whether user is already registered"""

    @abstractmethod
    async def contains(self, username: str):
        """Checks whether given username is already taken"""

    @abstractmethod
    async def update_key(self, user_id: int, secret: str):
        """Updates a secret for given telegram_id"""

    @abstractmethod
    async def get_username(self, user_id: int):
        """Gets username by telegram_id"""

    @abstractmethod
    async def get_secret(self, user_id: int):
        """Gets publickey by telegram_id"""

    @abstractmethod
    async def set_task(self, user_id: int, task_name: str):
        """Set current task of a user"""

    @abstractmethod
    async def get_tasks(self):
        """Get all task names"""

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
        return self

    @classmethod
    async def create_tmp(cls, connection: str):
        self = RedisDB()
        self.conn = await aioredis.create_connection(connection)
        return self

    async def create_user(self, user_id: int, username: str):
        await self.conn.execute("set", f"user:{user_id}", username)
        await self.conn.execute("sadd", "telegram_ids", user_id)
        await self.conn.execute("sadd", "usernames", username)
        await self.conn.execute("set", f"username:{username}", str(user_id))

    async def create_key(self, user_id: int, secret: str):
        await self.conn.execute("set", f"secrets:{user_id}", secret)

    async def is_registered(self, user_id: int):
        return bool(await self.conn.execute("sismember", "telegram_ids", user_id))

    async def contains(self, username: str):
        return bool(await self.conn.execute("sismember", "usernames", username))

    async def update_key(self, user_id: int, secret: str):
        await self.create_key(user_id, secret)

    async def get_username(self, user_id: int):
        return await self.conn.execute("get", f"user:{user_id}")

    async def get_secret(self, user_id: int):
        return await self.conn.execute("get", f"secrets:{user_id}")

    async def del_image(self, image_name: str):
        await self.conn.execute("srem", "images_set", image_name)

    async def add_image(self, image_name: str):
        await self.conn.execute("sadd", "images_set", image_name)

    async def get_images(self):
        images = await self.conn.execute("smembers", "images_set")
        images = [image.decode() for image in images]
        return images

    async def contains_image(self, imagename: str):
        return bool(await self.conn.execute("sismember", "images_set", imagename))

    async def set_image(self, user_id: int, imagename: str):
        await self.conn.execute("set", f"images:{user_id}", imagename)

    async def close(self):
        """Closes connection to redis"""
        self.conn.close()
        await self.conn.wait_closed()
