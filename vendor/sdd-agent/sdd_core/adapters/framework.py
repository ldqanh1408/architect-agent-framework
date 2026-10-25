from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from ..model import SddError


class FrameworkAdapter:
    """Explicit parent boundary; no parent import or sys.path mutation in core."""
    def __init__(self, root):
        self.root = Path(root).resolve()

    def capabilities(self):
        expected = {"gates": "architect_framework/gates/runner.py", "registry": "contracts/gates.yml",
                    "cli": "architect_framework/cli/main.py"}
        present = {key: (self.root / value).exists() for key, value in expected.items()}
        present["skills"] = (self.root / "exported_skills").exists() or (self.root / "skills").exists()
        return {"status": "PASS" if all(present.values()) else "INCOMPLETE", "capabilities": present,
                "root": str(self.root)}

    def gate(self, workspace, gate_id=None):
        capabilities = self.capabilities()
        if capabilities["status"] != "PASS":
            raise SddError("FRAMEWORK_CAPABILITY_MISSING", str(capabilities))
        command = [sys.executable, "-m", "architect_framework.cli.main", "gate", "run"]
        command += [gate_id] if gate_id else ["--scope", "workspace"]
        command.append(str(Path(workspace).resolve()))
        try:
            process = subprocess.run(command, cwd=self.root, capture_output=True, text=True, timeout=120, encoding="utf-8")
        except subprocess.TimeoutExpired as exc:
            raise SddError("FRAMEWORK_GATE_TIMEOUT", "Parent gate exceeded its deadline") from exc
        return {"command": command, "exit_code": process.returncode, "stdout": process.stdout,
                "stderr": process.stderr, "status": "PASS" if process.returncode == 0 else "FAIL"}
