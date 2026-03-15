"""Database service catalog — auto-imports all database service definitions."""

from __future__ import annotations

from pyworkspace.catalog.databases.cassandra import CassandraService
from pyworkspace.catalog.databases.clickhouse import ClickHouseService
from pyworkspace.catalog.databases.elasticsearch import ElasticsearchService
from pyworkspace.catalog.databases.mongodb import MongoDBService
from pyworkspace.catalog.databases.mysql import MySQLService
from pyworkspace.catalog.databases.neo4j import Neo4jService
from pyworkspace.catalog.databases.postgres import PostgresService
from pyworkspace.catalog.databases.redis_db import RedisService
from pyworkspace.catalog.databases.sqlite import SQLiteService

__all__ = [
    "CassandraService",
    "ClickHouseService",
    "ElasticsearchService",
    "MongoDBService",
    "MySQLService",
    "Neo4jService",
    "PostgresService",
    "RedisService",
    "SQLiteService",
]
