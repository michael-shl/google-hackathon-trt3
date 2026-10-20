import os

from google.cloud import bigquery

_client = None

_SCALAR_TYPES = {bool: "BOOL", int: "INT64", float: "FLOAT64", str: "STRING"}


def _param(name, value):
    if isinstance(value, (list, tuple)):
        elem_type = _SCALAR_TYPES[type(value[0])] if value else "STRING"
        return bigquery.ArrayQueryParameter(name, elem_type, list(value))
    return bigquery.ScalarQueryParameter(name, _SCALAR_TYPES[type(value)], value)


def run(sql: str, **params) -> list[dict]:
    """Runs a parameterized query (use @name in SQL) and returns rows as dicts.

    query_and_wait uses the jobs.query fast path (no job polling for small results).
    """
    global _client
    if _client is None:
        _client = bigquery.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
    job_config = bigquery.QueryJobConfig(query_parameters=[_param(k, v) for k, v in params.items()])
    return [dict(row) for row in _client.query_and_wait(sql, job_config=job_config)]
