from typing import List, Optional
import logging 
import time

from core.file_reader.reader import (
    process_and_insert_embeddings, 
    convert_to_response,
    Response, 
    RagClient, 
)

import weaviate
import requests
from cache.filecache import FileMetadataCache

logging.basicConfig(level=logging.WARN)

client = weaviate.connect_to_local()
cache = FileMetadataCache("cache.db")

while not client.is_ready():
    logging.info("Waiting for database connection")
    time.sleep(1)

def embedding_function(text: str) -> List[float]:
    output = requests.post("http://localhost:1234/v1/embeddings", json={
        "input": text,
        "model": "nomic-ai/nomic-embed-text-v1.5-GGUF"
    })
    json_data = output.json()
    return json_data["data"][0]["embedding"]


def query_function(_: str, contexts: List[dict]) -> Optional[Response]:
    raw_response = requests.post("http://localhost:1234/v1/chat/completions", json={
        "model": "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "messages": contexts,
    })
    response = raw_response.json()
    return convert_to_response(response)


rag_client = RagClient(client, embedding_function=embedding_function, query_function=query_function, cache=cache)

def start():
    _, collection_names = process_and_insert_embeddings(rag_client, folder_path="data/")
    while True:
        try:
            print("\n\n")
            query = input("Enter query >>> ")
            if query == "exit":
                break
            vectors = rag_client.query_collections(
                query=query, 
                collection_names=[*collection_names], 
                certainty=0.1,
                limit=100
            )
            response = rag_client.generate_response(
                query=query,
                contexts=vectors
            )
            print("\n\n")
            print(response)
        except KeyboardInterrupt:
            break
    rag_client.close()