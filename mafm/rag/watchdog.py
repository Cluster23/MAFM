import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from .vectorDb import save
from .sqlite import insert_file_info, update_file_info
from embedding import embedding, initialize_model
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

    def process_file(self, file_path):
        """파일 처리 및 벡터 DB에 저장"""
        last_modified_time = os.path.getmtime(file_path)

        # 파일 내용을 500바이트씩 읽기
        file_chunks = []
        try:
            with open(file_path, "rb") as file:
                while True:
                    chunk = file.read(500)
                    if not chunk:
                        break
                    file_chunks.append(chunk.decode("utf-8", errors="ignore"))
        except Exception as e:
            print(f"Failed to read file data for {file_path}: {e}")
            return

        # 임베딩 및 벡터 DB 저장
        embedding_result = embedding(file_chunks)
        save(self.db_path, Path(file_path).name, embedding_result)
        update_file_info(file_path, last_modified_time, "filesystem.db")


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
