import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from rag.vectorDb import save
from rag.sqlite import (
    insert_file_info,
    insert_directory_structure,
    update_file_info,
    get_id_by_path,
    change_directory_path,
    change_file_path,
    delete_directory_and_subdirectories,
    initialize_database,
)
from rag.embedding import embedding, initialize_model
from rag.fileops import get_file_data
from rag.vectorDb import (
    initialize_vector_db,
    insert_file_embedding,
    find_by_id,
    remove_by_id,
    delete_vector_db,
)
from collections import defaultdict
import pdfplumber
from docx import Document


def read_pdf(file_path):
    """PDF 파일을 읽어서 텍스트로 변환하는 함수"""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def read_word(file_path):
    """Word 파일을 읽어서 텍스트로 변환하는 함수"""
    text = ""
    doc = Document(file_path)
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def split_text_into_chunks(text, chunk_size=500):
    """텍스트를 주어진 크기의 청크 배열로 분할하는 함수"""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

class FileEventHandler(FileSystemEventHandler):
    """파일 시스템 이벤트 핸들러 클래스"""

    def __init__(self):
        super().__init__()

    def is_dot_file(self, path):
        """숨김 파일인지 확인하는 함수"""
        return os.path.basename(path).startswith(".")

    def is_ignored_file(self, path):
        """특정 패턴을 가진 파일을 무시하는 함수"""
        ignored_patterns = ["db-journal", ".db"]
        return any(pattern in path for pattern in ignored_patterns)

    def on_deleted(self, event):
        """파일 또는 디렉토리 삭제 이벤트 처리 함수"""
        if self.is_dot_file(event.src_path) or self.is_ignored_file(event.src_path):
            print("ignore deleted: " + event.src_path)
            return  # 숨김 파일과 무시할 패턴을 가진 파일은 무시

        print("--deleted--")
        print("deleting: " + event.src_path)

        if event.is_directory:
            dir_path = event.src_path
            dir_name = os.path.basename(dir_path)

            db_name = dir_path + "/" + dir_name + ".db"
            delete_vector_db(db_name)  # 디렉토리와 연결된 벡터 DB 삭제
            delete_directory_and_subdirectories(dir_path)  # 디렉토리 정보 DB에서 삭제
            print(f"Deleted directory and associated VectorDB: {db_name}")
            return

        file_path = event.src_path
        dir_path = os.path.dirname(file_path)

        db_name = dir_path + "/" + os.path.basename(dir_path) + ".db"
        id = get_id_by_path(file_path, "filesystem.db")
        remove_by_id(id, db_name)  # 벡터 DB에서 파일 데이터 삭제
        print(f"Deleted file: {event.src_path}")

    # def on_modified(self, event):
    #     """파일 수정 이벤트 처리 함수"""
    #     if event.is_directory or self.is_dot_file(event.src_path) or self.is_ignored_file(event.src_path):
    #         print("directory or dotfile modified")
    #         return  # 디렉토리와 숨김 파일은 무시
    #
    #     file_src_path = event.src_path
    #     dir_path = os.path.dirname(file_src_path)
    #     db_name = dir_path + "/" + os.path.basename(dir_path) + ".db"
    #
    #
    #     id = get_id_by_path(file_src_path, "filesystem.db")
    #     remove_by_id(id, db_name)  # 기존 벡터 데이터 제거
    #     save(db_name, id, get_file_data(file_src_path)[2:])  # 새로운 벡터 데이터 저장
    #     insert_file_info(file_src_path, 0, "filesystem.db")  # 파일 정보 DB 업데이트
    #     print(f"Modified file: {event.src_path}")

    def on_moved(self, event):
        """파일 또는 디렉토리 이동 이벤트 처리 함수"""
        if (
            self.is_dot_file(event.src_path)
            or self.is_dot_file(event.dest_path)
            or self.is_ignored_file(event.src_path)
            or self.is_ignored_file(event.dest_path)
        ):
            return  # 숨김 파일은 무시

        print("--moved--")

        if event.is_directory:
            change_directory_path(
                event.src_path, event.dest_path, "filesystem.db"
            )  # 디렉토리 경로 변경
            print(f"Moved directory: from {event.src_path} to {event.dest_path}")
        else:
            print(f"Moved file: from {event.src_path} to {event.dest_path}")
            self.move_file(event.src_path, event.dest_path)

    def on_created(self, event):
        print("--created--", flush=True)
        """파일 생성 이벤트 처리 함수"""
        if self.is_dot_file(event.src_path) or self.is_ignored_file(event.src_path):
            return  # 숨김 파일과 무시할 패턴을 가진 파일은 무시

        absolute_file_path = event.src_path
        dirpath = os.path.dirname(absolute_file_path)
        dirname = os.path.basename(dirpath)

        if event.is_directory:
            print("created directory")
            try:
                initialize_vector_db(dirpath + "/" + dirname + ".db")  # 벡터 DB 초기화
                id = insert_file_info(absolute_file_path, 1, "filesystem.db")
                insert_directory_structure(
                    id, dirpath, os.path.dirname(dirpath), "filesystem.db"
                )
            except Exception as e:
                print(f"Error initializing vector DB for directory: {e}")
        else:
            print("created file")
            insert_file_info(
                absolute_file_path, 0, "filesystem.db"
            )  # 파일 정보 DB에 추가

            # 파일 형식에 따라 데이터를 읽고 500바이트 크기의 배열로 분할
            if absolute_file_path.endswith(".pdf"):
                text_content = read_pdf(absolute_file_path)
                text_chunks = split_text_into_chunks(text_content)
            elif absolute_file_path.endswith(".docx"):
                text_content = read_word(absolute_file_path)
                text_chunks = split_text_into_chunks(text_content)
            else:
                # 일반 텍스트 파일일 경우
                file_chunks = get_file_data(absolute_file_path)
                text_chunks = file_chunks[2:]  # 필요한 데이터 조정


            # 벡터 DB에 저장
            save(
                dirpath + "/" + dirname + ".db",
                get_id_by_path(absolute_file_path, "filesystem.db"),
                text_chunks,
            )
            print(f"Created file: {event.src_path}")

    def move_file(self, file_src_path, file_dest_path):
        """파일 이동 시 벡터 DB 업데이트 함수"""
        dir_path = os.path.dirname(file_src_path)
        db_name = dir_path + "/" + os.path.basename(dir_path) + ".db"
        id = get_id_by_path(file_src_path, "filesystem.db")
        file_data = find_by_id(id, db_name)
        insert_file_embedding(file_data, db_name)  # 파일 임베딩 데이터 추가
        remove_by_id(id, db_name)  # 기존 ID 데이터 제거
        change_file_path(file_src_path, file_dest_path, db_name)  # 파일 경로 업데이트


# SQLite DB에 파일 및 디렉토리 데이터 삽입
def start_command_c(root):
    # 시작 시간 기록
    start_time = time.time()

    # SQLite DB 연결 및 초기화
    try:
        initialize_database("filesystem.db")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return

    # root 디렉토리의 벡터 DB 초기화
    try:
        initialize_vector_db(root + "/" + os.path.basename(root) + ".db")
    except Exception as e:
        print(f"Error initializing vector DB for root: {e}")
        return

    id = insert_file_info(root, 1, "filesystem.db")

    # 루트의 부모 디렉토리 찾기
    last_slash_index = root.rfind("/")
    if last_slash_index != -1:
        root_parent = root[:last_slash_index]

    insert_directory_structure(id, root, root_parent, "filesystem.db")

    # 디렉터리 재귀 탐색
    for dirpath, dirnames, filenames in os.walk(root):
        # 디렉토리 정보 삽입
        for dirname in dirnames:
            full_path = os.path.join(dirpath, dirname)
            print(f"디렉토리 경로: {full_path}")
            try:
                initialize_vector_db(full_path + "/" + dirname + ".db")
            except Exception as e:
                print(f"Error initializing vector DB for directory: {e}")
                continue

            id = insert_file_info(full_path, 1, "filesystem.db")
            insert_directory_structure(id, full_path, dirpath, "filesystem.db")

        # 파일 정보 삽입 및 벡터 DB에 저장
        for filename in filenames:
            # 비밀 파일과 .db 파일 제외
            if filename.startswith(".") or filename.endswith(".db"):
                continue

            full_path = os.path.join(dirpath, filename)
            print(f"Embedding 하는 파일의 절대 경로: {full_path}")

            # 파일 정보 삽입
            id = insert_file_info(full_path, 0, "filesystem.db")

            # PDF 및 Word 파일 처리
            if filename.endswith(".pdf"):
                text_content = read_pdf(full_path)
                text_chunks = split_text_into_chunks(text_content)
            elif filename.endswith(".docx"):
                text_content = read_word(full_path)
                text_chunks = split_text_into_chunks(text_content)
            else:
                # 일반 텍스트 파일 처리
                file_chunks = get_file_data(full_path)
                text_chunks = file_chunks[2:]  # 필요한 데이터 조정

            # 각 디렉토리의 벡터 DB에 해당 파일 내용을 저장
            dirname = dirpath.split("/")[-1]
            save(dirpath + "/" + dirname + ".db", id, text_chunks)

    # 종료 시간 기록
    end_time = time.time()

    # 걸린 시간 계산
    elapsed_time = end_time - start_time
    print(f"작업에 걸린 시간: {elapsed_time:.4f} 초")


def start_watchdog(root_dir):
    """파일 시스템 감시 시작 함수"""
    initialize_model()  # 임베딩 모델 초기화
    try:
        # 해당 root 아래에 존재하는 모든 파일들을 탐색해서 sqlite db에 저장해야함.
        # start_command_python(root_dir)
        start_command_c(root_dir)
        # get_file_data(root)
    except IndexError:
        print("start: missing argument")
    except FileNotFoundError:
        print(f"start: no such file or directory: {root_dir}")

    # 파일 이벤트 핸들러와 감시자 생성
    event_handler = FileEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=root_dir, recursive=True)

    # 파일 시스템 모니터링 시작
    observer.start()
    try:
        while True:
            time.sleep(1)  # 감시 유지
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


import argparse

if __name__ == "__main__":
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description="MAFM watchdog")
    parser.add_argument("-r", "--root", help="Root directory path")
    args = parser.parse_args()

    # 루트 디렉토리 경로가 제공되지 않으면 경고 메시지 출력
    if not args.root:
        print("Root directory path is required.")
    else:
        start_watchdog(args.root)  # 감시 시작
