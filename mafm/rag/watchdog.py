import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from .vectorDb import save
from .sqlite import (
    insert_file_info,
    insert_directory_structure,
    update_file_info,
    get_id_by_path,
    change_directory_path,
    change_file_path,
    delete_directory_and_subdirectories,
)
from .embedding import embedding, initialize_model
from ..rag.fileops import get_file_data
from .vectorDb import (
    initialize_vector_db,
    find_by_id,
    insert_file_embedding,
    remove_by_id,
    delete_vector_db,
)
import os


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path

    def on_deleted(self, event):
        """파일 삭제 이벤트 처리"""
        if event.is_directory:
            # 디렉토리인 경우 -> 벡터 DB 자체를 삭제하고 SQLite에서 해당 디렉토리와 관련 데이터를 모두 삭제
            dir_path = event.src_path
            dir_name = os.path.basename(dir_path)
            db_name = dir_path + "/" + dir_name + ".db"
            delete_vector_db(db_name)

            # SQLite에서도 해당 디렉토리 관련 데이터 삭제
            delete_directory_and_subdirectories(dir_path)

            print(f"Deleted directory and associated VectorDB: {db_name}")
            return

        # 파일 삭제 처리
        # 1. 벡터 DB에서 파일을 조회한 후 Vector DB에서 해당 파일 삭제
        # 2. file_info 테이블에서 해당 레코드 삭제
        file_path = event.src_path
        dir_path = os.path.dirname(file_path)
        dir_name = os.path.basename(dir_path)

        db_name = dir_path + "/" + dir_name + ".db"
        id = get_id_by_path(file_path, "filesystem.db")
        remove_by_id(id, db_name)

        print(f"Deleted file: {event.src_path}")
        # SQLite에서 해당 파일 관련 데이터 삭제 로직 추가 (필요 시)


    def on_modified(self, event):
        """파일 수정 이벤트 처리"""
        if event.is_directory:
            return

        print(f"Modified file: {event.src_path}")
        self.process_file(event.src_path)

    def on_moved(self, event):
        """파일 이동 이벤트 처리"""
        if event.is_directory:
            change_directory_path(
                event.dir_src_path, event.dir_dest_path, "filesystem.db"
            )
            return

        print(f"Moved file: from {event.src_path} to {event.dest_path}")
        # DB에 저장된 경로를 새로운 경로로 업데이트
        self.move_file(event.src_path, event.dest_path)

    def on_created(self, event):
        """새로운 파일이 생겼을 경우"""
        absolute_file_path = event.src_path
        dirpath = os.path.dirname(absolute_file_path)
        dirname = os.path.basename(dirpath)

        if event.is_directory:
            # 생성된 것이 디렉토리인 경우 -> 새로운 VectorDB를 생성 후 경로를 SQLite에 저장
            try:
                initialize_vector_db(dirpath + "/" + dirname + ".db")
            except Exception as e:
                print(f"Error initializing vector DB for directory: {e}")

            id = insert_file_info(absolute_file_path, 1, "filesystem.db")
            insert_directory_structure(id, dirpath, dirpath.parent, "filesystem.db")
            return

        """파일 생성 로직"""
        last_modified_time = os.path.getmtime(absolute_file_path)

        # 파일 정보 삽입
        insert_file_info(absolute_file_path, 0, "filesystem.db")

        file_chunks = get_file_data(absolute_file_path)
        # 각 디렉토리의 벡터 DB에 해당 파일 내용을 저장
        save(dirpath + "/" + dirname + ".db", id, file_chunks[2:])

    def move_file(self, file_src_path, file_dest_path):
        """파일 처리 및 벡터 DB에 저장"""
        dir_path = os.path.dirname(file_src_path)
        dir_name = os.path.basename(dir_path)
        db_name = dir_path + "/" + dir_name + ".db"
        id = get_id_by_path(file_src_path, "filesystem.db")
        file_data = find_by_id(id, db_name)
        insert_file_embedding(file_data, db_name)
        remove_by_id(id, db_name)
        change_file_path(file_src_path, file_dest_path, db_name)


def start_watchdog(root_dir, db_path):
    # 모델 초기화
    initialize_model()

    # 파일 이벤트 핸들러 및 옵저버 생성
    event_handler = FileEventHandler(db_path)
    observer = Observer()
    observer.schedule(event_handler, path=root_dir, recursive=True)

    # 파일 시스템 모니터링 시작
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
