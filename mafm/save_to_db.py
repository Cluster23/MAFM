from pymilvus import MilvusClient, connections, Collection, FieldSchema, CollectionSchema, DataType
from embedding import embedding


collection = None
client = None

def connect_to_db():
    global client

    # Milvus에 연결
    client = MilvusClient("milvus_demo.db")

    # 컬렉션 스키마 정의 => RDB의 테이블과 비슷한 개념
    if client.has_collection(collection_name="demo_collection"):
        client.drop_collection(collection_name="demo_collection")

    client.create_collection(
        collection_name="demo_collection",
        dimension=1024,
    )

def save(queries):
    global client

    query_embeddings = embedding(queries)

    # 임베딩 데이터 저장
    data = [
        {"id": i, "vector": query_embeddings[i], "word": queries[i]}
        for i in range(len(query_embeddings))
    ]

    # 데이터 삽입
    res = client.insert(collection_name="demo_collection", data=data)

    print(res)


def search(query):
    global collection  # 전역 변수 사용

    query_vectors = embedding(query) # query_vectors는 2차원 배열이어야 함

    print(query_vectors)

    res = client.search(
        collection_name = "demo_collection",
        data=query_vectors,
        limit=2,
        output_fields=["word"],
    )

    print(res)


queries = [
    "banana",
    "apple",
    "book",
    "library",
    "what should I do to become a librarian?",
    "swimmer",
    "athlete",
    "swimming",
    "gym",
    "fruit"
]
connect_to_db()
save(queries)
search(["strawberry"])