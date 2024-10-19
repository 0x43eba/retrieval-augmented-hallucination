import sqlite3
import hashlib

class FileMetadataCache:
    def __init__(self, cache_path):
        self.cache_path = cache_path
        self.connection = sqlite3.connect(cache_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, filename TEXT)")
    
    def get(self, key) -> str:
        self.cursor.execute("SELECT filename FROM cache WHERE key=?", (key,))
        result = self.cursor.fetchone()
        if result is None:
            return None
        return result[0]
    
    def set(self, key, filename) -> None:
        self.cursor.execute("INSERT OR REPLACE INTO cache (key, filename) VALUES (?, ?)", (key, filename))
        self.connection.commit()
    
    def exists(self, key) -> bool:
        return self.get(key) is not None
    
    def sha456_key(self, filename: str, file_path: str) -> str:
        return hashlib.sha256(f'{filename}-{file_path}'.encode()).hexdigest()
    