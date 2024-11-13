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
    initialize_database
)
from rag.embedding import embedding, initialize_model
from rag.fileops import get_file_data
from rag.vectorDb import (
    initialize_vector_db,
    find_by_id,
    remove_by_id,
    delete_vector_db,
)
from collections import defaultdict


class FileEventHandler(FileSystemEventHandler):
    """파일 시스템 이벤트 핸들러 클래스"""

    def __init__(self, cooldown=1.0):
        super().__init__()
        self.recent_events = defaultdict(float)  # 최근 이벤트 기록용 딕셔너리 (파일 경로별로 타임스탬프 저장)
        self.cooldown = cooldown  # 이벤트 발생 쿨다운 시간 (초)

    def is_dot_file(self, path):
        """숨김 파일인지 확인하는 함수"""
        return os.path.basename(path).startswith(".")

    def on_deleted(self, event):
        """파일 또는 디렉토리 삭제 이벤트 처리 함수"""
        if self.is_dot_file(event.src_path):
            return  # 숨김 파일은 무시

        print("--deleted--")

        if event.is_directory:
            dir_path = event.src_path
            dir_name = os.path.basename(dir_path)

            print("dir_path: " + dir_path)
            print("dir_name: " + dir_name)

            db_name = dir_path + "/" + dir_name + ".db"
            delete_vector_db(db_name)  # 디렉토리와 연결된 벡터 DB 삭제
            delete_directory_and_subdirectories(dir_path)  # 디렉토리 정보 DB에서 삭제
            print(f"Deleted directory and associated VectorDB: {db_name}")
            return

        file_path = event.src_path
        dir_path = os.path.dirname(file_path)

        print("dir_path: " + dir_path)
        print("file_path: " + file_path)

        db_name = dir_path + "/" + os.path.basename(dir_path) + ".db"
        id = get_id_by_path(file_path, "filesystem.db")
        remove_by_id(id, db_name)  # 벡터 DB에서 파일 데이터 삭제
        print(f"Deleted file: {event.src_path}")

    def on_modified(self, event):
        print("on_modified")
        """파일 수정 이벤트 처리 함수"""
        if event.is_directory or self.is_dot_file(event.src_path):
            return  # 디렉토리와 숨김 파일은 무시

        # 최근 생성된 파일인지 확인하여 쿨다운 시간 이내에 발생한 수정 이벤트는 무시
        if (time.time() - self.recent_events.get(event.src_path, 0)) < self.cooldown:
            return  # 쿨다운 시간 이내이므로 무시

        file_src_path = event.src_path
        dir_path = os.path.dirname(file_src_path)
        db_name = dir_path + "/" + os.path.basename(dir_path) + ".db"

        print("--modified--")
        print("dir_path: " + dir_path)
        print("db_name: " + db_name)

        id = get_id_by_path(file_src_path, "filesystem.db")
        remove_by_id(id, db_name)  # 기존 벡터 데이터 제거
        save(db_name, id, get_file_data(file_src_path)[2:])  # 새로운 벡터 데이터 저장
        insert_file_info(file_src_path, 0, "filesystem.db")  # 파일 정보 DB 업데이트
        print(f"Modified file: {event.src_path}")

    def on_moved(self, event):
        """파일 또는 디렉토리 이동 이벤트 처리 함수"""
        if self.is_dot_file(event.src_path) or self.is_dot_file(event.dest_path):
            return  # 숨김 파일은 무시

        print("--moved--")

        if event.is_directory:
            change_directory_path(event.src_path, event.dest_path, "filesystem.db")  # 디렉토리 경로 변경
            print(f"Moved directory: from {event.src_path} to {event.dest_path}")
        else:
            print(f"Moved file: from {event.src_path} to {event.dest_path}")
            self.move_file(event.src_path, event.dest_path)

    def on_created(self, event):
        print("--created--", flush=True)
        """파일 생성 이벤트 처리 함수"""
        if self.is_dot_file(event.src_path):
            return  # 숨김 파일은 무시

        self.recent_events[event.src_path] = time.time()  # 생성된 파일 기록
        absolute_file_path = event.src_path
        dirpath = os.path.dirname(absolute_file_path)
        dirname = os.path.basename(dirpath)

        print("dirpath: " + dirpath, flush=True)
        print("dirname: " + dirname, flush=True)

        if event.is_directory:
            try:
                initialize_vector_db(dirpath + "/" + dirname + ".db")  # 벡터 DB 초기화
                id = insert_file_info(absolute_file_path, 1, "filesystem.db")
                insert_directory_structure(id, dirpath, os.path.dirname(dirpath), "filesystem.db")
            except Exception as e:
                print(f"Error initializing vector DB for directory: {e}")
        else:
            insert_file_info(absolute_file_path, 0, "filesystem.db")  # 파일 정보 DB에 추가
            file_chunks = get_file_data(absolute_file_path)
            save(dirpath + "/" + dirname + ".db", get_id_by_path(absolute_file_path, "filesystem.db"), file_chunks[2:])
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


def start_watchdog(root_dir):
    """파일 시스템 감시 시작 함수"""
    initialize_model()  # 임베딩 모델 초기화
    initialize_database("filesystem.db")  # 파일 시스템 DB 초기화

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
