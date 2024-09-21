import os
import subprocess
from fileops import make_soft_links, get_file_data, get_all_file_data


def execute_command(command, link_dir):
    try:
        cmd_parts = command.strip().split()
        if cmd_parts[0] == "mf":
            # file_data, is_image_or_video = get_file_data(cmd_parts[1])
            # print(file_data)
            temp_dir = make_soft_links(
                [
                    "/Users/parksehwan/Documents/MAFM/mafm/shell.py",
                    "/Users/parksehwan/Documents/MAFM/mafm/a.txt",
                ]
            )
            os.chdir(temp_dir)
            # link_dir = temp_dir
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


def shell():
    link_dir = ""
    while True:
        cwd = os.getcwd()
        # if not cwd.startswith(link_dir):
        #     os.remove(link_dir)
        #     link_dir = ""
        command = input(f"{cwd} $ ")

        if command.strip().lower() in ["exit", "quit"]:
            print("쉘 종료 중...")
            break
        elif command.strip() == "":
            continue
        else:
            execute_command(command, link_dir)


if __name__ == "__main__":
    shell()
