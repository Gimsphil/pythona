import os
import sys
import time
import queue
import threading
import subprocess
import shutil
import py_compile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "PythonA Runner"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(APP_DIR, "assets", "icons")
ICON_ICO_PATH = os.path.join(ICON_DIR, "오아시스_로고01.ico")
ICON_PNG_PATH = os.path.join(ICON_DIR, "오아시스_로고01.png")
AUTHOR_NAME = "PHIL JK"
AUTHOR_EMAIL = "kacang@nate.com"
AUTHOR_HP = "+62 812 8094 3179"


class PythonARunner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1380x860")
        self.minsize(1100, 700)
        self._icon_image = None
        self._configure_icon()

        self.current_file = None
        self.current_folder = None
        self.process = None
        self.reader_threads = []
        self.output_queue = queue.Queue()
        self.last_bug_text = "버그 정보가 없습니다."
        self.run_started_at = None
        self.last_output_at = None
        self.last_heartbeat_at = None
        self.run_stdout_chunks = []
        self.run_stderr_chunks = []
        self.tree_nodes = {}

        self._build_ui()
        self._build_menu()
        self._bind_shortcuts()

        self.after(100, self._drain_output_queue)
        self.after(400, self._tick_runtime)

        arg_file = self._startup_file_from_args()
        if arg_file:
            self.open_file(arg_file)
            self.after(300, self.run_current_file)

    def _startup_file_from_args(self):
        if len(sys.argv) < 2:
            return None
        candidate = os.path.abspath(sys.argv[1])
        if os.path.isfile(candidate) and candidate.lower().endswith('.py'):
            return candidate
        return None

    def _build_ui(self):
        outer = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        outer.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(outer)
        right = ttk.PanedWindow(outer, orient=tk.VERTICAL)
        outer.add(left, weight=1)
        outer.add(right, weight=4)

        folder_bar = ttk.Frame(left)
        folder_bar.pack(fill=tk.X, padx=6, pady=6)
        ttk.Button(folder_bar, text="폴더 불러오기", command=self.choose_folder).pack(side=tk.LEFT)

        self.tree = ttk.Treeview(left, show='tree')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
        self.tree.bind('<<TreeviewOpen>>', self._on_tree_open)
        self.tree.bind('<Double-1>', self._on_tree_double_click)

        editor_frame = ttk.Frame(right)
        output_frame = ttk.Frame(right)
        right.add(editor_frame, weight=3)
        right.add(output_frame, weight=2)

        editor_top = ttk.Frame(editor_frame)
        editor_top.pack(fill=tk.X, padx=6, pady=6)
        self.file_label = ttk.Label(editor_top, text="파일: (없음)")
        self.file_label.pack(side=tk.LEFT)

        self.editor = tk.Text(editor_frame, wrap=tk.NONE, undo=True)
        self.editor.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        output_top = ttk.Frame(output_frame)
        output_top.pack(fill=tk.X, padx=6, pady=6)
        ttk.Button(output_top, text="실행", command=self.run_current_file).pack(side=tk.LEFT)
        ttk.Button(output_top, text="중지", command=self.stop_run).pack(side=tk.LEFT, padx=6)
        ttk.Button(output_top, text="출력 지우기", command=self.clear_output).pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(output_top, mode="indeterminate", length=180)
        self.progress.pack(side=tk.LEFT, padx=8)

        info_text = f"작성자: {AUTHOR_NAME} | e-Mail: {AUTHOR_EMAIL} | H/P: {AUTHOR_HP}"
        self.author_label = ttk.Label(output_top, text=info_text)
        self.author_label.pack(side=tk.LEFT, padx=14)

        self.status_label = ttk.Label(output_top, text="상태: 대기")
        self.status_label.pack(side=tk.RIGHT)

        self.output = tk.Text(output_frame, wrap=tk.NONE, bg="#0c1117", fg="#cfe6ff")
        self.output.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

    def _build_menu(self):
        m = tk.Menu(self)

        file_menu = tk.Menu(m, tearoff=0)
        file_menu.add_command(label="파일 불러오기", command=self.choose_file)
        file_menu.add_command(label="폴더 불러오기", command=self.choose_folder)
        file_menu.add_separator()
        file_menu.add_command(label="저장", command=self.save_file)
        file_menu.add_command(label="다른 이름으로 저장", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.destroy)
        m.add_cascade(label="파일", menu=file_menu)

        run_menu = tk.Menu(m, tearoff=0)
        run_menu.add_command(label="실행", command=self.run_current_file)
        run_menu.add_command(label="중지", command=self.stop_run)
        run_menu.add_command(label="출력 지우기", command=self.clear_output)
        m.add_cascade(label="실행", menu=run_menu)

        bug_menu = tk.Menu(m, tearoff=0)
        bug_menu.add_command(label="버그내용", command=self.show_bug_details)
        bug_menu.add_command(label="버그내용 복사", command=self.copy_bug_details)
        m.add_cascade(label="버그", menu=bug_menu)

        help_menu = tk.Menu(m, tearoff=0)
        help_menu.add_command(label="작성자 정보", command=self.show_author_info)
        m.add_cascade(label="도움말", menu=help_menu)

        self.config(menu=m)

    def _bind_shortcuts(self):
        self.bind('<Control-o>', lambda e: self.choose_file())
        self.bind('<Control-s>', lambda e: self.save_file())
        self.bind('<Control-Shift-S>', lambda e: self.save_file_as())
        self.bind('<F5>', lambda e: self.run_current_file())
        self.bind('<Shift-F5>', lambda e: self.stop_run())

    def _configure_icon(self):
        if os.path.isfile(ICON_ICO_PATH):
            try:
                self.iconbitmap(default=ICON_ICO_PATH)
            except Exception:
                pass

        if os.path.isfile(ICON_PNG_PATH):
            try:
                self._icon_image = tk.PhotoImage(file=ICON_PNG_PATH)
                self.iconphoto(True, self._icon_image)
            except Exception:
                pass

    def _now(self):
        return time.strftime("%H:%M:%S")

    def _log_event(self, label, message):
        self._append_output(f"[{self._now()}] [{label}] {message}\n")

    def _pick_auto_open_file(self, folder):
        candidates = ["main.py", "app.py", "run.py", "start.py", "launcher.py"]
        for name in candidates:
            full = os.path.join(folder, name)
            if os.path.isfile(full):
                return full

        py_files = []
        try:
            for name in os.listdir(folder):
                full = os.path.join(folder, name)
                if os.path.isfile(full) and name.lower().endswith(".py"):
                    py_files.append(full)
        except Exception:
            return None

        py_files.sort(key=lambda p: os.path.basename(p).lower())
        return py_files[0] if py_files else None

    def choose_file(self):
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if path:
            self.open_file(path)

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.current_folder = os.path.abspath(folder)
        self._load_tree(self.current_folder)

        auto_file = self._pick_auto_open_file(self.current_folder)
        if auto_file:
            self.open_file(auto_file)
            self._log_event("AUTO OPEN", auto_file)
        else:
            self._log_event("AUTO OPEN", "실행 가능한 .py 파일을 찾지 못했습니다.")

    def _load_tree(self, root_path):
        self.tree.delete(*self.tree.get_children())
        self.tree_nodes.clear()
        root_id = self.tree.insert('', 'end', text=os.path.basename(root_path) or root_path, open=True, values=(root_path,))
        self.tree_nodes[root_id] = root_path
        self._add_tree_placeholder(root_id, root_path)

    def _add_tree_placeholder(self, parent_id, path):
        try:
            entries = sorted(os.listdir(path), key=lambda n: (not os.path.isdir(os.path.join(path, n)), n.lower()))
        except Exception:
            return
        has_children = False
        for name in entries:
            full = os.path.join(path, name)
            if os.path.isdir(full) or full.lower().endswith('.py'):
                has_children = True
                break
        if has_children:
            self.tree.insert(parent_id, 'end', text='__placeholder__')

    def _on_tree_open(self, _evt):
        item = self.tree.focus()
        if not item:
            return
        path = self._item_path(item)
        if not path or not os.path.isdir(path):
            return
        children = self.tree.get_children(item)
        if len(children) == 1 and self.tree.item(children[0], 'text') == '__placeholder__':
            self.tree.delete(children[0])
            self._populate_tree(item, path)

    def _populate_tree(self, parent_id, path):
        try:
            entries = sorted(os.listdir(path), key=lambda n: (not os.path.isdir(os.path.join(path, n)), n.lower()))
        except Exception as e:
            self._log_event("TREE ERROR", str(e))
            return
        for name in entries:
            full = os.path.join(path, name)
            if os.path.isdir(full):
                node = self.tree.insert(parent_id, 'end', text=name, values=(full,))
                self.tree_nodes[node] = full
                self._add_tree_placeholder(node, full)
            elif full.lower().endswith('.py'):
                node = self.tree.insert(parent_id, 'end', text=name, values=(full,))
                self.tree_nodes[node] = full

    def _on_tree_double_click(self, _evt):
        item = self.tree.focus()
        if not item:
            return
        path = self._item_path(item)
        if path and os.path.isfile(path) and path.lower().endswith('.py'):
            self.open_file(path)

    def _item_path(self, item_id):
        vals = self.tree.item(item_id, 'values')
        if vals:
            return vals[0]
        return self.tree_nodes.get(item_id)

    def open_file(self, path):
        path = os.path.abspath(path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = f.read()
        except UnicodeDecodeError:
            with open(path, 'r', encoding='cp949', errors='replace') as f:
                data = f.read()
        except Exception as e:
            messagebox.showerror("오류", f"파일을 열 수 없습니다.\n{e}")
            return

        self.current_file = path
        self.current_folder = os.path.dirname(path)
        self.editor.delete('1.0', tk.END)
        self.editor.insert('1.0', data)
        self.file_label.config(text=f"파일: {path}")
        self.status_label.config(text="상태: 파일 로드 완료")

        if self.current_folder:
            self._load_tree(self.current_folder)

    def save_file(self):
        if not self.current_file:
            return self.save_file_as()
        return self._write_current_buffer(self.current_file)

    def save_file_as(self):
        target = filedialog.asksaveasfilename(defaultextension='.py', filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if not target:
            return False
        ok = self._write_current_buffer(target)
        if ok:
            self.current_file = os.path.abspath(target)
            self.file_label.config(text=f"파일: {self.current_file}")
        return ok

    def _write_current_buffer(self, target):
        data = self.editor.get('1.0', tk.END)
        try:
            with open(target, 'w', encoding='utf-8') as f:
                f.write(data)
            self.status_label.config(text=f"상태: 저장 완료 ({target})")
            return True
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패\n{e}")
            return False

    def run_current_file(self):
        if self.process and self.process.poll() is None:
            messagebox.showwarning("안내", "이미 실행 중입니다. 먼저 중지하세요.")
            return
        if not self.current_file:
            messagebox.showwarning("안내", "먼저 .py 파일을 불러오세요.")
            return
        if not os.path.isfile(self.current_file):
            reason = f"실행 파일을 찾을 수 없습니다: {self.current_file}"
            self._log_event("ERROR", reason)
            self.status_label.config(text="상태: 실행 실패")
            self.last_bug_text = f"[실행 실패 이유]\n{reason}"
            messagebox.showerror("실행 실패 사유", reason)
            return
        if not self.save_file():
            return

        self.last_bug_text = "버그 정보가 없습니다."
        self.run_stdout_chunks = []
        self.run_stderr_chunks = []
        self.clear_output()

        cwd = os.path.dirname(self.current_file)

        self.status_label.config(text="상태: 실행 준비 중")
        self._log_event("STEP", "실행 준비 시작")
        syntax_ok, syntax_msg = self._check_syntax(self.current_file)
        if not syntax_ok:
            self.status_label.config(text="상태: 실행 실패(문법 오류)")
            self._log_event("ERROR", syntax_msg)
            self.last_bug_text = syntax_msg + "\n\n[수정 팁]\nTraceback의 라인 번호를 편집기에서 수정 후 F5로 다시 실행하세요."
            messagebox.showerror("실행 실패 사유", syntax_msg)
            return

        if os.name == "nt":
            ps_exe = "powershell.exe"
            if shutil.which(ps_exe) is None:
                reason = "PowerShell 실행 파일을 찾을 수 없습니다. (powershell.exe)"
                self._log_event("ERROR", reason)
                self.status_label.config(text="상태: 실행 실패")
                self.last_bug_text = f"[실행 실패 이유]\n{reason}"
                messagebox.showerror("실행 실패 사유", reason)
                return
            ps_cmd = f"& '{sys.executable}' '{self.current_file}'"
            cmd = [ps_exe, "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]
            self._log_event("TERMINAL", "PowerShell 실행 모드")
        else:
            if shutil.which(sys.executable) is None:
                reason = f"Python 실행 파일을 찾을 수 없습니다: {sys.executable}"
                self._log_event("ERROR", reason)
                self.status_label.config(text="상태: 실행 실패")
                self.last_bug_text = f"[실행 실패 이유]\n{reason}"
                messagebox.showerror("실행 실패 사유", reason)
                return
            cmd = [sys.executable, self.current_file]
            self._log_event("TERMINAL", "Python 직접 실행 모드(비-Windows)")

        self._log_event("RUN", " ".join(cmd))
        self._log_event("CWD", cwd)
        self._append_output("\n")

        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
            )
        except Exception as e:
            reason = f"프로세스 시작 실패: {e}"
            self._log_event("ERROR", reason)
            self.last_bug_text = f"[실행 실패 이유]\n{reason}"
            messagebox.showerror("실행 실패 사유", reason)
            self.status_label.config(text="상태: 실행 실패")
            return

        self.run_started_at = time.time()
        self.last_output_at = self.run_started_at
        self.last_heartbeat_at = self.run_started_at
        self.status_label.config(text="상태: 실행 중")
        self.progress.start(10)
        self._log_event("STEP", "프로세스 시작 완료. 실시간 출력 수집 중")

        t_out = threading.Thread(target=self._reader_worker, args=(self.process.stdout, 'STDOUT'), daemon=True)
        t_err = threading.Thread(target=self._reader_worker, args=(self.process.stderr, 'STDERR'), daemon=True)
        t_wait = threading.Thread(target=self._wait_worker, daemon=True)
        self.reader_threads = [t_out, t_err, t_wait]
        for t in self.reader_threads:
            t.start()

    def _reader_worker(self, stream, tag):
        try:
            for line in iter(stream.readline, ''):
                self.output_queue.put((tag, line))
        finally:
            try:
                stream.close()
            except Exception:
                pass

    def _wait_worker(self):
        code = self.process.wait()
        self.output_queue.put(('EXIT', code))

    def _build_bug_report(self, reason):
        lines = self.run_stderr_chunks + self.run_stdout_chunks
        trace = []
        in_tb = False
        for line in lines:
            if 'Traceback (most recent call last):' in line:
                in_tb = True
                trace = [line]
                continue
            if in_tb:
                trace.append(line)

        if trace:
            bug_body = '\n'.join(trace[-30:])
        else:
            bug_body = '\n'.join(lines[-30:]) if lines else reason

        hint = (
            f"[실행 실패 이유]\n{reason}\n\n"
            "[수정 팁]\n"
            "1) VS Code/Cursor/Antigravity에서 마지막 Traceback의 파일/라인을 열어 수정하세요.\n"
            "2) 수정 후 이 프로그램에서 F5로 재실행하세요.\n"
            "3) 무한루프/멈춤이면 Shift+F5(중지)를 누르세요.\n"
        )
        self.last_bug_text = bug_body + "\n\n" + hint

    def stop_run(self):
        if not self.process or self.process.poll() is not None:
            self.status_label.config(text="상태: 실행 중인 프로세스 없음")
            return
        try:
            self.process.terminate()
            self.after(1200, self._kill_if_alive)
            self._log_event("STOP", "terminate 요청 전송")
            self.status_label.config(text="상태: 중지 요청됨")
        except Exception as e:
            self._log_event("STOP ERROR", str(e))

    def _kill_if_alive(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.kill()
                self._log_event("STOP", "강제 종료(kill) 완료")
                self.status_label.config(text="상태: 강제 종료됨")
            except Exception as e:
                self._log_event("STOP ERROR", f"강제 종료 실패: {e}")

    def clear_output(self):
        self.output.delete('1.0', tk.END)

    def _append_output(self, text):
        self.output.insert(tk.END, text)
        self.output.see(tk.END)

    def _drain_output_queue(self):
        while True:
            try:
                tag, chunk = self.output_queue.get_nowait()
            except queue.Empty:
                break

            if tag == 'STDOUT':
                self.run_stdout_chunks.append(chunk.rstrip("\n"))
                self.last_output_at = time.time()
                self._append_output(chunk)
            elif tag == 'STDERR':
                self.run_stderr_chunks.append(chunk.rstrip("\n"))
                self.last_output_at = time.time()
                self._append_output(f"[ERR] {chunk}")
            elif tag == 'EXIT':
                self._handle_process_exit(int(chunk))

        self.after(100, self._drain_output_queue)

    def _tick_runtime(self):
        if self.process and self.process.poll() is None and self.run_started_at:
            elapsed = int(time.time() - self.run_started_at)
            self.status_label.config(text=f"상태: 실행 중 ({elapsed}s)")
            if self.last_output_at and (time.time() - self.last_output_at) > 5:
                if not self.last_heartbeat_at or (time.time() - self.last_heartbeat_at) > 5:
                    self._log_event("PROGRESS", f"실행 중... ({elapsed}s, 출력 대기)")
                    self.last_heartbeat_at = time.time()
        self.after(400, self._tick_runtime)

    def _check_syntax(self, path):
        try:
            py_compile.compile(path, doraise=True)
            return True, "OK"
        except py_compile.PyCompileError as e:
            return False, f"문법 오류: {e.msg}"
        except Exception as e:
            return False, f"문법 검사 실패: {e}"

    def _handle_process_exit(self, code):
        self.progress.stop()
        reason = self._exit_reason(code)
        self._append_output(f"\n[{self._now()}] [EXIT] return code = {code}\n")
        self._log_event("RESULT", reason)
        if code == 0:
            self.status_label.config(text="상태: 실행 완료(성공)")
            self.last_bug_text = "버그 정보가 없습니다. 마지막 실행은 성공했습니다."
        else:
            self.status_label.config(text="상태: 실행 실패")
            self._build_bug_report(reason)
            fail_summary = self._failure_summary(reason)
            self._log_event("FAIL SUMMARY", fail_summary.replace("\n", " | "))
            messagebox.showerror("실행 실패 사유", fail_summary)

    def _exit_reason(self, code):
        err_text = "\n".join(self.run_stderr_chunks[-60:])
        if "No such file or directory" in err_text:
            return "실행 경로 또는 대상 파일이 없어 실행 실패했습니다."
        if "is not recognized as an internal or external command" in err_text:
            return "필수 명령(파이썬/PowerShell)을 찾지 못해 실행 실패했습니다."
        if code == -15:
            return "사용자 중지(terminate)로 종료되었습니다."
        if code == -9:
            return "강제 종료(kill)되었습니다."
        if "SyntaxError" in err_text:
            return "문법 오류(SyntaxError)로 실행 실패했습니다."
        if "ModuleNotFoundError" in err_text:
            return "모듈 누락(ModuleNotFoundError)으로 실행 실패했습니다."
        if "PermissionError" in err_text:
            return "권한 문제(PermissionError)로 실행 실패했습니다."
        if "FileNotFoundError" in err_text:
            return "파일 경로 문제(FileNotFoundError)로 실행 실패했습니다."
        if "NameError" in err_text:
            return "정의되지 않은 변수/함수(NameError)로 실행 실패했습니다."
        if "TypeError" in err_text:
            return "타입 오류(TypeError)로 실행 실패했습니다."
        if "ValueError" in err_text:
            return "값 오류(ValueError)로 실행 실패했습니다."
        if err_text.strip():
            return "예외 발생으로 실행 실패했습니다. stderr를 확인하세요."
        return "비정상 종료(return code != 0)되었습니다."

    def _failure_summary(self, reason):
        tail_err = "\n".join(self.run_stderr_chunks[-8:]).strip()
        tail_out = "\n".join(self.run_stdout_chunks[-5:]).strip()
        parts = [f"실행 실패 이유: {reason}"]
        if tail_err:
            parts.append(f"[최근 STDERR]\n{tail_err}")
        elif tail_out:
            parts.append(f"[최근 출력]\n{tail_out}")
        return "\n\n".join(parts)

    def show_bug_details(self):
        messagebox.showinfo("버그내용", self.last_bug_text)

    def copy_bug_details(self):
        self.clipboard_clear()
        self.clipboard_append(self.last_bug_text)
        self.update()
        self.status_label.config(text="상태: 버그내용 클립보드 복사 완료")

    def show_author_info(self):
        message = (
            f"작성자 : {AUTHOR_NAME}\n"
            f"e-Mail : {AUTHOR_EMAIL}\n"
            f"H/P : {AUTHOR_HP}"
        )
        messagebox.showinfo("작성자 정보", message)


if __name__ == '__main__':
    app = PythonARunner()
    app.mainloop()
