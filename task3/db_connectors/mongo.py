from pymongo import MongoClient, database, collection


class MongodbService(object):

    def __init__(self):
        self.client = MongoClient("localhost", 27017)

    def create_db(self, db_name: str):
        """Create data base for MongoClient"""
        return self.client[db_name]

    def drop_db(self, db_name: str):
        """Delete data base"""
        self.client.drop_database(db_name)

    @staticmethod
    def create_collection(db: database.Database, collection_name: str):
        """Create collection in data base"""
        return db[collection_name]

    @staticmethod
    def insert_one(collection_name: collection.Collection, data: dict):
        """Insert document into collection"""
        return collection_name.insert_one(data)

    @staticmethod
    def delete_one(collection_name: collection.Collection,
                   search_filter: dict):
        """Delete document from collection by filter"""
        return collection_name.delete_one(search_filter)

    @staticmethod
    def update_one(collection_name: collection.Collection,
                   search_filter: dict, new_values: dict):
        """Update document fields in collection by filter"""
        collection_name.update_one(search_filter, {'$set': new_values})

    @staticmethod
    def find(collection_name: collection.Collection):
        """Get all documents from collection

        Return list of documents.
        """
        return list(collection_name.find())

    @staticmethod
    def find_one(collection_name: collection.Collection,
                 search_filter: dict, *args):
        """Get single document from collection by filter

        *args - necessary fields for output from document
        """
        return collection_name.find_one(search_filter, *args)
