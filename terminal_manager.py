from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import subprocess
import threading
import uuid


@dataclass
class TerminalSession:
    session_id: str
    namespace: str
    pod: str
    container: str | None
    shell: str
    process: subprocess.Popen[str]
    output_lines: deque[str] = field(default_factory=lambda: deque(maxlen=400))
    history: list[str] = field(default_factory=list)
    is_open: bool = True
    error: str | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)


class TerminalManager:
    def __init__(self, kubectl_binary: str = "kubectl") -> None:
        self.kubectl_binary = kubectl_binary
        self.sessions: dict[str, TerminalSession] = {}
        self._lock = threading.Lock()

    def open_session(
        self,
        namespace: str,
        pod: str,
        context: str | None = None,
        container: str | None = None,
        shell: str = "/bin/sh",
    ) -> tuple[str | None, str | None]:
        session_id = str(uuid.uuid4())
        command = [self.kubectl_binary, "exec", "-i", "-n", namespace, pod]
        if container:
            command.extend(["-c", container])
        if context:
            command.extend(["--context", context])
        command.extend(["--", shell])

        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            return None, "kubectl is not installed or not on PATH."
        except OSError as exc:
            return None, str(exc)

        session = TerminalSession(
            session_id=session_id,
            namespace=namespace,
            pod=pod,
            container=container,
            shell=shell,
            process=process,
        )
        with self._lock:
            self.sessions[session_id] = session

        thread = threading.Thread(target=self._read_output, args=(session_id,), daemon=True)
        thread.start()
        self.send_command(session_id, "pwd")
        return session_id, None

    def _read_output(self, session_id: str) -> None:
        session = self.sessions.get(session_id)
        if not session or not session.process.stdout:
            return

        try:
            for line in iter(session.process.stdout.readline, ""):
                with session.lock:
                    session.output_lines.append(line.rstrip("\n"))
            session.process.wait(timeout=1)
        except Exception as exc:  # noqa: BLE001
            session.error = str(exc)
        finally:
            session.is_open = False

    def send_command(self, session_id: str, command: str) -> str | None:
        session = self.sessions.get(session_id)
        if not session:
            return "Terminal session not found."
        if not session.is_open or not session.process.stdin:
            return "Terminal session is closed."

        try:
            session.process.stdin.write(f"{command}\n")
            session.process.stdin.flush()
            with session.lock:
                session.history.append(command)
            return None
        except OSError as exc:
            session.is_open = False
            return str(exc)

    def get_output(self, session_id: str) -> str:
        session = self.sessions.get(session_id)
        if not session:
            return ""
        with session.lock:
            return "\n".join(session.output_lines)

    def get_history(self, session_id: str) -> list[str]:
        session = self.sessions.get(session_id)
        if not session:
            return []
        with session.lock:
            return list(session.history)

    def close_session(self, session_id: str) -> str | None:
        session = self.sessions.get(session_id)
        if not session:
            return "Terminal session not found."

        if session.process.stdin and session.is_open:
            try:
                session.process.stdin.write("exit\n")
                session.process.stdin.flush()
            except OSError:
                pass
        session.process.terminate()
        session.is_open = False
        return None

    def status(self, session_id: str) -> tuple[bool, str | None]:
        session = self.sessions.get(session_id)
        if not session:
            return False, "Terminal session not found."
        if session.error:
            return False, session.error
        if session.process.poll() is not None:
            session.is_open = False
        return session.is_open, None
