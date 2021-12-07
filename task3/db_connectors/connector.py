"""Abstract class for methods description
of connectors to database"""

from abc import ABC, abstractmethod


class Connector(ABC):

    def __init__(self, hostname, port):
        self._hostname = hostname
        self._port = port

    @abstractmethod
    def insert_one(self, *args, **kwargs):
        """Insert data"""
        pass

    @abstractmethod
    def delete_one(self, *args, **kwargs):
        """Delete data"""
        pass

    @abstractmethod
    def update_one(self, *args, **kwargs):
        """Update data"""
        pass

    @abstractmethod
    def find_all(self, *args, **kwargs):
        """Get all data"""
        pass

    @abstractmethod
    def find_one(self, *args, **kwargs):
        """Get single data"""
        pass
