import psycopg2
import psycopg2.extensions
from typing import Union, List

from db_connectors.connector import Connector


class PostgreService(Connector):
    """Connect and process requests to the PostgreSQL database """

    def __init__(self, hostname, port):
        super(PostgreService, self).__init__(hostname, port)
        self._connection = None

    def create_connection(self, user: str,
                          password: str) -> psycopg2.extensions.connection:
        """Create connection to PostgreSQL

        "user" - user name registered in Postgres
        "password" - user password
        Return connection to PostgreSQL (psycopg2.extensions.connection
        class instance).
        """
        try:
            self._connection = psycopg2.connect(user=user,
                                                password=password)
        except psycopg2.OperationalError:
            pass
        else:
            return self._connection

    def create_connection_to_db(self, db_name: str, user: str,
                                password: str) -> psycopg2.extensions.connection:
        """Create connection to PostgreSQL database

        "db_name" - database name
        "user" - user name registered in Postgres
        "password" - user password
        Return connection to database (psycopg2.extensions.connection
        class instance).
        """
        try:
            self._connection = psycopg2.connect(database=db_name, user=user,
                                                password=password)
        except psycopg2.OperationalError:
            pass
        else:
            return self._connection

    def reset_connections(self, search_condition: dict) -> None:
        """Reset active connections from the database

        "search_condition" - database name
        """
        insert_query = (f"SELECT pg_terminate_backend( pid ) "
                        f"FROM pg_stat_activity WHERE pid <>"
                        f"pg_backend_pid( ) AND datname = %(db_name)s")
        self.execute_query(insert_query, search_condition)

    def clean_table(self, table) -> None:
        """Clean table in database

        "table" - table name
        """
        insert_query = f"TRUNCATE {table} CASCADE"
        self.execute_query(insert_query)

    def execute_query(self, query: str,
                      parameters: Union[dict, list] = None) -> None:
        """Execute send data query to the database

        "query" - data change query
        "parameters" - additional query parameters
        """
        self._connection.autocommit = True
        with self._connection.cursor() as cursor:
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)

    def execute_read_query(self, query: str,
                           parameters: Union[dict, list] = None) -> List[tuple]:
        """Execute read data query to the database

        "query" - data read query
        "parameters" - additional query parameters
        Return list of values in tuple format.
        """
        with self._connection.cursor() as cursor:
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            return result

    def execute_read_query_unique_data(self, query: str,
            parameters: Union[dict, list] = None) -> Union[list, tuple, str]:
        """Execute read unique data query to the database

        "query" - unique data read query
        "parameters" - additional query parameters
        Return values in tuple format if it was found.
        Return empty list if it was not found.
        Return "DATA NOT UNIQUE" if multiple unique values were found ->
        (!!!NECESSARY TO CHECK THE DATABASE!!!)
        """
        with self._connection.cursor() as cursor:
            cursor.execute(query, parameters)
            result = cursor.fetchall()
            if len(result) == 1:
                result = result[0]
            elif len(result) > 0:
                result = "DATA NOT UNIQUE"
            return result

    def insert_one(self, table: str,
                   fields: Union[tuple, list], data: tuple) -> None:
        """Insert record into table

        "table" - table name
        "fields" - column names
        "data" - row values
        """
        column_names = ", ".join(fields)
        insert_query = f"INSERT INTO {table} ({column_names}) VALUES {data}"
        self.execute_query(insert_query)

    def delete_one(self, table: str, column: str,
                   search_value: dict) -> None:
        """Delete record from table by filter

        "table" - table name
        "column" - column name
        "search_condition" - column value
        """
        insert_query = f"DELETE FROM {table} WHERE {column} = %(value)s"
        self.execute_query(insert_query, search_value)

    def update_one(self, table: str, fields: Union[tuple, list], column: str,
                   substitution_values: list) -> None:
        """Update record fields in table by filter

        "table" - table name
        "fields" - column names
        "column" - column name
        "substitution_values" - row values for update and column value
        """
        column_names = ", ".join(fields)
        data = ", ".join(["%s"] * len(fields))
        insert_query = (f"UPDATE {table} "
                        f"SET ({column_names}) = ({data}) "
                        f"WHERE {column} = %s")
        self.execute_query(insert_query, substitution_values)

    def find_all(self, table: str) -> List[tuple]:
        """Get all values from table

        "table" - table name
        Return list of values in tuple format.
        """
        insert_query = f"SELECT * FROM {table}"
        return self.execute_read_query(insert_query)

    def find_one(self, table: str, column: str,
                 search_condition: dict) -> Union[list, tuple, str]:
        """Get unique data from table by filter

        "table" - table name
        "column" - column name
        "search_condition" - column value
        Return values in tuple format if it was found.
        Return empty list if it was not found.
        Return "DATA NOT UNIQUE" if multiple unique values were found ->
        (!!!NECESSARY TO CHECK THE DATABASE!!!)
        """
        insert_query = f"SELECT * FROM {table} WHERE {column} = %(value)s"
        return self.execute_read_query_unique_data(insert_query,
                                                   search_condition)
