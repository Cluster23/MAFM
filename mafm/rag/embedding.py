from sentence_transformers import SentenceTransformer
import os
import psutil

# 모델을 전역 변수로 초기화하여 재사용
model = None
os.environ["TOKENIZERS_PARALLELISM"] = "false"


def initialize_model():

    global model
    if model is None:
        try:

            # 일단 1024 차원으로 실험
            # 실험 결과가 만족스럽지 않다면 모델을 clone 한 후 8000 차원 이상으로 늘릴 예정
            # 모델은 github에 등록되어 있음
            # CPU로 실험
            # GPU로 변환 시 SentenceTransformer() 메소드 뒤에 .cuda() 메소드를 붙여주면 됨
            # 모델 초기화
            model = SentenceTransformer(
                # "dunzhang/stella_en_400M_v5",
                "avsolatorio/GIST-small-Embedding-v0",  # 33
                # "hkunlp/instructor-base",  # 110
                trust_remote_code=True,
                device="cpu",
                config_kwargs={
                    "use_memory_efficient_attention": False,
                    "unpad_inputs": False,
                },
            )

            # model = SentenceTransformer("sentence-transformers/all-MiniLM-L12-v1")

            print("모델이 성공적으로 초기화되었습니다.")
        except Exception as e:
            print(f"모델 초기화 중 오류 발생: {e}")


def embedding(queries):
    global model

    # 모델이 초기화되지 않은 경우 초기화
    if model is None:
        initialize_model()

    try:
        # 쿼리 임베딩
        if not isinstance(queries, list) or not all(
            isinstance(q, str) for q in queries
        ):
            raise ValueError("The input to encode() must be a list of strings.")
        query_embeddings = model.encode(queries)

        return query_embeddings.tolist()
    except MemoryError as me:
        print(f"MemoryError: {me}")
    except Exception as e:
        print(f"embedding 중 오z류 발생: {e}")
        return None
