import pytest
import redis

# bot libraries, are accessible by setting PYTHONPATH
from db import RedisDB
from config import DB_CONN

@pytest.fixture
def clean_redis():
    """Initializes database for testing purposes"""
    rdb = redis.Redis(host='redis', port=6379, db=0)
    rdb.flushdb()

@pytest.fixture
async def create_user():
    """Creates new user for testing purposes"""
    rdb = await RedisDB.create(DB_CONN)
    username = "testing"
    user_id = "228"
    password = "qwerty"

    await rdb.create_user(user_id, username)
    await rdb.create_key(user_id, password)

    await rdb.close()

@pytest.fixture
async def create_user_set_image():
    """Creates new user, sets an image for him"""
    rdb = await RedisDB.create(DB_CONN)

    username = "testing"
    user_id = "228"
    password = "qwerty"
    imagename = "dummy"

    await rdb.create_user(user_id, username)
    await rdb.create_key(user_id, password)

    await rdb.add_image(imagename)
    await rdb.set_image(user_id, imagename)
