from sentence_transformers import SentenceTransformer

def embedding(queries):
    # 일단 1024 차원으로 실험
    # 실험 결과가 만족스럽지 않다면 모델을 clone 한 후 8000 차원 이상으로 늘릴 예정
    # 모델은 github에 등록되어 있음
    # CPU로 실험
    # GPU로 변환 시 SentenceTransformer() 메소드 뒤에 .cuda() 메소드를 붙여주면 됨

    model = SentenceTransformer(
        "dunzhang/stella_en_400M_v5",
        trust_remote_code=True,
        device="cpu",
        config_kwargs={"use_memory_efficient_attention": False, "unpad_inputs": False}
    )

    query_embeddings = model.encode(queries, prompt_name="s2p_query")
    print(query_embeddings.shape)

    return query_embeddings.tolist()
