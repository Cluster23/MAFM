import sqlite3
import os

# sqlite는 서버 기반 데이터베이스가 아니다.
# 서버 기반 데이터 베이스(MySQL, PostgreSQL)와는 다르게, 서버가 없는 내장형 데이터베이스이다.
# 데이터베이스 파일은 하나의 독립적인 파일로 구성된다.


def initialize_database(db_name="filesystem.db"):
    # 기존에 db가 존재하면 날림
    if os.path.exists(db_name):
        os.remove(db_name)

    # 데이터베이스 파일에 연결
    connection = sqlite3.connect("filesystem.db")

    # 커서 생성
    # 커서는 SQL 문을 실행하고 결과를 처리하는 데 사용되는 객체이다.
    # cursor.execute() 메소드를 사용해서 데이터베이스에 대한 SQL 쿼리를 실행할 수 있다.
    cursor = connection.cursor()

    # 첫 번째 테이블(file_info) 생성
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS file_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            is_dir INTEGER NOT NULL
        )
    """
    )

    # 두 번째 테이블(directory_structure) 생성
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS directory_structure (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            id TEXT NOT NULL,
            dir_path TEXT NOT NULL,
            parent_dir_path TEXT
        )
    """
    )

    # 변경 사항 저장
    connection.commit()
    connection.close()


# CREATE 함수 - 데이터 삽입
def insert_file_info(file_path, is_dir, db_name="filesystem.db"):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO file_info (file_path, is_dir)
        VALUES (?, ?)
        """,
        (file_path, is_dir),
    )
    cursor.execute("SELECT last_insert_rowid()")
    rows = cursor.fetchall()
    connection.commit()
    connection.close()
    return rows[0][0]


def insert_directory_structure(id, dir_path, parent_dir_path, db_name="filesystem.db"):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO directory_structure (id, dir_path, parent_dir_path)
        VALUES (?, ?, ?)
    """,
        (id, dir_path, parent_dir_path),
    )
    connection.commit()
    connection.close()


# READ 함수 - 데이터 조회
def get_file_info(db_name="filesystem.db"):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM file_info")
    rows = cursor.fetchall()
    connection.close()
    return rows


def get_path_by_id(id, db_name="filesystem.db"):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute("SELECT file_path FROM file_info WHERE id = ?", (id,))
    rows = cursor.fetchall()
    connection.close()
    file_path = rows[0][0]
    return file_path


def get_id_by_path(path, db_name="filesystem.db"):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM file_info WHERE file_path = ?", (path,))
    rows = cursor.fetchall()
    connection.close()
    print("rows ========", rows)
    file_path = rows[0][0]
    return file_path


def get_directory_structure(db_name="filesystem.db"):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute("SELECT dir_path FROM directory_structure")
    rows = cursor.fetchall()
    connection.close()
    ret_list = []
    for row in rows:
        ret_list.append(row[0])
    return ret_list


# UPDATE 함수 - 데이터 수정
def update_file_info(id, new_file_path, db_name="filesystem.db"):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE file_info
        SET file_path = ?
        WHERE id = ?
    """,
        (new_file_path, id),
    )
    connection.commit()
    connection.close()


def update_directory_structure(record_id, new_dir_path, db_name="filesystem.db"):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE file_info
        SET dir_path = ?
        WHERE record_id = ?
    """,
        (new_dir_path, record_id),
    )
    connection.commit()
    connection.close()


# DELETE 함수 - 데이터 삭제
def delete_file_info(record_id, db_name="filesystem.db"):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        DELETE FROM file_info
        WHERE record_id = ?
    """,
        (record_id,),
    )
    connection.commit()
    connection.close()


def change_directory_path(dir_src_path, dir_dest_path, db_name="filesystem.db"):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE directory_structure
        SET dir_path = ?
        WHERE dir_path = ?
    """,
        (dir_dest_path, dir_src_path),
    )
    cursor.execute(
        """
        SELECT file_path FROM file_info WHERE file_path LIKE ?
        """,
        (f"{dir_src_path}%",),
    )
    rows = cursor.fetchall()

    # 각 레코드에 대해 dir_path를 업데이트합니다.
    for (file_path,) in rows:
        new_file_path = file_path.replace(dir_src_path, dir_dest_path, 1)
        cursor.execute(
            """
            UPDATE file_info
            SET file_path = ?
            WHERE file_path = ?
            """,
            (new_file_path, file_path),
        )
    connection.commit()
    connection.close()


def change_file_path(file_src_path, file_dest_path, db_name):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE file_info
        SET file_path = ?
        WHERE file_path = ?
        """,
        (file_dest_path, file_src_path),
    )
    connection.commit()
    connection.close()


def delete_directory_and_subdirectories(dir_path):
    connection = sqlite3.connect("filesystem.db")
    cursor = connection.cursor()

    # directory_structure 테이블에서 dir_path가 포함된 모든 레코드 삭제
    cursor.execute(
        """
        DELETE FROM directory_structure
        WHERE dir_path LIKE ?
        """,
        (f"{dir_path}%",),
    )

    # file_info 테이블에서 file_path가 dir_path로 시작하는 모든 레코드 삭제
    cursor.execute(
        """
        DELETE FROM file_info
        WHERE file_path LIKE ?
        """,
        (f"{dir_path}%",),
    )

    # 변경 사항을 커밋
    conn.commit()
    print(f"Deleted all records related to {dir_path} and its subdirectories.")
