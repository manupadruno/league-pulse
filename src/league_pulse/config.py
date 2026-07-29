from dotenv import load_dotenv
import os

load_dotenv()


def require_env(name):
    env_value = os.getenv(name)
    if env_value is None:
        raise ValueError(f"{name} is not set in the environment variables.")
    return env_value


API_TOKEN = require_env("FOOTBALL_DATA_API_TOKEN")
BASE_URL = require_env("FOOTBALL_DATA_BASE_URL")
POSTGRES_HOST = require_env("POSTGRES_HOST")
POSTGRES_PORT = require_env("POSTGRES_PORT")
POSTGRES_USER = require_env("POSTGRES_USER")
POSTGRES_PASSWORD = require_env("POSTGRES_PASSWORD")
POSTGRES_DB = require_env("POSTGRES_DB")
