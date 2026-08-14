#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/landlock.h>
#include <linux/seccomp.h>
#include <net/if.h>
#include <signal.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

#ifndef LANDLOCK_ACCESS_FS_REFER
#define LANDLOCK_ACCESS_FS_REFER (1ULL << 13)
#endif
#ifndef LANDLOCK_ACCESS_FS_TRUNCATE
#define LANDLOCK_ACCESS_FS_TRUNCATE (1ULL << 14)
#endif
#ifndef LANDLOCK_ACCESS_NET_BIND_TCP
#define LANDLOCK_ACCESS_NET_BIND_TCP (1ULL << 0)
#endif
#ifndef LANDLOCK_ACCESS_NET_CONNECT_TCP
#define LANDLOCK_ACCESS_NET_CONNECT_TCP (1ULL << 1)
#endif
#ifndef LANDLOCK_RULE_NET_PORT
#define LANDLOCK_RULE_NET_PORT 2
#endif
#ifndef __NR_landlock_create_ruleset
#if defined(__x86_64__)
#define __NR_landlock_create_ruleset 444
#define __NR_landlock_add_rule 445
#define __NR_landlock_restrict_self 446
#else
#error "Landlock syscall numbers are only provided here for x86_64"
#endif
#endif
#ifndef __NR_close_range
#define __NR_close_range 436
#endif

struct ruleset_attr_v4 {
    uint64_t handled_access_fs;
    uint64_t handled_access_net;
};

static const uint64_t FS_RO =
    LANDLOCK_ACCESS_FS_EXECUTE |
    LANDLOCK_ACCESS_FS_READ_FILE |
    LANDLOCK_ACCESS_FS_READ_DIR;

static const uint64_t FS_RW =
    LANDLOCK_ACCESS_FS_EXECUTE |
    LANDLOCK_ACCESS_FS_WRITE_FILE |
    LANDLOCK_ACCESS_FS_READ_FILE |
    LANDLOCK_ACCESS_FS_READ_DIR |
    LANDLOCK_ACCESS_FS_REMOVE_DIR |
    LANDLOCK_ACCESS_FS_REMOVE_FILE |
    LANDLOCK_ACCESS_FS_MAKE_DIR |
    LANDLOCK_ACCESS_FS_MAKE_REG |
    LANDLOCK_ACCESS_FS_MAKE_SOCK |
    LANDLOCK_ACCESS_FS_MAKE_FIFO |
    LANDLOCK_ACCESS_FS_MAKE_SYM |
    LANDLOCK_ACCESS_FS_REFER |
    LANDLOCK_ACCESS_FS_TRUNCATE;

static void die(const char *what) {
    fprintf(stderr, "sandbox: %s: %s\n", what, strerror(errno));
    exit(125);
}

static void usage(const char *argv0) {
    fprintf(stderr, "usage: %s WORKSPACE [--ro PATH ...] -- COMMAND [ARG ...]\n", argv0);
    exit(125);
}

static int ll_create(const void *attr, size_t size, uint32_t flags) {
    return (int)syscall(__NR_landlock_create_ruleset, attr, size, flags);
}

static int ll_add(int fd, enum landlock_rule_type type, const void *attr, uint32_t flags) {
    return (int)syscall(__NR_landlock_add_rule, fd, type, attr, flags);
}

static int ll_restrict(int fd, uint32_t flags) {
    return (int)syscall(__NR_landlock_restrict_self, fd, flags);
}

static void add_path_rule(int ruleset_fd, const char *path, uint64_t rights, int required) {
    struct stat st;
    int path_fd = open(path, O_PATH | O_CLOEXEC);
    if (path_fd < 0) {
        if (!required && errno == ENOENT)
            return;
        die(path);
    }
    if (fstat(path_fd, &st) < 0)
        die("fstat allowlisted path");
    if (!S_ISDIR(st.st_mode))
        rights &= LANDLOCK_ACCESS_FS_EXECUTE |
                  LANDLOCK_ACCESS_FS_READ_FILE |
                  LANDLOCK_ACCESS_FS_WRITE_FILE |
                  LANDLOCK_ACCESS_FS_TRUNCATE;
    struct landlock_path_beneath_attr rule = {
        .allowed_access = rights,
        .parent_fd = path_fd,
    };
    if (ll_add(ruleset_fd, LANDLOCK_RULE_PATH_BENEATH, &rule, 0) < 0)
        die(path);
    close(path_fd);
}

#define DENY_SYSCALL(nr) \
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, (nr), 0, 1), \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))

static void enable_loopback(void) {
    int fd = socket(AF_INET, SOCK_DGRAM | SOCK_CLOEXEC, 0);
    if (fd < 0)
        die("open loopback control socket");
    struct ifreq request = {0};
    strncpy(request.ifr_name, "lo", IFNAMSIZ - 1);
    if (ioctl(fd, SIOCGIFFLAGS, &request) < 0)
        die("read loopback flags");
    request.ifr_flags |= IFF_UP | IFF_RUNNING;
    if (ioctl(fd, SIOCSIFFLAGS, &request) < 0)
        die("enable loopback");
    close(fd);
}

static void install_seccomp(int allow_loopback) {
    struct sock_filter filter[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
#ifdef __NR_clone
        /* Allow ordinary processes/threads, but not creation of new namespaces. */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_clone, 0, 4),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, args[0])),
        BPF_STMT(BPF_ALU | BPF_AND | BPF_K, 0x7e020080U),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 0, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA)),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
#endif
#ifdef __NR_clone3
        /* Classic BPF cannot inspect clone3's pointed-to flags. Report ENOSYS
         * so libc safely falls back to filtered legacy clone for subprocesses. */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_clone3, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (ENOSYS & SECCOMP_RET_DATA)),
#endif
#ifdef __NR_socket
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_socket, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, allow_loopback ? SECCOMP_RET_ALLOW :
                 (SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))),
#endif
#ifdef __NR_socketpair
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_socketpair, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, allow_loopback ? SECCOMP_RET_ALLOW :
                 (SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))),
#endif
#ifdef __NR_connect
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_connect, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, allow_loopback ? SECCOMP_RET_ALLOW :
                 (SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))),
#endif
#ifdef __NR_bind
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_bind, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, allow_loopback ? SECCOMP_RET_ALLOW :
                 (SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))),
#endif
#ifdef __NR_listen
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_listen, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, allow_loopback ? SECCOMP_RET_ALLOW :
                 (SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))),
#endif
#ifdef __NR_accept
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_accept, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, allow_loopback ? SECCOMP_RET_ALLOW :
                 (SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))),
#endif
#ifdef __NR_accept4
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_accept4, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, allow_loopback ? SECCOMP_RET_ALLOW :
                 (SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))),
#endif
#ifdef __NR_sendto
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_sendto, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, allow_loopback ? SECCOMP_RET_ALLOW :
                 (SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))),
#endif
#ifdef __NR_sendmsg
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_sendmsg, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, allow_loopback ? SECCOMP_RET_ALLOW :
                 (SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))),
#endif
#ifdef __NR_sendmmsg
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_sendmmsg, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, allow_loopback ? SECCOMP_RET_ALLOW :
                 (SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))),
#endif
#ifdef __NR_recvmsg
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_recvmsg, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, allow_loopback ? SECCOMP_RET_ALLOW :
                 (SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))),
#endif
#ifdef __NR_recvmmsg
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_recvmmsg, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, allow_loopback ? SECCOMP_RET_ALLOW :
                 (SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))),
#endif
#ifdef __NR_mount
        DENY_SYSCALL(__NR_mount),
#endif
#ifdef __NR_umount2
        DENY_SYSCALL(__NR_umount2),
#endif
#ifdef __NR_pivot_root
        DENY_SYSCALL(__NR_pivot_root),
#endif
#ifdef __NR_move_mount
        DENY_SYSCALL(__NR_move_mount),
#endif
#ifdef __NR_open_tree
        DENY_SYSCALL(__NR_open_tree),
#endif
#ifdef __NR_fsopen
        DENY_SYSCALL(__NR_fsopen),
#endif
#ifdef __NR_fsconfig
        DENY_SYSCALL(__NR_fsconfig),
#endif
#ifdef __NR_fsmount
        DENY_SYSCALL(__NR_fsmount),
#endif
#ifdef __NR_mount_setattr
        DENY_SYSCALL(__NR_mount_setattr),
#endif
#ifdef __NR_setns
        DENY_SYSCALL(__NR_setns),
#endif
#ifdef __NR_unshare
        DENY_SYSCALL(__NR_unshare),
#endif
#ifdef __NR_chmod
        DENY_SYSCALL(__NR_chmod),
#endif
#ifdef __NR_fchmod
        DENY_SYSCALL(__NR_fchmod),
#endif
#ifdef __NR_fchmodat
        DENY_SYSCALL(__NR_fchmodat),
#endif
#ifdef __NR_fchmodat2
        DENY_SYSCALL(__NR_fchmodat2),
#endif
#ifdef __NR_chown
        DENY_SYSCALL(__NR_chown),
#endif
#ifdef __NR_fchown
        DENY_SYSCALL(__NR_fchown),
#endif
#ifdef __NR_lchown
        DENY_SYSCALL(__NR_lchown),
#endif
#ifdef __NR_fchownat
        DENY_SYSCALL(__NR_fchownat),
#endif
#ifdef __NR_utime
        DENY_SYSCALL(__NR_utime),
#endif
#ifdef __NR_utimes
        DENY_SYSCALL(__NR_utimes),
#endif
#ifdef __NR_futimesat
        DENY_SYSCALL(__NR_futimesat),
#endif
#ifdef __NR_utimensat
        DENY_SYSCALL(__NR_utimensat),
#endif
#ifdef __NR_setxattr
        DENY_SYSCALL(__NR_setxattr),
#endif
#ifdef __NR_lsetxattr
        DENY_SYSCALL(__NR_lsetxattr),
#endif
#ifdef __NR_fsetxattr
        DENY_SYSCALL(__NR_fsetxattr),
#endif
#ifdef __NR_removexattr
        DENY_SYSCALL(__NR_removexattr),
#endif
#ifdef __NR_lremovexattr
        DENY_SYSCALL(__NR_lremovexattr),
#endif
#ifdef __NR_fremovexattr
        DENY_SYSCALL(__NR_fremovexattr),
#endif
#ifdef __NR_mknod
        DENY_SYSCALL(__NR_mknod),
#endif
#ifdef __NR_mknodat
        DENY_SYSCALL(__NR_mknodat),
#endif
#ifdef __NR_io_uring_setup
        DENY_SYSCALL(__NR_io_uring_setup),
#endif
#ifdef __NR_bpf
        DENY_SYSCALL(__NR_bpf),
#endif
#ifdef __NR_perf_event_open
        DENY_SYSCALL(__NR_perf_event_open),
#endif
#ifdef __NR_userfaultfd
        DENY_SYSCALL(__NR_userfaultfd),
#endif
#ifdef __NR_open_by_handle_at
        DENY_SYSCALL(__NR_open_by_handle_at),
#endif
#ifdef __NR_ptrace
        DENY_SYSCALL(__NR_ptrace),
#endif
#ifdef __NR_process_vm_readv
        DENY_SYSCALL(__NR_process_vm_readv),
#endif
#ifdef __NR_process_vm_writev
        DENY_SYSCALL(__NR_process_vm_writev),
#endif
#ifdef __NR_pidfd_getfd
        DENY_SYSCALL(__NR_pidfd_getfd),
#endif
#ifdef __NR_keyctl
        DENY_SYSCALL(__NR_keyctl),
#endif
#ifdef __NR_add_key
        DENY_SYSCALL(__NR_add_key),
#endif
#ifdef __NR_request_key
        DENY_SYSCALL(__NR_request_key),
#endif
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog prog = {
        .len = (unsigned short)(sizeof(filter) / sizeof(filter[0])),
        .filter = filter,
    };
    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog) < 0)
        die("PR_SET_SECCOMP");
}

int main(int argc, char **argv) {
    if (argc < 4)
        usage(argv[0]);

    int abi = ll_create(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION);
    if (abi < 4) {
        if (abi < 0)
            die("query Landlock ABI");
        fprintf(stderr, "sandbox: Landlock ABI %d is too old; ABI >= 4 required\n", abi);
        return 125;
    }

    char *workspace = realpath(argv[1], NULL);
    if (!workspace)
        die("realpath workspace");
    struct stat workspace_st;
    if (stat(workspace, &workspace_st) < 0 || !S_ISDIR(workspace_st.st_mode)) {
        errno = ENOTDIR;
        die("workspace");
    }

    struct stat stdio_st;
    int allow_stdin_pipe = getenv("SANDBOX_ALLOW_STDIN_PIPE") != NULL &&
                           strcmp(getenv("SANDBOX_ALLOW_STDIN_PIPE"), "1") == 0;
    if (fstat(STDIN_FILENO, &stdio_st) < 0 ||
        !(S_ISCHR(stdio_st.st_mode) || (allow_stdin_pipe && S_ISFIFO(stdio_st.st_mode)))) {
        errno = EINVAL;
        die("stdin must be /dev/null-like character device or an explicitly allowed pipe");
    }
    for (int fd = STDOUT_FILENO; fd <= STDERR_FILENO; fd++) {
        if (fstat(fd, &stdio_st) < 0 || !S_ISFIFO(stdio_st.st_mode)) {
            errno = EINVAL;
            die("stdout and stderr must be pipes");
        }
    }

    int sep = 2;
    while (sep < argc && strcmp(argv[sep], "--") != 0) {
        if (strcmp(argv[sep], "--ro") != 0 || sep + 1 >= argc)
            usage(argv[0]);
        sep += 2;
    }
    if (sep >= argc - 1)
        usage(argv[0]);

    int allow_loopback = getenv("SANDBOX_ALLOW_LOOPBACK") != NULL &&
                         strcmp(getenv("SANDBOX_ALLOW_LOOPBACK"), "1") == 0;

    struct ruleset_attr_v4 ruleset = {
        .handled_access_fs = FS_RW |
            LANDLOCK_ACCESS_FS_MAKE_CHAR |
            LANDLOCK_ACCESS_FS_MAKE_BLOCK,
        .handled_access_net = allow_loopback ? 0 :
            (LANDLOCK_ACCESS_NET_BIND_TCP | LANDLOCK_ACCESS_NET_CONNECT_TCP),
    };
    int ruleset_fd = ll_create(&ruleset, sizeof(ruleset), 0);
    if (ruleset_fd < 0)
        die("create Landlock ruleset");

    add_path_rule(ruleset_fd, workspace, FS_RW, 1);
    add_path_rule(ruleset_fd, "/usr", FS_RO, 0);
    add_path_rule(ruleset_fd, "/bin", FS_RO, 0);
    add_path_rule(ruleset_fd, "/lib", FS_RO, 0);
    add_path_rule(ruleset_fd, "/lib64", FS_RO, 0);
    add_path_rule(ruleset_fd, "/etc/ld.so.cache", LANDLOCK_ACCESS_FS_READ_FILE, 0);
    add_path_rule(ruleset_fd, "/etc/ld.so.preload", LANDLOCK_ACCESS_FS_READ_FILE, 0);
    add_path_rule(ruleset_fd, "/dev/null", LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_WRITE_FILE, 0);
    add_path_rule(ruleset_fd, "/dev/zero", LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_WRITE_FILE, 0);
    add_path_rule(ruleset_fd, "/dev/random", LANDLOCK_ACCESS_FS_READ_FILE, 0);
    add_path_rule(ruleset_fd, "/dev/urandom", LANDLOCK_ACCESS_FS_READ_FILE, 0);
    add_path_rule(ruleset_fd, argv[sep + 1], FS_RO, 1);

    for (int i = 2; i < sep; i += 2)
        add_path_rule(ruleset_fd, argv[i + 1], FS_RO, 1);

    const char *env_ro = getenv("SANDBOX_RO_PATHS");
    if (env_ro && *env_ro) {
        char *paths = strdup(env_ro);
        if (!paths)
            die("strdup SANDBOX_RO_PATHS");
        char *saveptr = NULL;
        for (char *path = strtok_r(paths, ":", &saveptr);
             path;
             path = strtok_r(NULL, ":", &saveptr))
            add_path_rule(ruleset_fd, path, FS_RO, 1);
        free(paths);
    }
    if (unsetenv("SANDBOX_RO_PATHS") < 0)
        die("unsetenv SANDBOX_RO_PATHS");
    if (unsetenv("SANDBOX_ALLOW_LOOPBACK") < 0)
        die("unsetenv SANDBOX_ALLOW_LOOPBACK");
    if (unsetenv("SANDBOX_ALLOW_STDIN_PIPE") < 0)
        die("unsetenv SANDBOX_ALLOW_STDIN_PIPE");

    if (chdir(workspace) < 0)
        die("chdir workspace");

    if (prctl(PR_SET_DUMPABLE, 0, 0, 0, 0) < 0)
        die("PR_SET_DUMPABLE");
    if (prctl(PR_SET_PDEATHSIG, SIGKILL, 0, 0, 0) < 0)
        die("PR_SET_PDEATHSIG");
    for (int cap = 0; cap < 64; cap++) {
        if (prctl(PR_CAPBSET_DROP, cap, 0, 0, 0) < 0 && errno != EINVAL && errno != EPERM)
            die("PR_CAPBSET_DROP");
    }

    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0)
        die("PR_SET_NO_NEW_PRIVS");
    if (ll_restrict(ruleset_fd, 0) < 0)
        die("restrict with Landlock");

    /* Do not let inherited descriptors bypass path-based confinement. */
    if (syscall(__NR_close_range, 3U, ~0U, 0U) < 0)
        die("close_range");

    if (allow_loopback)
        enable_loopback();
    install_seccomp(allow_loopback);
    execv(argv[sep + 1], &argv[sep + 1]);
    die("exec command");
}
