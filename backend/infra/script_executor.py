"""
Executor de Scripts — camada de Infra.

Isola toda interação com o sistema operacional via subprocess.
Detecta automaticamente o interpretador Bash disponível no host.
Em ambientes Windows sem Bash, executa em modo simulado (demo).
"""
from __future__ import annotations
import os
import platform
import shutil
import subprocess
import time
from dataclasses import dataclass

# Locais comuns do bash no Windows (Git Bash, Cygwin, WSL)
_WINDOWS_BASH_CANDIDATES = [
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
    r"C:\msys64\usr\bin\bash.exe",
    r"C:\cygwin64\bin\bash.exe",
]


def _find_bash() -> str | None:
    """Retorna o caminho do bash disponível, ou None se não encontrado."""
    found = shutil.which("bash")
    if found:
        return found
    if platform.system() == "Windows":
        for candidate in _WINDOWS_BASH_CANDIDATES:
            if os.path.isfile(candidate):
                return candidate
    return None


BASH = _find_bash()


@dataclass
class ExecutionResult:
    status: str      # "success" | "error" | "timeout"
    stdout: str
    stderr: str
    duration_ms: int


class ScriptExecutor:
    def run(
        self,
        script_path: str,
        params: list[str],
        timeout: int = 120,
    ) -> ExecutionResult:
        if not os.path.isfile(script_path):
            return ExecutionResult(
                status="error",
                stdout="",
                stderr=f"Arquivo de script não encontrado: {script_path}",
                duration_ms=0,
            )

        # Sem Bash disponível → modo simulado (útil para demo no Windows)
        if BASH is None:
            return self._simulate(script_path, params)

        start = time.monotonic()
        try:
            proc = subprocess.run(
                [BASH, script_path] + params,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            ms = int((time.monotonic() - start) * 1000)
            return ExecutionResult(
                status="success" if proc.returncode == 0 else "error",
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=ms,
            )
        except subprocess.TimeoutExpired:
            ms = int((time.monotonic() - start) * 1000)
            return ExecutionResult(
                status="timeout",
                stdout="",
                stderr=f"Script excedeu o timeout configurado de {timeout}s.",
                duration_ms=ms,
            )
        except Exception as exc:
            ms = int((time.monotonic() - start) * 1000)
            return ExecutionResult(
                status="error",
                stdout="",
                stderr=str(exc),
                duration_ms=ms,
            )

    @staticmethod
    def _simulate(script_path: str, params: list[str]) -> ExecutionResult:
        """Execução simulada para ambientes Windows sem Bash instalado."""
        import time as _time
        _time.sleep(0.4)  # simula latência real
        script_name = os.path.basename(script_path)
        params_str  = " ".join(params) if params else "—"
        stdout = (
            f"========================================\n"
            f" IsyShell — {script_name} [MODO DEMO]\n"
            f"========================================\n"
            f"Parâmetros : {params_str}\n"
            f"----------------------------------------\n"
            f"[INFO] Bash não encontrado no host Windows.\n"
            f"[INFO] Executando em modo simulado para demonstração.\n"
            f"[INFO] Em produção (Linux/Docker), o script real é executado.\n"
            f"----------------------------------------\n"
            f"SUCESSO: rotina '{script_name}' simulada com êxito.\n"
            f"STATUS: SUCCESS · exit code 0\n"
        )
        return ExecutionResult(
            status="success",
            stdout=stdout,
            stderr="",
            duration_ms=400,
        )
