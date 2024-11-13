import pytest
from mafm.rag.embedding import embedding


@pytest.fixture
def test_sentences():
    # Define a set of test sentences
    return [
        "This is the first test sentence.",
        "Here is another example sentence.",
        "Sentence embeddings are useful.",
    ]


def test_embedding_output_shape(test_sentences):
    """Test that the embeddings have the correct shape."""
    embeddings = embedding(test_sentences)
    # Assert that the number of embeddings matches the number of sentences
    assert len(embeddings) == len(test_sentences)
