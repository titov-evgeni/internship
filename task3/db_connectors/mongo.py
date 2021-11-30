from pymongo import MongoClient, database, collection
from typing import List, Union


class MongodbService(object):

    def __init__(self, hostname, port):
        self._hostname = hostname
        self._port = port
        self._client = MongoClient(self._hostname, self._port)

    def create_db(self, db_name: str) -> database.Database:
        """Create data base for MongoClient

        "db_name" - database name
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

        "db_name" - database name
        "collection_name" - collection name
        """
        return db_name[collection_name]

    @staticmethod
    def insert_one(collection_name: collection.Collection, data: dict) -> None:
        """Insert document into collection

        "collection_name" - collection name
        "data" - data to insert into collection
        """
        collection_name.insert_one(data)

    @staticmethod
    def delete_one(collection_name: collection.Collection,
                   search_filter: dict) -> None:
        """Delete document from collection by filter

        "collection_name" - collection name
        "search_filter" - filter to find document in the collection
        """
        collection_name.delete_one(search_filter)

    @staticmethod
    def update_one(collection_name: collection.Collection,
                   search_filter: dict, new_values: dict) -> None:
        """Update document fields in collection by filter

        "collection_name" - collection name
        "search_filter" - filter to find document in the collection
        "new_values" - data to update in document
        """
        collection_name.update_one(search_filter, {'$set': new_values})

    @staticmethod
    def find(collection_name: collection.Collection) -> List[dict]:
        """Get all documents from collection

        "collection_name" - collection name
        Return list of documents.
        """
        return list(collection_name.find())

    @staticmethod
    def find_one(collection_name: collection.Collection,
                 search_filter: dict, *args) -> Union[dict, str]:
        """Get single document from collection by filter

        "collection_name" - collection name
        "search_filter" - filter to find document in the collection
        "*args" - additional parameters for output from document
        """
        try:
            document = collection_name.find_one(search_filter, *args)
            return document
        except Exception:
            return "No connection"
