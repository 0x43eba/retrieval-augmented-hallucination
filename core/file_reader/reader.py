import os
import logging
from random import shuffle
from dataclasses import dataclass
from typing import Callable, List, Dict, Optional, Tuple

import weaviate.classes as wvc
from weaviate import WeaviateClient
from cache.filecache import FileMetadataCache
from core.file_reader.chunker import sliding_window_split

EmbeddingFunction = Callable[[str], List[float]]

@dataclass
class Message:
    role: str
    content: str
    
@dataclass
class Choice:
    message: Message
    
@dataclass
class Response:
    choices: List[Choice]
    
def convert_to_response(data: dict) -> Response:
    choices = []
    
    # Loop through choices in the input data
    for choice_data in data.get('choices', []):
        message_data = choice_data.get('message', {})
        message = Message(
            role=message_data.get('role', ''),
            content=message_data.get('content', '')
        )
        choices.append(Choice(message=message))
    
    # Create the Response object
    return Response(choices=choices)

QueryFunction = Callable[[str, List[Dict[str, str]]], Optional[Response]]

class EmbeddingResult:
    def __init__(self, collection_name, inserted_vectors):
        self.collection_name = collection_name
        self.inserted_vectors = inserted_vectors

    def __repr__(self):
        return f"EmbeddingResult(collection_name={self.collection_name}, inserted_vectors={len(self.inserted_vectors)})"

def de_duplicate(contexts: List[Dict[str, str]]) -> List[Dict[str, str]]:
    unique_contexts = []
    for context in contexts:
        if context not in unique_contexts:
            unique_contexts.append(context)
    return unique_contexts

class RagClient:
    def __init__(
            self, 
            vector_database: WeaviateClient, 
            embedding_function: EmbeddingFunction, 
            query_function: QueryFunction,
            cache: Optional[FileMetadataCache] = None,
        ):
        self.file_cache = cache
        self.vector_database = vector_database
        self.embedding_function = embedding_function
        self.query_function = query_function

    def query_collections(self, query: str, collection_names: List[str], certainty: float, limit: Optional[int]) -> List[Dict[str, str]]:
        embedded_query = self.embedding_function(query)
        contexts: List[Dict[str, str]] = []

        for collection_name in collection_names:
            if not self.vector_database.collections.exists(collection_name):
                logging.warning(f"Collection {collection_name} does not exist")
                continue

            collection = self.vector_database.collections.get(collection_name)
            output = None
            match limit:
                case None:
                    logging.debug(f"Querying collection {collection_name} with certainty {certainty}")
                    output = collection.query.near_vector(
                        near_vector=embedded_query,
                        certainty=certainty
                    )
                case int(limit):
                    logging.debug(f"Querying collection {collection_name} with certainty {certainty} and limit {limit}")
                    output = collection.query.near_vector(
                        near_vector=embedded_query,
                        certainty=certainty,
                        limit=limit
                    )
            if output is not None and len(output.objects) > 0:
                for ctx in output.objects:
                    contexts.append({
                        "role": "system",
                        "content": f'Context for informing user query from a collection called {collection_name}: {ctx.properties["text"]}'
                    })
        match contexts:
            case None:
                logging.debug("No contexts found")
                return []
            case list(contexts):
                match limit:
                    case None:
                        logging.debug(f"Returning all contexts")
                        return contexts
                    case int(limit):
                        logging.debug(f"Shuffling contexts and limiting to {limit}")
                        shuffle(contexts)
                        return contexts[:limit]
            

    def generate_response(self, query: str, contexts: List[Dict[str, str]]) -> str:
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant"
            },
            {
                "role": "system",
                "content": "Using the provided context, provide an answer to the user provided query."
            },
            {
                "role": "system",
                "content": "be concise, do not be verbose. Try to keep explanations to one cohesive paragraph"
            },
            *contexts,
            {
                "role": "user",
                "content": f"User Query: {query}"
            }
        ]

        response = self.query_function(query, messages)
        if response is not None:
            return response.choices[0].message.content
        return ""

    def close(self) -> None:
        self.vector_database.close()


def process_and_insert_embeddings(rag_client: RagClient, folder_path="text_samples") -> Tuple[List[EmbeddingResult], List[str]]:

    collection_names = []
    results = []

    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            logging.info(f"Processing file {filename}")
            collection_name = filename.split(".")[0]
            collection_names.append(collection_name)
            cache_key = rag_client.file_cache.sha456_key(filename, folder_path)
            if rag_client.file_cache.exists(cache_key):
                continue
            
            if not rag_client.vector_database.collections.exists(collection_name):
                collection = rag_client.vector_database.collections.create(
                    name=collection_name,
                    description="Collected documents",
                    vectorizer_config=wvc.config.Configure.Vectorizer.none(),
                )
            else:
                collection = rag_client.vector_database.collections.get(collection_name)

            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r") as file:
                text = file.read()

            text_target_array = sliding_window_split(text, 500, 50)
            inserted_vectors = []
            
            try:
                for text_chunk in text_target_array:
                    embedded_data = rag_client.embedding_function(text_chunk)
                    collection.data.insert(
                        vector=embedded_data,
                        properties={"text": text_chunk}
                    )
                    rag_client.file_cache.set(cache_key, file_path)
                    inserted_vectors.append(embedded_data)

            except Exception as e:
                logging.error(f"Error: {e}")
                break

            results.append(EmbeddingResult(collection_name, inserted_vectors))

    return results, collection_names
