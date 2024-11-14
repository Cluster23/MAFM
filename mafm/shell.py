import os
import subprocess
import tempfile
import time
from rag.fileops import make_soft_links, get_file_data
from rag.sqlite import (
    initialize_database,
    insert_file_info,
    insert_directory_structure,
)
from rag.vectorDb import (
    initialize_vector_db,
    save,
)
from rag.embedding import initialize_model
from agent.graph import graph


link_dir = None


def execute_command(command, root_dir):
    global link_dir

    # temp_dir_path 지정
    temp_dir_path = os.path.join(os.getcwd(), "temp")

    # temp 디렉토리가 없으면 생성
    if not os.path.exists(temp_dir_path):
        os.makedirs(temp_dir_path)

    try:
        cmd_parts = command.strip().split()
        if cmd_parts[0] == "mlink":
            if len(cmd_parts) < 2:
                print("mlink: missing arguments. Usage: mlink <query>")
                return

            prompt = " ".join(cmd_parts[1:])
            paths = graph(root_dir, prompt)

            # 임시 디렉토리 생성
            temp_dir = tempfile.TemporaryDirectory(dir=temp_dir_path)

            # 소프트 링크 생성
            result = make_soft_links(paths, temp_dir)
            print(f"Soft links created: {result}")

            # 디렉토리 변경 및 링크 디렉토리 갱신
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

        else:
            result = subprocess.run(cmd_parts, check=True)
            return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
    except FileNotFoundError:
        print(f"Command not found: {command}")


def shell(root_dir: str):
    global link_dir

    initialize_model()  # embedding 모델 초기화
    print("model")

    # # root 위치에서부터 MAFM을 활성화
    # # /Users 아래에 존재하는 모든 디렉토리들을 관리할 수 있으면 좋겠지만, 일단 프로토타입이기 때문에 depth를 최소화
    # try:
    #     # 해당 root 아래에 존재하는 모든 파일들을 탐색해서 sqlite db에 저장해야함.
    #     # start_command_python(root_dir)
    #     start_command_c(root_dir)
    #     # get_file_data(root)
    # except IndexError:
    #     print("start: missing argument")
    # except FileNotFoundError:
    #     print(f"start: no such file or directory: {root_dir}")

    while True:
        cwd = os.getcwd()
        if link_dir != None and not link_dir.name in cwd:
            link_dir.cleanup()
            link_dir = None
        command = input(f"{cwd} $ ")
        command = command.encode("utf-8").decode("utf-8")

        if command.strip().lower() in ["exit", "quit"]:
            print("쉘 종료 중...")
            break
        elif command.strip() == "":
            continue
        else:
            execute_command(command, root_dir)


import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MAFM shell")
    parser.add_argument("-r", "--root", help="Root directory path")
    args = parser.parse_args()

    if not args.root:
        print("Root directory path is required.")
    else:
        shell(args.root)
