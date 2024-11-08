from dotenv import load_dotenv
import os

load_dotenv()


def get_env_key(key: str):
    return os.getenv(key)
