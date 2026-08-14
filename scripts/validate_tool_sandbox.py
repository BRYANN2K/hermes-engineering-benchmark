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
from hermes_cli import auth as auth_mod
from run_agent import AIAgent
from tools.environments.local import LocalEnvironment
from tools.file_operations import ShellFileOperations

# Verify atomic refresh writes and advisory locking remain on one shared
# host-only store rather than replacing a per-run auth symlink.
shared_auth=Path(os.environ['HEB_SHARED_AUTH_FILE']).resolve()
auth_path_shared=auth_mod._auth_file_path()==shared_auth
auth_lock_shared=auth_mod._auth_lock_path()==shared_auth.with_suffix('.lock')
saved_path=auth_mod._save_auth_store({'providers':{}})
atomic_auth_shared=saved_path==shared_auth and shared_auth.is_file()
ephemeral_auth_absent=not (Path(os.environ['HERMES_HOME'])/'auth.json').exists()

# Capture the kwargs applied by the installed constructor wrapper without
# initializing provider/network state.
captured={}
wrapped=AIAgent.__init__
closure=[cell.cell_contents for cell in (wrapped.__closure__ or ())]
original=next(value for value in closure if callable(value) and value is not wrapped)
def capture(self,*args,**kwargs):
    captured.update(kwargs)
    return None
for cell in (wrapped.__closure__ or ()):
    if cell.cell_contents is original:
        import ctypes
        ctypes.pythonapi.PyCell_Set.argtypes=(ctypes.py_object,ctypes.py_object)
        ctypes.pythonapi.PyCell_Set(cell,capture)
        break
wrapped(object())
w=Path(os.environ['HERMES_WRITE_SAFE_ROOT'])
e=LocalEnvironment(cwd=str(w), timeout=30)
f=ShellFileOperations(e)
write=f.write_file('created.txt','payload-via-stdin\n')
r1=e.execute("export HEB_STATE=kept; printf 'terminal-edit\\n' >> created.txt")
r2=e.execute("printf '%s' \"$HEB_STATE\"")
outside=e.execute("cat /etc/hostname")
network=e.execute("python3 -c 'import socket; socket.socket()'")
secret=e.execute("test -z \"${OPENCODE_GO_API_KEY-}\" && test -z \"${HEB_SHARED_AUTH_FILE-}\"")
read=f.read_file('created.txt')
result={'write_error':write.error,'terminal_rc':r1['returncode'],'state_output':r2['output'].strip(),'outside_rc':outside['returncode'],'network_rc':network['returncode'],'secret_absent_rc':secret['returncode'],'content_has_payload':'payload-via-stdin' in read.content,'content_has_terminal':'terminal-edit' in read.content,'auth_path_shared':auth_path_shared,'auth_lock_shared':auth_lock_shared,'atomic_auth_shared':atomic_auth_shared,'ephemeral_auth_absent':ephemeral_auth_absent,'cognitive_flags':{k:captured.get(k) for k in ('skip_memory','skip_context_files','load_soul_identity','fallback_model')}}
print(json.dumps(result,sort_keys=True))
e.cleanup()
'''
EXPECTED = {"write_error": None, "terminal_rc": 0, "state_output": "kept", "outside_rc": 1, "network_rc": 1, "secret_absent_rc": 0, "content_has_payload": True, "content_has_terminal": True, "auth_path_shared": True, "auth_lock_shared": True, "atomic_auth_shared": True, "ephemeral_auth_absent": True, "cognitive_flags": {"skip_memory": True, "skip_context_files": True, "load_soul_identity": False, "fallback_model": None}}


def main() -> int:
    if not PYTHON.is_file():
        print(json.dumps({"passed": False, "error": f"Hermes Python missing: {PYTHON}"}))
        return 1
    with tempfile.TemporaryDirectory(prefix="heb-hook-", dir="/opt/data") as temp:
        base = Path(temp)
        workspace = base / "workspace"
        workspace.mkdir()
        fake_auth = base / "auth.json"
        fake_auth.write_text('{"version":1}\n', encoding="utf-8")
        trace = base / "tool-sandbox.jsonl"
        env = os.environ.copy()
        env.update({"PYTHONPATH": str(HOOK), "HEB_TOOL_SANDBOX": "1", "HEB_SANDBOX_RUN": str(SANDBOX), "HEB_SANDBOX_TRACE": str(trace), "HEB_SHARED_AUTH_FILE": str(fake_auth), "HERMES_HOME": str(base / "ephemeral-home"), "HERMES_WRITE_SAFE_ROOT": str(workspace), "TERMINAL_CWD": str(workspace)})
        completed = subprocess.run([str(PYTHON), "-c", CHILD], cwd=workspace, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError:
            result = None
        trace_lines = trace.read_text(encoding="utf-8").splitlines() if trace.is_file() else []
        records = [json.loads(line) for line in trace_lines]
        hook_valid = bool(records) and records[0].get("cognitive_isolation_installed") is True
        cognitive_valid = len([r for r in records if r.get("sandbox") == "hermes-cognitive-isolation" and r.get("applied") is True]) == 1
        kernel_valid = bool([r for r in records if r == {"sandbox":"landlock-seccomp-netns","activated":True}])
        markers_valid = hook_valid and cognitive_valid and kernel_valid
        passed = completed.returncode == 0 and result == EXPECTED and markers_valid
        report = {"passed": passed, "returncode": completed.returncode, "checks": result, "trace_lines": len(trace_lines), "trace_markers_valid": markers_valid, "stderr": completed.stderr}
    output = ROOT / "proof" / "hermes-tool-sandbox-integration.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("passed", "returncode", "trace_lines", "trace_markers_valid")}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
