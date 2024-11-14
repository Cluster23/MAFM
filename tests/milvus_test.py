import pytest
from pymilvus import connections, utility, Collection
from mafm.rag.vectorDb import (
    initialize_vector_db,
    delete_vector_db,
    save,
    insert_file_embedding,
    search,
    find_by_id,
    remove_by_id,
)
from mafm.rag.embedding import embedding  # Ensure this is implemented
from mafm.rag.sqlite import get_path_by_id  # Ensure this is implemented

# Constants for testing
DB_NAME = "test_db"
TEST_ID = 123
TEST_QUERIES = ["test query one", "test query two"]
TEST_FILE_DATA = [
    # Assuming file_data is in the format expected by insert_file_embedding
    [TEST_ID, embedding(["file data sample"])[0], "file data sample"]
]


@pytest.fixture(scope="module")
def setup_milvus():
    # Setup: Initialize the vector database
    initialize_vector_db(DB_NAME)
    yield
    # Teardown: Delete the vector database
    delete_vector_db(DB_NAME)


def test_initialize_vector_db():
    # Test initialization
    initialize_vector_db(DB_NAME)
    connections.connect(alias="default", host="localhost", port="19530")
    collection_name = f"{DB_NAME}_demo_collection"
    assert utility.has_collection(collection_name)
    connections.disconnect(alias="default")


def test_save(setup_milvus):
    # Test saving data
    save(DB_NAME, TEST_ID, TEST_QUERIES)
    connections.connect(alias="default", host="localhost", port="19530")
    collection_name = f"{DB_NAME}_demo_collection"
    collection = Collection(name=collection_name)
    collection.load()
    # Query to check if data was inserted
    res = collection.query(expr=f"id in [{TEST_ID}]", output_fields=["id", "word"])
    assert len(res) > 0
    collection.release()
    connections.disconnect(alias="default")


def test_insert_file_embedding(setup_milvus):
    # Test inserting file embeddings
    insert_file_embedding(TEST_FILE_DATA, DB_NAME)
    connections.connect(alias="default", host="localhost", port="19530")
    collection_name = f"{DB_NAME}_demo_collection"
    collection = Collection(name=collection_name)
    collection.load()
    # Query to check if data was inserted
    res = collection.query(expr=f"id in [{TEST_ID}]", output_fields=["id", "word"])
    assert len(res) > 0
    collection.release()
    connections.disconnect(alias="default")


def test_search(setup_milvus, mocker):
    # Mock get_path_by_id to return a predictable value
    mocker.patch("your_module.get_path_by_id", return_value="path/to/file")

    # Ensure data is saved before searching
    save(DB_NAME, TEST_ID, TEST_QUERIES)

    # Test searching
    results = search(DB_NAME, ["test query one"])
    assert results is not None
    assert len(results) == 2  # As limit=2 in search
    assert all(result == "path/to/file" for result in results)


def test_find_by_id(setup_milvus):
    # Ensure data is saved before querying
    save(DB_NAME, TEST_ID, TEST_QUERIES)

    # Test finding by ID
    res = find_by_id(TEST_ID, DB_NAME)
    assert res is not None
    assert len(res) > 0
    assert res[0]["id"] == TEST_ID


def test_remove_by_id(setup_milvus):
    # Ensure data is saved before deleting
    save(DB_NAME, TEST_ID, TEST_QUERIES)

    # Test removing by ID
    remove_by_id(TEST_ID, DB_NAME)

    # Check if the data is actually deleted
    connections.connect(alias="default", host="localhost", port="19530")
    collection_name = f"{DB_NAME}_demo_collection"
    collection = Collection(name=collection_name)
    collection.load()
    res = collection.query(expr=f"id in [{TEST_ID}]", output_fields=["id", "word"])
    assert len(res) == 0  # No records should be found
    collection.release()
    connections.disconnect(alias="default")


def test_delete_vector_db():
    # Test deleting the vector database
    initialize_vector_db(DB_NAME)
    delete_vector_db(DB_NAME)
    connections.connect(alias="default", host="localhost", port="19530")
    collection_name = f"{DB_NAME}_demo_collection"
    assert not utility.has_collection(collection_name)
    connections.disconnect(alias="default")
