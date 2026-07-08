import os
import boto3
from functools import lru_cache


@lru_cache(maxsize=1)
def get_dynamodb_resource():
    return boto3.resource("dynamodb")


@lru_cache(maxsize=1)
def get_s3_client():
    return boto3.client("s3")


def get_table(env_var: str):
    table_name = os.environ[env_var]
    return get_dynamodb_resource().Table(table_name)


def get_bucket_name(env_var: str) -> str:
    return os.environ[env_var]
