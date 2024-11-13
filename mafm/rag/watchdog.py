import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from .vectorDb import save
from .sqlite import insert_file_info, insert_directory_structure, update_file_info
from .embedding import embedding, initialize_model
from ..rag.fileops import get_file_data
from .vectorDb import initialize_vector_db
import os


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path

    def on_modified(self, event):
        """파일 수정 이벤트 처리"""
        if event.is_directory:
            return

        print(f"Modified file: {event.src_path}")
        self.process_file(event.src_path)

    def on_moved(self, event):
        """파일 이동 이벤트 처리"""
        if event.is_directory:
            return

        print(f"Moved file: from {event.src_path} to {event.dest_path}")
        # DB에 저장된 경로를 새로운 경로로 업데이트
        self.process_file(event.dest_path)

    def on_created(self, event, absolute_file_path):
        """새로운 파일이 생겼을 경우"""

        dirname = os.path.dirname(absolute_file_path)
        dirpath = Path(dirname)

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


def start_watchdog(root_dir, db_path):
    # 모델 초기화
    initialize_model()

    # 파일 이벤트 핸들러 및 옵저버 생성
    event_handler = FileEventHandler(db_path)
    observer = Observer()
    observer.schedule(event_handler, path=root_dir, recursive=True)

    # 파일 시스템 모니터링 시작
    observer.start()
    print(f"Started watchdog for {root_dir}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    root_directory = "/path/to/your/root"
    db_path = root_directory + ".db"
    start_watchdog(root_directory, db_path)
