import ast
import gc
import os
from pymilvus import (
    MilvusClient,
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
)
from .embedding import embedding
from .sqlite import get_path_by_id


def delete_db_lock_file(db_name):
    dir_path = os.path.dirname(db_name)
    base_name = os.path.basename(db_name)

    lock_file = f"{dir_path}/.{base_name}.lock"
    if os.path.exists(lock_file):
        os.remove(lock_file)
    else:
        print(f"No lock file found for {lock_file}")


def initialize_vector_db(db_name):
    client = None
    try:
        # Milvus에 연결
        client = MilvusClient(db_name)
        print(f"Connected to {db_name}")

        # 컬렉션 스키마 정의 => RDB의 테이블과 비슷한 개념
        if client.has_collection(collection_name="demo_collection"):
            client.drop_collection(collection_name="demo_collection")

        client.create_collection(
            collection_name="demo_collection",
            dimension=384,  #  384 Adjust dimension as needed
        )
    except Exception as e:
        print(f"Error initializing vector DB for {db_name}: {e}")
    finally:
        if client is not None:
            client.close()
        gc.collect()
        delete_db_lock_file(db_name)


def delete_vector_db(db_name):
    try:
        client = MilvusClient(db_name)
        if client.has_collection(collection_name="demo_collection"):
            client.drop_collection(collection_name="demo_collection")
            print(f"Collection 'demo_collection' in {db_name} has been deleted.")
        else:
            print(f"Collection 'demo_collection' does not exist in {db_name}")
    except Exception as e:
        print(f"Error deleting collection in {db_name}: {e}")
    finally:
        client.close()
        gc.collect()
        delete_db_lock_file(db_name)


def save(db_name, id, queries):
    try:
        client = MilvusClient(db_name)
        if not client.has_collection(collection_name="demo_collection"):
            print(f"Collection 'demo_collection' does not exist in {db_name}")
            return

        # 쿼리 임베딩
        query_embeddings = embedding(queries)

        # 임베딩 데이터 저장
        data = [
            {"id": id, "vector": query_embeddings[i], "word": queries[i]}
            for i in range(len(query_embeddings))
        ]

        # 데이터 삽입
        res = client.insert(collection_name="demo_collection", data=data)
        print(res)

    except MemoryError as me:
        print(f"MemoryError: {me}")
    except ValueError as ve:
        print(f"ValueError: {ve}")
    except Exception as e:
        print(f"Error occurred during saving data to Milvus: {e}")
    finally:
        client.close()
        gc.collect()
        delete_db_lock_file(db_name)


def insert_file_embedding(file_data, db_name):
    try:
        client = MilvusClient(db_name)
        if not client.has_collection(collection_name="demo_collection"):
            print(f"Collection 'demo_collection' does not exist in {db_name}")
            return

        # 데이터 삽입
        res = client.insert(collection_name="demo_collection", data=file_data)

    except MemoryError as me:
        print(f"MemoryError: {me}")
    except ValueError as ve:
        print(f"ValueError: {ve}")
    except Exception as e:
        print(f"Error occurred during saving data to Milvus: {e}")
    finally:
        client.close()
        gc.collect()
        delete_db_lock_file(db_name)


def search(db_name, query_list):
    try:
        client = MilvusClient(db_name)
        if not client.has_collection(collection_name="demo_collection"):
            print(f"Collection 'demo_collection' does not exist in {db_name}")
            return

        query_vectors = embedding(query_list)

        res = client.search(
            collection_name="demo_collection",
            data=query_vectors,
            limit=2,
        )
        id_list = [item["id"] for item in res[0]]
        path_list = [get_path_by_id(id, "filesystem.db") for id in id_list]
        return path_list
    finally:
        client.close()
        gc.collect()
        delete_db_lock_file(db_name)


def find_by_id(search_id, db_name):
    try:
        client = MilvusClient(db_name)
        collection_name = "demo_collection"

        if not client.has_collection(collection_name):
            print(f"Collection '{collection_name}' does not exist in {db_name}")
            return

        res = client.query(
            collection_name=collection_name, filter=f"id in [{search_id}]"
        )

        if not res:
            print(f"No results found for ID: {search_id}")
            return
        return res
    finally:
        client.close()
        gc.collect()
        delete_db_lock_file(db_name)


def remove_by_id(remove_id, db_name):
    try:
        client = MilvusClient(db_name)
        collection_name = "demo_collection"
        if not client.has_collection(collection_name):
            raise Exception(
                f"Collection '{collection_name}' does not exist in {db_name}"
            )

        res = client.delete(
            collection_name=collection_name, filter=f"id in [{remove_id}]"
        )

        print(f"Deleted records with ID: {remove_id}")
        return res
    finally:
        client.close()
        gc.collect()
        delete_db_lock_file(db_name)
