from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

pwd_context = PasswordHash((Argon2Hasher(),))


class Hasher:
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Retrieve the hashed password to store in the database.

        :param password: unhashed password (we don't store it anywhere)
        :return: Argon2id-hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def is_valid_password(plain_password: str, hashed_password: str) -> bool:
        """
        Compare the given raw password with the hashed password.
        Returns True if it's the same, False otherwise.

        :param plain_password: raw password
        :param hashed_password: password hash produced by hash_password()
        :return: True if it's the same, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
