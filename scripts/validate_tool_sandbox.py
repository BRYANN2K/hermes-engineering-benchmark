#!/usr/bin/env python3
"""Exercise the real Hermes local backend through the benchmark tool hook."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "runtime" / "hermes_tool_sandbox"
SANDBOX = ROOT / "runtime" / "sandbox" / "sandbox-run"
PYTHON = Path("/opt/hermes/.venv/bin/python")
CHILD = r'''
import json, os
from pathlib import Path
from tools.environments.local import LocalEnvironment
from tools.file_operations import ShellFileOperations
w=Path(os.environ['HERMES_WRITE_SAFE_ROOT'])
e=LocalEnvironment(cwd=str(w), timeout=30)
f=ShellFileOperations(e)
write=f.write_file('created.txt','payload-via-stdin\n')
r1=e.execute("export HEB_STATE=kept; printf 'terminal-edit\\n' >> created.txt")
r2=e.execute("printf '%s' \"$HEB_STATE\"")
outside=e.execute("cat /etc/hostname")
network=e.execute("python3 -c 'import socket; socket.socket()'")
read=f.read_file('created.txt')
result={'write_error':write.error,'terminal_rc':r1['returncode'],'state_output':r2['output'].strip(),'outside_rc':outside['returncode'],'network_rc':network['returncode'],'content_has_payload':'payload-via-stdin' in read.content,'content_has_terminal':'terminal-edit' in read.content}
print(json.dumps(result,sort_keys=True))
e.cleanup()
'''
EXPECTED = {"write_error": None, "terminal_rc": 0, "state_output": "kept", "outside_rc": 1, "network_rc": 1, "content_has_payload": True, "content_has_terminal": True}


def main() -> int:
    if not PYTHON.is_file():
        print(json.dumps({"passed": False, "error": f"Hermes Python missing: {PYTHON}"}))
        return 1
    with tempfile.TemporaryDirectory(prefix="heb-hook-", dir="/opt/data") as temp:
        base = Path(temp)
        workspace = base / "workspace"
        workspace.mkdir()
        trace = base / "tool-sandbox.jsonl"
        env = os.environ.copy()
        env.update({"PYTHONPATH": str(HOOK), "HEB_TOOL_SANDBOX": "1", "HEB_SANDBOX_RUN": str(SANDBOX), "HEB_SANDBOX_TRACE": str(trace), "HERMES_WRITE_SAFE_ROOT": str(workspace), "TERMINAL_CWD": str(workspace)})
        completed = subprocess.run([str(PYTHON), "-c", CHILD], cwd=workspace, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError:
            result = None
        trace_lines = trace.read_text(encoding="utf-8").splitlines() if trace.is_file() else []
        hook = '{"sandbox":"hermes-tool-hook","installed":true}'
        marker = '{"sandbox":"landlock-seccomp-netns","activated":true}'
        markers_valid = bool(trace_lines) and trace_lines[0] == hook and set(trace_lines[1:]) == {marker}
        passed = completed.returncode == 0 and result == EXPECTED and markers_valid
        report = {"passed": passed, "returncode": completed.returncode, "checks": result, "trace_lines": len(trace_lines), "trace_markers_valid": markers_valid, "stderr": completed.stderr}
    output = ROOT / "proof" / "hermes-tool-sandbox-integration.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("passed", "returncode", "trace_lines", "trace_markers_valid")}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
