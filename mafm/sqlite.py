import sqlite3

# sqlite는 서버 기반 데이터베이스가 아니다.
# 서버 기반 데이터 베이스(MySQL, PostgreSQL)와는 다르게, 서버가 없는 내장형 데이터베이스이다.
# 데이터베이스 파일은 하나의 독립적인 파일로 구성된다.

def initialize_database(db_name='filesystem.db'):
    # 데이터베이스 파일에 연결
    connection = sqlite3.connect('filesystem.db')

    # 커서 생성
    # 커서는 SQL 문을 실행하고 결과를 처리하는 데 사용되는 객체이다.
    # cursor.execute() 메소드를 사용해서 데이터베이스에 대한 SQL 쿼리를 실행할 수 있다.
    cursor = connection.cursor()

    # 첫 번째 테이블(file_info) 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_info (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            is_dir BOOLEAN NOT NULL
        )
    ''')

    # 두 번째 테이블(directory_structure) 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS directory_structure (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            id TEXT NOT NULL,
            dir_path TEXT NOT NULL,
            parent_dir_path TEXT
        )
    ''')

    # 변경 사항 저장
    connection.commit()
    connection.close()

# CREATE 함수 - 데이터 삽입
def insert_file_info(id, file_path, is_dir, db_name='filesystem.db'):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute('''
        INSERT INTO file_info (id, file_path, is_dir)
        VALUES (?, ?, ?)
    ''', (id, file_path, is_dir))
    connection.commit()
    connection.close()

def insert_directory_structure(id, dir_path, parent_dir_path, db_name='filesystem.db'):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute('''
        INSERT INTO directory_structure (id, dir_path, parent_dir_path)
        VALUES (?, ?, ?)
    ''', (id, dir_path, parent_dir_path))
    connection.commit()
    connection.close()

# READ 함수 - 데이터 조회
def get_file_info(db_name='filesystem.db'):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM file_info')
    rows = cursor.fetchall()
    connection.close()
    return rows

def get_directory_structure(db_name='filesystem.db'):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM directory_structure')
    rows = cursor.fetchall()
    connection.close()
    return rows

# UPDATE 함수 - 데이터 수정
def update_file_info(record_id, new_file_path, db_name='filesystem.db'):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute('''
        UPDATE file_info
        SET file_path = ?
        WHERE record_id = ?
    ''', (new_file_path, record_id))
    connection.commit()
    connection.close()

# DELETE 함수 - 데이터 삭제
def delete_file_info(record_id, db_name='filesystem.db'):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute('''
        DELETE FROM file_info
        WHERE record_id = ?
    ''', (record_id,))
    connection.commit()
    connection.close()