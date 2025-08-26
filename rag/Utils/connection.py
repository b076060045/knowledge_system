from qdrant_client import QdrantClient
import dotenv
import os

class Connection:
    def __init__(self):
        self.qdrant_host = os.getenv('QDRANT_HOST', "127.0.0.1")
        self.qdrant_port = os.getenv('QDRANT_PORT', "6336")
    def qdrant_connection(self):
        return QdrantClient(self.qdrant_host, self.qdrant_port)

    