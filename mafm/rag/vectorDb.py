import ast

from pymilvus import (
    MilvusClient,
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
)
from .embedding import embedding
import gc

from .sqlite import get_path_by_id

# MilvusClient 전역 클라이언트 객체 생성
client_cache = {}


def initialize_vector_db(db_name):
    global client_cache

    # 이미 연결된 클라이언트가 있다면 재사용
    if db_name in client_cache:
        print(f"Reusing existing client for {db_name}")
        return client_cache[db_name]

    try:
        # Milvus에 연결
        client = MilvusClient(db_name)
        client_cache[db_name] = client  # 클라이언트를 캐시에 저장

        print(f"Connected to {db_name}")

        # 컬렉션 스키마 정의 => RDB의 테이블과 비슷한 개념
        if client.has_collection(collection_name="demo_collection"):
            client.drop_collection(collection_name="demo_collection")

        client.create_collection(
            collection_name="demo_collection",
            dimension=384,  # stella는 1024 스노우플레이크는 384
        )

        return client

    except Exception as e:
        print(f"Error initializing vector DB for {db_name}: {e}")
        return None

def delete_vector_db(db_name):
    global client_cache

    # 캐시에서 클라이언트를 가져옴
    if db_name not in client_cache:
        print(f"Client for {db_name} does not exist.")
        return

    client = client_cache[db_name]

    # 컬렉션이 존재하는지 확인
    if client.has_collection(collection_name="demo_collection"):
        try:
            # 컬렉션 삭제
            client.drop_collection(collection_name="demo_collection")
            print(f"Collection 'demo_collection' in {db_name} has been deleted.")
            # 캐시에서도 클라이언트를 제거
            del client_cache[db_name]
        except Exception as e:
            print(f"Error deleting collection in {db_name}: {e}")
    else:
        print(f"Collection 'demo_collection' does not exist in {db_name}")


def save(db_name, id, queries):
    global client_cache

    # 캐시에서 클라이언트를 가져옴
    if db_name not in client_cache:
        print(f"Client for {db_name} does not exist.")
        return

    client = client_cache[db_name]

    # 컬렉션이 존재하는지 확인
    if not client.has_collection(collection_name="demo_collection"):
        print(f"Collection 'demo_collection' does not exist in {db_name}")
        return

    try:
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
        print()

        # 임베딩 값 삭제 후 가비지 컬렉션 호출
        del query_embeddings
        del data
        gc.collect()

    except MemoryError as me:
        print(f"MemoryError: {me}")

    except ValueError as ve:
        print(f"ValueError: {ve}")

    except Exception as e:
        print(f"Error occurred during saving data to Milvus: {e}")


def insert_file_embedding(file_data, db_name):
    global client_cache
    if db_name not in client_cache:
        print(f"Client for {db_name} does not exist.")
        return

    client = client_cache[db_name]
    if not client.has_collection(collection_name="demo_collection"):
        print(f"Collection 'demo_collection' does not exist in {db_name}")
        return

    try:
        # 데이터 삽입
        res = client.insert(collection_name="demo_collection", data=file_data)

    except MemoryError as me:
        print(f"MemoryError: {me}")

    except ValueError as ve:
        print(f"ValueError: {ve}")

    except Exception as e:
        print(f"Error occurred during saving data to Milvus: {e}")


# input: query들의 리스트임에 유의!!
# Output: input의 query와 가장 가까운 2개의 파일 경로
def search(db_name, query_list):

    global client_cache

    # 캐시에서 클라이언트를 가져옴
    if db_name not in client_cache:
        print(f"Client for {db_name} does not exist.")
        return

    client = client_cache[db_name]

    # 컬렉션이 존재하는지 확인
    if not client.has_collection(collection_name="demo_collection"):
        print(f"Collection 'demo_collection' does not exist in {db_name}")
        return

    query_vectors = embedding(query_list)  # query_vectors는 2차원 배열이어야 함

    res = client.search(
        collection_name="demo_collection",
        data=query_vectors,
        limit=2,
        output_fields=["id"],
    )

    print(res)

    # milvus search 를 수행한 결과에서 id값들만 가져옴
    id_list = [item["id"] for item in res[0]]

    # 해당 id 값을 토대로 file_path를 검색
    # milvus db 자체에 file_path를 저장하지 않는 이유는 파일 수정, 삭제등을 용이하게 만들기 위해서
    path_list = [get_path_by_id(id, "filesystem.db") for id in id_list]

    print(path_list)
    return path_list


def find_by_id(search_id, db_name):
    global client_cache

    # Check if client exists in the cache
    if db_name not in client_cache:
        print(f"Client for {db_name} does not exist.")
        return

    client = client_cache[db_name]

    collection_name = "demo_collection"

    # Check if the collection exists using the client
    if not client.has_collection(collection_name):
        print(f"Collection '{collection_name}' does not exist in {db_name}")
        return

    # Perform the query directly using the client
    res = client.query(collection_name=collection_name, filter=f"id in [{search_id}]")

    if not res:
        print(f"No results found for ID: {search_id}")
        return

    return res


def remove_by_id(remove_id, db_name):
    global client_cache

    if db_name not in client_cache:
        raise Exception(f"Client for {db_name} does not exist.")

    client = client_cache[db_name]

    collection_name = "demo_collection"
    if not client.has_collection(collection_name):
        raise Exception(f"Collection '{collection_name}' does not exist in {db_name}")

    res = client.delete(collection_name=collection_name, filter=f"id in [{remove_id}]")

    print(f"Deleted records with ID: {remove_id}")
    return res
