from pymilvus import MilvusClient, connections, Collection, FieldSchema, CollectionSchema, DataType
from embedding import embedding


collection = None

def initialize_vector_db(db_name):
    # Milvus에 연결
    client = MilvusClient(db_name)

    print(f"Connected to {db_name}")

    # 컬렉션 스키마 정의 => RDB의 테이블과 비슷한 개념
    if client.has_collection(collection_name="demo_collection"):
        client.drop_collection(collection_name="demo_collection")

    client.create_collection(
        collection_name="demo_collection",
        dimension=1024,
    )

def save(db_name, queries):
    client = MilvusClient(db_name)  # 데이터베이스 이름을 사용하여 클라이언트 생성

    if not client.has_collection(collection_name="demo_collection"):
        raise ValueError(f"Collection 'demo_collection' does not exist in {db_name}")

    query_embeddings = embedding(queries)

    # 임베딩 데이터 저장
    data = [
        {"id": i, "vector": query_embeddings[i], "word": queries[i]}
        for i in range(len(query_embeddings))
    ]

    # 데이터 삽입
    res = client.insert(collection_name="demo_collection", data=data)

    print(res)


def search(db_name, query):
    client = MilvusClient(db_name)  # 데이터베이스 이름을 사용하여 클라이언트 생성

    if not client.has_collection(collection_name="demo_collection"):
        raise ValueError(f"Collection 'demo_collection' does not exist in {db_name}")

    query_vectors = embedding(query)  # query_vectors는 2차원 배열이어야 함

    print(query_vectors)

    res = client.search(
        collection_name="demo_collection",
        data=query_vectors,
        limit=2,
        output_fields=["word"],
    )

    print(res)