from sentence_transformers import SentenceTransformer

query_prompt_name = "s2p_query"
queries = [
    "What are some ways to reduce stress?",
]
# docs do not need any prompts
docs = [
    "There are many effective ways to reduce stress. Some common techniques include deep breathing, meditation, and physical activity. Engaging in hobbies, spending time in nature, and connecting with loved ones can also help alleviate stress. Additionally, setting boundaries, practicing self-care, and learning to say no can prevent stress from building up.",
    "Green tea has been consumed for centuries and is known for its potential health benefits. It contains antioxidants that may help protect the body against damage caused by free radicals. Regular consumption of green tea has been associated with improved heart health, enhanced cognitive function, and a reduced risk of certain types of cancer. The polyphenols in green tea may also have anti-inflammatory and weight loss properties.",
]

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

query_embeddings = model.encode(queries, prompt_name=query_prompt_name)
doc_embeddings = model.encode(docs)
print(query_embeddings.shape, doc_embeddings.shape)

similarities = model.similarity(query_embeddings, doc_embeddings)
print(similarities)