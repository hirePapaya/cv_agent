import logging
import os

import boto3
from boto3.resources.base import ServiceResource
from botocore.client import BaseClient

logger = logging.getLogger(__name__)

# Local dev default points to the docker-compose mapped port.
# Override via DYNAMODB_ENDPOINT env var when running inside docker
# (set to http://dynamodb-local:8000) or against real AWS (leave unset).
_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8001")
_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

# DynamoDB Local ignores credentials but boto3 requires non-empty values.
_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "local")
_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "local")

_KWARGS = dict(
    region_name=_REGION,
    aws_access_key_id=_ACCESS_KEY,
    aws_secret_access_key=_SECRET_KEY,
    endpoint_url=_ENDPOINT,
)

logger.info("DynamoDB endpoint: %s", _ENDPOINT)


def get_resource() -> ServiceResource:
    """Return a high-level DynamoDB resource (Table objects, etc.)."""
    return boto3.resource("dynamodb", **_KWARGS)


def get_client() -> BaseClient:
    """Return a low-level DynamoDB client (for raw API calls)."""
    return boto3.client("dynamodb", **_KWARGS)
