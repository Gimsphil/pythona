#!/usr/bin/env python3
"""
pythona - 파이썬 파일(.py)을 바로 실행해 볼 수 있는 프로그램
A program to directly execute Python (.py) files.
"""

import sys
import os
import subprocess
import glob


def find_py_files(directory="."):
    """Find all .py files in the given directory (excluding this file)."""
    current_file = os.path.abspath(__file__)
    py_files = []
    for path in sorted(glob.glob(os.path.join(directory, "*.py"))):
        if os.path.abspath(path) != current_file:
            py_files.append(path)
    return py_files


def run_file(filepath, extra_args=None):
    """Execute the given Python file using the current Python interpreter."""
    # Resolve to absolute path to prevent ambiguity
    abs_path = os.path.realpath(filepath)

    if not os.path.exists(abs_path):
        print(f"오류: 파일을 찾을 수 없습니다 - '{filepath}'")
        return 1

    if not abs_path.endswith(".py"):
        print(f"오류: '.py' 파일만 실행할 수 있습니다 - '{filepath}'")
        return 1

    if not os.path.isfile(abs_path):
        print(f"오류: 디렉토리가 아닌 파일이어야 합니다 - '{filepath}'")
        return 1

    cmd = [sys.executable, abs_path] + (extra_args or [])
    print(f"실행 중: python {os.path.basename(abs_path)}" + (f" {' '.join(extra_args)}" if extra_args else ""))
    print("-" * 40)
    try:
        result = subprocess.run(cmd)
    except PermissionError:
        print(f"오류: 파일 실행 권한이 없습니다 - '{filepath}'")
        return 1
    except OSError as e:
        print(f"오류: 파일을 실행할 수 없습니다 - {e}")
        return 1
    print("-" * 40)
    return result.returncode


def interactive_mode():
    """Let the user choose a .py file from the current directory to run."""
    py_files = find_py_files(".")
    if not py_files:
        print("현재 디렉토리에 실행 가능한 .py 파일이 없습니다.")
        return 1

    print("실행할 파이썬 파일을 선택하세요:")
    for i, filepath in enumerate(py_files, start=1):
        print(f"  {i}. {filepath}")
    print("  0. 종료")

    while True:
        try:
            choice = input("\n번호 입력: ").strip()
            if choice == "0":
                print("종료합니다.")
                return 0
            idx = int(choice) - 1
            if 0 <= idx < len(py_files):
                return run_file(py_files[idx])
            else:
                print(f"1부터 {len(py_files)} 사이의 번호를 입력하세요.")
        except ValueError:
            print("올바른 번호를 입력하세요.")
        except (KeyboardInterrupt, EOFError):
            print("\n종료합니다.")
            return 0


def print_usage():
    prog = os.path.basename(sys.argv[0])
    print(f"사용법: python {prog} [파일.py] [인자...]")
    print()
    print("  파일.py 없이 실행하면 현재 디렉토리의 .py 파일 목록을 보여줍니다.")
    print("  파일.py 를 지정하면 해당 파일을 바로 실행합니다.")
    print()
    print("예시:")
    print(f"  python {prog}                  # 대화형 파일 선택")
    print(f"  python {prog} hello.py         # hello.py 실행")
    print(f"  python {prog} script.py arg1   # script.py를 arg1과 함께 실행")


def main():
    args = sys.argv[1:]

    if args and args[0] in ("-h", "--help"):
        print_usage()
        return 0

    if not args:
        return interactive_mode()

    filepath = args[0]
    extra_args = args[1:]
    return run_file(filepath, extra_args)


if __name__ == "__main__":
    sys.exit(main())
