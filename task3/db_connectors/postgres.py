import psycopg2
import psycopg2.extensions
from typing import Union, List


class PostgreService:
    """Connect and process requests to the PostgreSQL database """

    def __init__(self):
        self.hostname = "127.0.0.1"
        self.port = "5432"
        self.connection = None

    def create_connection(
            self, db_user: str,
            db_password: str) -> psycopg2.extensions.connection:
        """Create connection to PostgreSQL"""
        try:
            self.connection = psycopg2.connect(user=db_user,
                                               password=db_password)
        except psycopg2.OperationalError:
            pass
        else:
            return self.connection

    def create_connection_to_db(
            self, db_name: str, db_user: str,
            db_password: str) -> psycopg2.extensions.connection:
        """Create connection to PostgreSQL database """
        try:
            self.connection = psycopg2.connect(database=db_name, user=db_user,
                                               password=db_password)
        except psycopg2.OperationalError:
            pass
        else:
            return self.connection

    def reset_connections(self, search_condition: dict) -> None:
        """Reset active connections from the database"""
        insert_query = (f"SELECT pg_terminate_backend( pid ) "
                        f"FROM pg_stat_activity WHERE pid <>"
                        f"pg_backend_pid( ) AND datname = %(db_name)s")
        self.execute_query(insert_query, search_condition)

    def get_tables(self) -> list:
        """Get tables from the database

        Return list of tables in tuple format.
        """
        insert_query = ("SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema NOT IN "
                        "('information_schema','pg_catalog')")
        return self.execute_read_query(insert_query)

    def clean_table(self, table) -> None:
        """Clean table in database"""
        insert_query = f"TRUNCATE {table} CASCADE"
        self.execute_query(insert_query)

    def execute_query(self, query: str,
                      data: Union[dict, list] = None) -> None:
        """Execute send data query to the database"""
        self.connection.autocommit = True
        cursor = self.connection.cursor()
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        cursor.close()

    def execute_read_query(self, query: str,
                           search_condition: Union[dict, list] = None) -> list:
        """Execute read data query to the database

        Return list of values in tuple format.
        """
        cursor = self.connection.cursor()
        if search_condition:
            cursor.execute(query, search_condition)
        else:
            cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result

    def execute_read_query_unique_data(
            self, query: str, search_condition: Union[dict, list] = None
            ) -> Union[list, tuple, str]:
        """Execute read unique data query to the database

        Return values in tuple format if it was found.
        Return empty list if it was not found.
        Return "DATA NOT UNIQUE" if multiple unique values were found ->
        (!!!NECESSARY TO CHECK THE DATABASE!!!)
        """
        cursor = self.connection.cursor()
        cursor.execute(query, search_condition)
        result = cursor.fetchall()
        if len(result) == 1:
            result = result[0]
        elif len(result) > 0:
            result = "DATA NOT UNIQUE"
        cursor.close()
        return result

    def insert_one(self, table: str,
                   fields: Union[tuple, list], data: tuple) -> None:
        """Insert record into table"""
        fields_records = ", ".join(fields)
        insert_query = (f"INSERT INTO {table} "
                        f"({fields_records}) VALUES {data}")
        self.execute_query(insert_query)

    def delete(self, table: str, column: str, search_condition: dict) -> None:
        """Delete record from table by filter"""
        insert_query = f"DELETE FROM {table} WHERE {column} = %(value)s"
        self.execute_query(insert_query, search_condition)

    def update(self, table: str, fields: Union[tuple, list], column: str,
               search_condition: list) -> None:
        """Update record fields in table by filter"""
        fields_records = ", ".join(fields)
        data_records = ", ".join(["%s"] * len(fields))
        insert_query = (f"UPDATE {table} "
                        f"SET ({fields_records}) = ({data_records}) "
                        f"WHERE {column} = %s")
        self.execute_query(insert_query, search_condition)

    def find_all(self, table: str) -> List[tuple]:
        """Get all values from table

        Return list of values in tuple format.
        """
        insert_query = f"SELECT * FROM {table}"
        return self.execute_read_query(insert_query)

    def find_unique_data(self, table: str,
                         column: str,
                         search_condition: dict) -> Union[list, tuple, str]:
        """Get unique data from table by filter

        Return values in tuple format if it was found.
        Return empty list if it was not found.
        Return "DATA NOT UNIQUE" if multiple unique values were found ->
        (!!!NECESSARY TO CHECK THE DATABASE!!!)
        """
        insert_query = f"SELECT * FROM {table} WHERE {column} = %(value)s"
        return self.execute_read_query_unique_data(insert_query,
                                                   search_condition)
