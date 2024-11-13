from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
)
from .embedding import embedding
import gc
from .sqlite import get_path_by_id

# Milvus 기본 호스트와 포트 설정
HOST = "localhost"
PORT = "19530"

# 고정된 컬렉션 이름
COLLECTION_NAME = "demo_collection"

def initialize_vector_db(db_name):
    try:
        # db_name을 alias로 사용하여 연결 설정
        connections.connect(alias=db_name, host=HOST, port=PORT)
        print(f"Connected to Milvus with alias '{db_name}'")

        # 컬렉션 존재 여부 확인 및 삭제 후 재생성
        if connections.get_connection(db_name).has_collection(COLLECTION_NAME):
            Collection(name=COLLECTION_NAME, using=db_name).drop()

        # 컬렉션 스키마 정의 및 생성
        schema = CollectionSchema(
            fields=[
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=384),
                FieldSchema(name="word", dtype=DataType.STRING),
            ]
        )
        Collection(name=COLLECTION_NAME, schema=schema, using=db_name)

    except Exception as e:
        print(f"Error initializing vector DB '{db_name}': {e}")
    finally:
        connections.disconnect(alias=db_name)


def delete_vector_db(db_name):
    try:
        connections.connect(alias=db_name, host=HOST, port=PORT)

        # 컬렉션이 존재하는지 확인
        if connections.get_connection(db_name).has_collection(COLLECTION_NAME):
            Collection(name=COLLECTION_NAME, using=db_name).drop()
            print(f"Collection '{COLLECTION_NAME}' in '{db_name}' has been deleted.")
        else:
            print(f"Collection '{COLLECTION_NAME}' does not exist in '{db_name}'")
    except Exception as e:
        print(f"Error deleting collection in '{db_name}': {e}")
    finally:
        connections.disconnect(alias=db_name)


def save(db_name, id, queries):
    try:
        connections.connect(alias=db_name, host=HOST, port=PORT)

        # 컬렉션 존재 여부 확인
        if not connections.get_connection(db_name).has_collection(COLLECTION_NAME):
            print(f"Collection '{COLLECTION_NAME}' does not exist in '{db_name}'")
            return

        # 쿼리 임베딩
        query_embeddings = embedding(queries)

        # 데이터 삽입 준비
        data = [
            {"id": id, "vector": query_embeddings[i], "word": queries[i]}
            for i in range(len(query_embeddings))
        ]

        # 데이터 삽입
        collection = Collection(name=COLLECTION_NAME, using=db_name)
        collection.insert(data)
        print(f"Inserted data into '{COLLECTION_NAME}' in '{db_name}'")

        # 메모리 해제
        del query_embeddings
        del data
        gc.collect()

    except Exception as e:
        print(f"Error occurred during saving data to Milvus in '{db_name}': {e}")
    finally:
        connections.disconnect(alias=db_name)


def search(db_name, query_list):
    try:
        connections.connect(alias=db_name, host=HOST, port=PORT)

        # 컬렉션 존재 여부 확인
        if not connections.get_connection(db_name).has_collection(COLLECTION_NAME):
            print(f"Collection '{COLLECTION_NAME}' does not exist in '{db_name}'")
            return

        # 쿼리 벡터 생성
        query_vectors = embedding(query_list)

        # 검색 수행
        collection = Collection(name=COLLECTION_NAME, using=db_name)
        results = collection.search(
            data=query_vectors,
            limit=2,
            output_fields=["id"],
        )

        id_list = [item["id"] for item in results[0]]
        path_list = [get_path_by_id(id, "filesystem.db") for id in id_list]
        print(f"Search results in '{db_name}': {path_list}")
        return path_list

    except Exception as e:
        print(f"Error occurred during search in Milvus in '{db_name}': {e}")
    finally:
        connections.disconnect(alias=db_name)


def find_by_id(db_name, search_id):
    try:
        connections.connect(alias=db_name, host=HOST, port=PORT)

        # 컬렉션 존재 여부 확인
        if not connections.get_connection(db_name).has_collection(COLLECTION_NAME):
            print(f"Collection '{COLLECTION_NAME}' does not exist in '{db_name}'")
            return

        # ID로 데이터 조회
        collection = Collection(name=COLLECTION_NAME, using=db_name)
        res = collection.query(expr=f"id in [{search_id}]")
        return res

    except Exception as e:
        print(f"Error occurred during find_by_id in Milvus in '{db_name}': {e}")
    finally:
        connections.disconnect(alias=db_name)


def remove_by_id(db_name, remove_id):
    try:
        connections.connect(alias=db_name, host=HOST, port=PORT)

        # 컬렉션 존재 여부 확인
        if not connections.get_connection(db_name).has_collection(COLLECTION_NAME):
            print(f"Collection '{COLLECTION_NAME}' does not exist in '{db_name}'")
            return

        # ID로 데이터 삭제
        collection = Collection(name=COLLECTION_NAME, using=db_name)
        res = collection.delete(expr=f"id in [{remove_id}]")
        print(f"Deleted record with ID: {remove_id} in '{db_name}'")
        return res

    except Exception as e:
        print(f"Error occurred during remove_by_id in Milvus in '{db_name}': {e}")
    finally:
        connections.disconnect(alias=db_name)
