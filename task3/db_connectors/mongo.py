from pymongo import MongoClient, database, collection
from typing import List, Union

from db_connectors.connector import Connector


class MongodbService(Connector):

    def __init__(self, hostname, port):
        super(MongodbService, self).__init__(hostname, port)
        self._client = MongoClient(self._hostname, self._port)

    def create_db(self, db_name: str) -> database.Database:
        """Create data base for MongoClient

        "db_name" - database name
        Return pymongo.database.Database class instance
        """
        return self._client[db_name]

    def drop_db(self, db_name: str) -> None:
        """Delete data base

        "db_name" - database name
        """
        self._client.drop_database(db_name)

    @staticmethod
    def create_collection(db_name: database.Database,
                          collection_name: str) -> collection.Collection:
        """Create collection in data base

        "db_name" - pymongo.database.Database class instance
        "collection_name" - collection name
        Return pymongo.collection.Collection class instance
        """
        return db_name[collection_name]

    def insert_one(self, collection_name: collection.Collection,
                   data: dict) -> None:
        """Insert document into collection

        "collection_name" - pymongo.collection.Collection class instance
        "data" - data to insert into collection
        """
        collection_name.insert_one(data)

    def delete_one(self, collection_name: collection.Collection,
                   search_filter: dict) -> None:
        """Delete document from collection by filter

        "collection_name" - pymongo.collection.Collection class instance
        "search_filter" - filter to find document in the collection
        """
        collection_name.delete_one(search_filter)

    def update_one(self, collection_name: collection.Collection,
                   search_filter: dict, new_values: dict) -> None:
        """Update document fields in collection by filter

        "collection_name" - pymongo.collection.Collection class instance
        "search_filter" - filter to find document in the collection
        "new_values" - data to update in document
        """
        collection_name.update_one(search_filter, {'$set': new_values})

    def find_all(self, collection_name: collection.Collection) -> List[dict]:
        """Get all documents from collection

        "collection_name" - pymongo.collection.Collection class instance
        Return list of documents from collection in dict format.
        """
        return list(collection_name.find())

    def find_one(self, collection_name: collection.Collection,
                 search_filter: dict, *args) -> Union[dict, str, None]:
        """Get single document from collection by filter

        "collection_name" - pymongo.collection.Collection class instance
        "search_filter" - filter to find document in the collection
        "*args" - additional parameters for output from document
        Return document from collection by filter in dict format if
        it was found.
        Return "None" if document was not found.
        Return str "No connection" if there is no connection
        to database server.
        """
        try:
            document = collection_name.find_one(search_filter, *args)
            return document
        except Exception:
            return "No connection"
