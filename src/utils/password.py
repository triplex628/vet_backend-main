# пока без хеширования
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return plain_password == hashed_password


def get_password_hash(plain_password: str) -> str:
    return plain_password
