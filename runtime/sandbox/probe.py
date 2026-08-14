#!/usr/bin/env python3
import errno
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

workspace = Path.cwd()
hidden = Path(sys.argv[1])
outside_target = Path(sys.argv[2])
runtime_asset = Path(sys.argv[3])
results = {}


def record(name, ok, detail):
    results[name] = {"ok": bool(ok), "detail": str(detail)}


def must_be_denied(name, operation, extra_errnos=()):
    try:
        operation()
    except OSError as exc:
        record(
            name,
            exc.errno in (errno.EACCES, errno.EPERM, *extra_errnos),
            f"errno={exc.errno} {exc.strerror}",
        )
    else:
        record(name, False, "unexpected success")


try:
    (workspace / "edited.txt").write_text("workspace edit succeeded\n", encoding="utf-8")
    with (workspace / "edited.txt").open("a", encoding="utf-8") as handle:
        handle.write("append succeeded\n")
    (workspace / "made-dir").mkdir(exist_ok=True)
    (workspace / "rename-source").write_text("rename", encoding="utf-8")
    (workspace / "rename-source").rename(workspace / "rename-destination")
    record("workspace_mutation", True, "create+append+mkdir+rename succeeded")
except OSError as exc:
    record("workspace_mutation", False, f"errno={exc.errno} {exc.strerror}")

must_be_denied("hidden_read", lambda: hidden.read_bytes())
must_be_denied("hidden_directory_list", lambda: list(hidden.parent.iterdir()))
must_be_denied("host_read_etc", lambda: Path("/etc/passwd").read_bytes())
must_be_denied("outside_write", lambda: outside_target.write_text("escape", encoding="utf-8"))
must_be_denied("outside_unlink", hidden.unlink)
must_be_denied("outside_chmod", lambda: hidden.chmod(0o644))
must_be_denied("workspace_chmod", lambda: (workspace / "edited.txt").chmod(0o600))
must_be_denied(
    "outside_hardlink",
    lambda: os.link(hidden, workspace / "hardlink-to-hidden"),
    (errno.EXDEV,),
)
must_be_denied(
    "outside_rename",
    lambda: (workspace / "rename-destination").rename(outside_target),
)

try:
    runtime_value = runtime_asset.read_text(encoding="utf-8").strip()
    record("runtime_read", runtime_value == "RUNTIME_ASSET", repr(runtime_value))
except OSError as exc:
    record("runtime_read", False, f"errno={exc.errno} {exc.strerror}")
must_be_denied(
    "runtime_write",
    lambda: runtime_asset.write_text("modified", encoding="utf-8"),
)
must_be_denied("runtime_unlink", runtime_asset.unlink)

symlink = workspace / "symlink-to-hidden"
try:
    symlink.unlink(missing_ok=True)
    symlink.symlink_to(hidden)
    try:
        symlink.read_bytes()
    except OSError as exc:
        record("symlink_escape_read", exc.errno in (errno.EACCES, errno.EPERM), f"errno={exc.errno} {exc.strerror}")
    else:
        record("symlink_escape_read", False, "unexpected success")
except OSError as exc:
    record("symlink_escape_read", False, f"fixture error errno={exc.errno} {exc.strerror}")

must_be_denied("inet_socket", lambda: socket.socket(socket.AF_INET, socket.SOCK_STREAM))
must_be_denied("inet6_socket", lambda: socket.socket(socket.AF_INET6, socket.SOCK_DGRAM))
must_be_denied("unix_socket", lambda: socket.socket(socket.AF_UNIX, socket.SOCK_STREAM))
must_be_denied("socketpair", socket.socketpair)

try:
    completed = subprocess.run(
        ["/bin/sh", "-c", "printf subprocess-ok > subprocess-edit.txt"],
        check=False,
        capture_output=True,
        text=True,
    )
    record(
        "subprocess_workspace_edit",
        completed.returncode == 0 and (workspace / "subprocess-edit.txt").read_text() == "subprocess-ok",
        f"exit={completed.returncode}",
    )
except OSError as exc:
    record("subprocess_workspace_edit", False, f"errno={exc.errno} {exc.strerror}")

try:
    completed = subprocess.run(
        ["/usr/bin/unshare", "--user", "true"],
        check=False,
        capture_output=True,
        text=True,
    )
    record("nested_namespace_escape", completed.returncode != 0, f"exit={completed.returncode}")
except OSError as exc:
    record("nested_namespace_escape", exc.errno in (errno.EACCES, errno.EPERM), f"errno={exc.errno} {exc.strerror}")

try:
    import ctypes

    libc_for_clone = ctypes.CDLL(None, use_errno=True)
    child = libc_for_clone.syscall(56, 0x10000000 | 17, 0, 0, 0, 0)  # clone(CLONE_NEWUSER|SIGCHLD)
    clone_errno = ctypes.get_errno()
    if child == 0:
        os._exit(99)
    if child > 0:
        os.waitpid(child, 0)
    record("clone_namespace_escape", child == -1 and clone_errno == errno.EPERM, f"result={child} errno={clone_errno}")
except Exception as exc:
    record("clone_namespace_escape", False, repr(exc))

try:
    import ctypes

    libc_for_clone3 = ctypes.CDLL(None, use_errno=True)
    clone3_result = libc_for_clone3.syscall(435, 0, 0)
    clone3_errno = ctypes.get_errno()
    record(
        "clone3_disabled",
        clone3_result == -1 and clone3_errno == errno.ENOSYS,
        f"result={clone3_result} errno={clone3_errno}",
    )
except Exception as exc:
    record("clone3_disabled", False, repr(exc))

try:
    import ctypes

    libc = ctypes.CDLL(None, use_errno=True)
    nnp = libc.prctl(39, 0, 0, 0, 0)  # PR_GET_NO_NEW_PRIVS
    seccomp = libc.prctl(21, 0, 0, 0, 0)  # PR_GET_SECCOMP
    class CapHeader(ctypes.Structure):
        _fields_ = [("version", ctypes.c_uint32), ("pid", ctypes.c_int)]

    class CapData(ctypes.Structure):
        _fields_ = [
            ("effective", ctypes.c_uint32),
            ("permitted", ctypes.c_uint32),
            ("inheritable", ctypes.c_uint32),
        ]

    header = CapHeader(0x20080522, 0)  # _LINUX_CAPABILITY_VERSION_3
    data = (CapData * 2)()
    capget_result = libc.syscall(125, ctypes.byref(header), ctypes.byref(data))
    cap_effective = data[0].effective | (data[1].effective << 32)
    cap_permitted = data[0].permitted | (data[1].permitted << 32)
    record(
        "kernel_guards_active",
        (
            nnp == 1
            and seccomp == 2
            and capget_result == 0
            and cap_effective == 0
            and cap_permitted == 0
            # uid 0 is expected inside a root-mapped user namespace. With no
            # effective/permitted capabilities it is not host root.
            and (os.geteuid() != 0 or (cap_effective == 0 and cap_permitted == 0))
        ),
        (
            f"no_new_privs={nnp} seccomp_mode={seccomp} "
            f"cap_effective=0x{cap_effective:x} cap_permitted=0x{cap_permitted:x} "
            f"euid={os.geteuid()}"
        ),
    )
except Exception as exc:
    record("kernel_guards_active", False, repr(exc))

try:
    os.fstat(9)
except OSError as exc:
    record("inherited_fd_closed", exc.errno == errno.EBADF, f"errno={exc.errno} {exc.strerror}")
else:
    record("inherited_fd_closed", False, "fd 9 unexpectedly inherited")

allowed_env = {"HOME", "LC_ALL", "PATH", "TMPDIR"}
unexpected_env = sorted(set(os.environ) - allowed_env)
record("environment_scrubbed", not unexpected_env, f"unexpected={unexpected_env}")

all_ok = all(item["ok"] for item in results.values())
try:
    hidden_stat = hidden.stat()
    metadata_limitation = (
        "Landlock does not mediate stat(2): hidden inode metadata remains visible "
        f"when the exact path is known (size={hidden_stat.st_size}, mode={oct(hidden_stat.st_mode & 0o777)})."
    )
except OSError as exc:
    metadata_limitation = f"hidden stat failed with errno={exc.errno} {exc.strerror}"

print(
    json.dumps(
        {"all_ok": all_ok, "limitations_observed": [metadata_limitation], "results": results},
        indent=2,
        sort_keys=True,
    )
)
sys.exit(0 if all_ok else 1)
