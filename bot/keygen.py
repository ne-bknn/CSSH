from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

from concurrent.futures import ProcessPoolExecutor
import asyncio

class KeyGenerator:
    def __init__(self):
        self.executor = ProcessPoolExecutor(10)

    async def _in_thread(self, func):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func)
    
    @staticmethod
    def _generate():
        key = rsa.generate_private_key(
            backend=crypto_default_backend(),
            public_exponent=65537,
            key_size=4096
        )

        private_key = key.private_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PrivateFormat.PKCS8,
            crypto_serialization.NoEncryption()
        )

        public_key = key.public_key().public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH
        )

        return private_key, public_key

    async def generate(self):
        private_key, public_key = await asyncio.gather(self._in_thread(self._generate))
        return private_key, public_key
