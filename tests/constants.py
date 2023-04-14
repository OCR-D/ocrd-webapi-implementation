__all__ = [
    'MONGO_TESTDB'
]

# This value has to match exactly with the value inside pyproject.toml
# -> OCRD_WEBAPI_DB_URL = mongodb://localhost:6701/test-ocrd-webapi
MONGO_TESTDB: str = "test-ocrd-webapi"
