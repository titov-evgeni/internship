import psycopg2.extensions

import db_connectors.postgres
from config import user, password
import postgres_create_tables as tables


def postgresql_create_connection_to_db(
        postgres: db_connectors.postgres.PostgreService,
        db: str) -> psycopg2.extensions.connection:
    """Connect to PostgreSQL and connect to database.

    If there is no database, create it and connect.
    Return connection to database.
    """
    connection_to_db = postgres.create_connection_to_db(db, user, password)
    if connection_to_db:
        postgres.reset_connections({"db_name": db})
    else:
        postgres.create_connection(user, password)
        create_database_query = f"CREATE DATABASE {db}"
        postgres.execute_query(create_database_query)
        connection_to_db = postgres.create_connection_to_db(db, user, password)
        # Create tables in database
        tables.create_tables_postgresql(postgres)
    return connection_to_db
