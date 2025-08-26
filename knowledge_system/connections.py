from dotenv import load_dotenv
from qdrant_client import QdrantClient
import os
class Connection:
    def __init__(self):
        load_dotenv()
        qdrant_host = os.getenv("QDRANT_HOST", "127.0.0.1")
        qdrant_port = os.getenv("QDRANT_PORT", 6333)
        self.qdrant_client = QdrantClient(qdrant_host, port = int(qdrant_port))

    def qdrant_connection(self):
        return self.qdrant_client