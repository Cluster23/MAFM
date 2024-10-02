import os
import subprocess
import tempfile
import time
from fileops import make_soft_links, get_file_data, get_all_file_data
from sqlite import (
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

link_dir = None


def execute_command(command):
    global link_dir
    try:
        cmd_parts = command.strip().split()
        if cmd_parts[0] == "mf":
            # file_data = get_all_file_data(cmd_parts[1])
            # print(file_data)

            temp_dir = tempfile.TemporaryDirectory()
            make_soft_links(
                [
                    "/Users/parksehwan/Documents/MAFM/mafm/shell.py",
                    "/Users/parksehwan/Documents/MAFM/mafm/a.txt",
                ],
                temp_dir,
            )
            os.chdir(temp_dir.name)
            link_dir = temp_dir
            return
        elif cmd_parts[0] == "cd":
            try:
                if cmd_parts[1] == "~":
                    os.chdir(os.path.expanduser("~"))
                else:
                    os.chdir(cmd_parts[1])
            except IndexError:
                print("cd: missing argument")
            except FileNotFoundError:
                print(f"cd: no such file or directory: {cmd_parts[1]}")

        elif cmd_parts[0] == "start":
            # start 뒤에 오는 경로를 root로 지정해서, 해당 위치에서부터 MAFM을 활성화
            # /Users 아래에 존재하는 모든 디렉토리들을 관리할 수 있으면 좋겠지만, 일단 프로토타입이기 때문에 depth를 최소화
            try:
                root = cmd_parts[1]

                # 해당 root 아래에 존재하는 모든 파일들을 탐색해서 sqlite db에 저장해야함.
                # start_command_python(root)
                # start_command_c(root)
                # get_file_data(root)
            except IndexError:
                print("start: missing argument")
            except FileNotFoundError:
                print(f"start: no such file or directory: {cmd_parts[1]}")

        else:
            result = subprocess.run(cmd_parts, check=True)
            return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
    except FileNotFoundError:
        print(f"Command not found: {command}")


def start_command_python(root):
    # 시작 시간 기록
    start_time = time.time()

    # SQLite DB 연결 및 초기화
    initialize_database("filesystem.db")

    id = 1
    # 디렉터리 재귀 탐색
    for dirpath, dirnames, filenames in os.walk(root):
        # 디렉터리 정보 삽입
        for dirname in dirnames:
            full_path = os.path.join(dirpath, dirname)
            # ToDo id값 해결해야됨
            print(full_path)
            insert_file_info(id,full_path,1,"filesystem.db")
            insert_directory_structure(id,full_path,dirpath,"filesystem.db")
            id += 1

        # 파일 정보 삽입
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            print(full_path)
            # ToDo id값 해결해야됨
            insert_file_info(id, full_path, 0, "filesystem.db")
            id += 1

    # 종료 시간 기록
    end_time = time.time()

    # 걸린 시간 계산
    elapsed_time = end_time - start_time
    print(f"작업에 걸린 시간: {elapsed_time:.4f} 초")


# SQLite DB에 파일 및 디렉토리 데이터 삽입
def start_command_c(root):
    # 시작 시간 기록
    start_time = time.time()

    # SQLite 데이터베이스 연결
    initialize_database("filesystem.db")

    # C 코드에서 디렉토리 데이터 가져오기
    file_data_list = get_all_file_data(root)

    id = 1
    # 데이터베이스에 파일 및 디렉토리 정보 삽입
    for file_data in file_data_list:
        path = file_data[0]  # 전체 경로
        name = file_data[1]  # 파일 또는 디렉토리 이름
        is_dir = file_data[2] == b"True"  # 디렉토리 여부 확인

        # 디렉토리인지 파일인지에 따라 테이블에 삽입
        if is_dir:
            # directory_structure 테이블에 디렉토리 정보 삽입
            parent_dir = os.path.dirname(path) if path != root else None
            print(path)
            insert_file_info(id,path,is_dir,"filesystem.db")
            insert_directory_structure(id,path,parent_dir,"filesystem.db")

        else:
            print(path)
            insert_file_info(id, path, is_dir, "filesystem.db")
        id += 1

    # 종료 시간 기록
    end_time = time.time()

    # 걸린 시간 계산
    elapsed_time = end_time - start_time
    print(f"작업에 걸린 시간: {elapsed_time:.4f} 초")

def shell():
    global link_dir

    while True:
        cwd = os.getcwd()
        if link_dir != None and not link_dir.name in cwd:
            link_dir.cleanup()
            link_dir = None
        command = input(f"{cwd} $ ")

        if command.strip().lower() in ["exit", "quit"]:
            print("쉘 종료 중...")
            break
        elif command.strip() == "":
            continue
        else:
            execute_command(command)




if __name__ == "__main__":
    shell()
