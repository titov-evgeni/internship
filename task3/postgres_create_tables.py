import db_connectors.postgres as connector


def create_tables_postgresql(postgres: connector.PostgreService) -> None:
    """Create tables in database

    "postgres" - PostgreService class instance
    """

    users_table = """
        CREATE TABLE IF NOT EXISTS users (
          id SERIAL PRIMARY KEY,
          user_name VARCHAR(50) NOT NULL UNIQUE,
          user_karma INT NOT NULL,
          user_cake_day VARCHAR(20) NOT NULL,
          post_karma INT NOT NULL,
          comment_karma INT NOT NULL
        )
        """
    postgres.execute_query(users_table)

    posts_table = """
        CREATE TABLE IF NOT EXISTS posts (
          id VARCHAR(50) NOT NULL UNIQUE,
          post_url TEXT NOT NULL,
          post_date VARCHAR(20) NOT NULL,
          number_of_comments INT NOT NULL,
          number_of_votes INT NOT NULL,
          post_category VARCHAR(50) NOT NULL,
          user_id INTEGER REFERENCES users(id)
        )
        """
    postgres.execute_query(posts_table)
