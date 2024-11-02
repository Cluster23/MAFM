import os
import subprocess
import tempfile
import time
from rag.fileops import make_soft_links, get_file_data, get_all_file_data
from rag.sqlite import (
    initialize_database,
    insert_file_info,
    insert_directory_structure,
    get_file_info,
    get_directory_structure,
    update_file_info,
    update_directory_structure,
    delete_file_info,
    delete_directory_structure,
)
from rag.vectorDb import (
    initialize_vector_db,
    save,
    search,
)
from rag.embedding import initialize_model
from agent.graph import graph
import ctypes
link_dir = None
def start_command_python(root):
    # 시작 시간 기록
    start_time = time.time()

    # SQLite DB 연결 및 초기화
    try:
        initialize_database("filesystem.db")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return

    id = 1

    # root 자체는 os.walk(root)에 포함되지 않음 -> 따로 처리 필요
    try:
        initialize_vector_db(root + ".db")
    except Exception as e:
        print(f"Error initializing vector DB for root: {e}")
        return

    # print(root)
    insert_file_info(id, root, 1, "filesystem.db")

    # 루트의 부모 디렉토리 찾기
    last_slash_index = root.rfind("/")
    if last_slash_index != -1:
        root_parent = root[:last_slash_index]

    insert_directory_structure(id, root, root_parent, "filesystem.db")
    id += 1

    # 디렉터리 재귀 탐색
    for dirpath, dirnames, filenames in os.walk(root):
        # 디렉터리 정보 삽입
        for dirname in dirnames:
            full_path = os.path.join(dirpath, dirname)

            try:
                initialize_vector_db(full_path + ".db")
            except Exception as e:
                print(f"Error initializing vector DB for directory: {e}")
                continue

            print(f"디렉토리 경로: {full_path}")
            insert_file_info(id, full_path, 1, "filesystem.db")
            insert_directory_structure(id, full_path, dirpath, "filesystem.db")
            id += 1

        # 파일 정보 삽입 및 벡터 DB에 저장
        for filename in filenames:
            # 비밀 파일(파일 이름이 .으로 시작)과 .db 파일 제외
            if filename.startswith(".") or filename.endswith(".db"):
                continue

            full_path = os.path.join(dirpath, filename)
            print(f"Embedding 하는 파일의 절대 경로: {full_path}")

            # 파일 정보 삽입
            insert_file_info(id, full_path, 0, "filesystem.db")

            file_chunks = []

            # 파일 데이터를 500Bytes씩 읽기
            try:
                with open(full_path, "rb") as file:
                    while True:
                        chunk = file.read(500)
                        if not chunk:
                            break
                        file_chunks.append(
                            chunk.decode("utf-8", errors="ignore")
                        )  # 바이너리 데이터를 문자열로 변환
            except Exception as e:
                print(f"Failed to read file data for {full_path}: {e}")
                continue

            # 각 디렉토리의 벡터 DB에 해당 파일 내용을 저장
            save(dirpath + ".db", id, file_chunks)

            id += 1

    # 종료 시간 기록
    end_time = time.time()

    # 걸린 시간 계산
    elapsed_time = end_time - start_time
    print(f"작업에 걸린 시간: {elapsed_time:.4f} 초")


# SQLite DB에 파일 및 디렉토리 데이터 삽입
import os
import time


def start_command_c(root):
    # 시작 시간 기록
    start_time = time.time()

    # SQLite DB 연결 및 초기화
    try:
        initialize_database("filesystem.db")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return

    # C 코드에서 파일 데이터 가져오기
    file_data_list = get_all_file_data(root)

    if file_data_list is None:
        print("Error: file_data_list is NULL.")
        return

    id = 1
    added_directories = set()  # 이미 추가된 디렉토리 경로를 저장하는 집합

    # 데이터베이스에 파일 정보 삽입
    for file_data in file_data_list:
        path = file_data[0]  # 절대 경로
        name = file_data[1]  # 파일 이름
        is_dir = False  # file_data_list에는 파일만 포함되므로 기본적으로 False

        # 파일이 속한 디렉토리 경로 확인
        dirpath = os.path.dirname(path)

        # 비밀 파일 제외, db 파일 제외
        if name.startswith(".") or name.endswith(".db"):
            continue

        # 디렉토리가 추가되지 않았다면 추가
        if dirpath not in added_directories:
            parent_dir = os.path.dirname(dirpath) if dirpath != root else None
            insert_file_info(id, dirpath, 1, "filesystem.db")
            insert_directory_structure(id, dirpath, parent_dir, "filesystem.db")

            try:
                initialize_vector_db(dirpath + ".db")  # 디렉토리와 대응되는 Vector DB 생성
            except Exception as e:
                print(f"Error initializing vector DB for directory: {e}")
                continue

            added_directories.add(dirpath)  # 디렉토리 경로를 집합에 추가
            id += 1

        # 파일 정보 삽입
        insert_file_info(id, path, is_dir, "filesystem.db")


        # 파일 내용을 벡터화하여 해당 디렉토리의 Vector DB에 저장
        file_chunks = file_data[2:]
        print(f"Embedding 하는 파일의 절대 경로: {path}")
        save(dirpath + ".db", id, file_chunks)
        id += 1

    # 종료 시간 기록
    end_time = time.time()

    # 걸린 시간 계산
    elapsed_time = end_time - start_time
    print(f"작업에 걸린 시간: {elapsed_time:.4f} 초")

if __name__ == "__main__":
#    start_command_python("/Users/Ruffles/Projects/MAFM/MAFM/mafm/MAFM_test")
    start_command_c("/Users/Ruffles/Projects/MAFM/MAFM/mafm/MAFM_test")