import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from mafm.rag.vectorDb import save
from mafm.rag.sqlite import (
    insert_file_info,
    insert_directory_structure,
    update_file_info,
    get_id_by_path,
    change_directory_path,
    change_file_path,
    delete_directory_and_subdirectories,
    initialize_database
)
from mafm.rag.embedding import embedding, initialize_model
from mafm.rag.fileops import get_file_data
from mafm.rag.vectorDb import (
    initialize_vector_db,
    find_by_id,
    insert_file_embedding,
    remove_by_id,
    delete_vector_db,
)


class FileEventHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()

    def is_dot_file(self, path):
        """Check if the file or directory starts with a dot."""
        return os.path.basename(path).startswith(".")

    def on_deleted(self, event):
        """Handle file deletion events"""
        if self.is_dot_file(event.src_path):
            return  # Skip dot files

        if event.is_directory:
            dir_path = event.src_path
            dir_name = os.path.basename(dir_path)

            print("--deleted--")
            print("dir_path: " + dir_path)
            print("dir_name: " + dir_name)

            db_name = dir_path + "/" + dir_name + ".db"
            delete_vector_db(db_name)
            delete_directory_and_subdirectories(dir_path)
            print(f"Deleted directory and associated VectorDB: {db_name}")
            return

        file_path = event.src_path
        dir_path = os.path.dirname(file_path)
        db_name = dir_path + "/" + os.path.basename(dir_path) + ".db"
        id = get_id_by_path(file_path, "filesystem.db")
        remove_by_id(id, db_name)
        print(f"Deleted file: {event.src_path}")

    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory or self.is_dot_file(event.src_path):
            return  # Skip directories and dot files

        file_src_path = event.src_path
        dir_path = os.path.dirname(file_src_path)
        db_name = dir_path + "/" + os.path.basename(dir_path) + ".db"
        id = get_id_by_path(file_src_path, "filesystem.db")
        remove_by_id(id, db_name)
        save(db_name, id, get_file_data(file_src_path)[2:])
        insert_file_info(file_src_path, 0, "filesystem.db")
        print(f"Modified file: {event.src_path}")

    def on_moved(self, event):
        """Handle file move events"""
        if self.is_dot_file(event.src_path) or self.is_dot_file(event.dest_path):
            return  # Skip dot files

        if event.is_directory:
            change_directory_path(event.src_path, event.dest_path, "filesystem.db")
            print(f"Moved directory: from {event.src_path} to {event.dest_path}")
        else:
            print(f"Moved file: from {event.src_path} to {event.dest_path}")
            self.move_file(event.src_path, event.dest_path)

    def on_created(self, event):
        """Handle file creation events"""
        if self.is_dot_file(event.src_path):
            return  # Skip dot files

        absolute_file_path = event.src_path
        dirpath = os.path.dirname(absolute_file_path)
        dirname = os.path.basename(dirpath)

        print("--created--")
        print("dirpath: " + dirpath)
        print("dirname: " + dirname)
        if event.is_directory:
            try:
                initialize_vector_db(dirpath + "/" + dirname + ".db")
                id = insert_file_info(absolute_file_path, 1, "filesystem.db")
                insert_directory_structure(id, dirpath, os.path.dirname(dirpath), "filesystem.db")
            except Exception as e:
                print(f"Error initializing vector DB for directory: {e}")
        else:
            insert_file_info(absolute_file_path, 0, "filesystem.db")
            file_chunks = get_file_data(absolute_file_path)
            save(dirpath + "/" + dirname + ".db", get_id_by_path(absolute_file_path, "filesystem.db"), file_chunks[2:])
            print(f"Created file: {event.src_path}")

    def move_file(self, file_src_path, file_dest_path):
        """Handle file embedding and update in VectorDB on file move"""
        dir_path = os.path.dirname(file_src_path)
        db_name = dir_path + "/" + os.path.basename(dir_path) + ".db"
        id = get_id_by_path(file_src_path, "filesystem.db")
        file_data = find_by_id(id, db_name)
        insert_file_embedding(file_data, db_name)
        remove_by_id(id, db_name)
        change_file_path(file_src_path, file_dest_path, db_name)


def start_watchdog(root_dir):
    initialize_model()
    initialize_database("filesystem.db")

    # Create file event handler and observer
    event_handler = FileEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=root_dir, recursive=True)

    # Start file system monitoring
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MAFM watchdog")
    parser.add_argument("-r", "--root", help="Root directory path")
    args = parser.parse_args()

    if not args.root:
        print("Root directory path is required.")
    else:
        start_watchdog(args.root)
