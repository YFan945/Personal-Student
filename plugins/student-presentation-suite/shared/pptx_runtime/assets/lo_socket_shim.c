#define _GNU_SOURCE

#include <dlfcn.h>
#include <errno.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define TRACKED_FDS 4096

static int (*next_socket)(int, int, int);
static int (*next_socketpair)(int, int, int, int[2]);
static int (*next_listen)(int, int);
static int (*next_accept)(int, struct sockaddr *, socklen_t *);
static int (*next_close)(int);
static ssize_t (*next_read)(int, void *, size_t);

static unsigned char tracked[TRACKED_FDS];
static int peer_fd[TRACKED_FDS];
static int wake_read[TRACKED_FDS];
static int wake_write[TRACKED_FDS];

__attribute__((constructor)) static void initialize(void) {
    next_socket = dlsym(RTLD_NEXT, "socket");
    next_socketpair = dlsym(RTLD_NEXT, "socketpair");
    next_listen = dlsym(RTLD_NEXT, "listen");
    next_accept = dlsym(RTLD_NEXT, "accept");
    next_close = dlsym(RTLD_NEXT, "close");
    next_read = dlsym(RTLD_NEXT, "read");
    for (int index = 0; index < TRACKED_FDS; ++index) {
        peer_fd[index] = -1;
        wake_read[index] = -1;
        wake_write[index] = -1;
    }
}

int socket(int domain, int type, int protocol) {
    const char *force_denial = getenv("PPTX_RUNTIME_TEST_DENY_AF_UNIX");
    int result;
    if (domain == AF_UNIX && force_denial != NULL && strcmp(force_denial, "1") == 0) {
        errno = EPERM;
        result = -1;
    } else {
        result = next_socket(domain, type, protocol);
    }
    if (result >= 0 || domain != AF_UNIX || (errno != EPERM && errno != EACCES)) {
        return result;
    }
    int pair[2];
    if (next_socketpair(AF_UNIX, type, protocol, pair) != 0) {
        return -1;
    }
    if (pair[0] < 0 || pair[0] >= TRACKED_FDS) {
        next_close(pair[0]);
        next_close(pair[1]);
        errno = EMFILE;
        return -1;
    }
    int wake[2];
    if (pipe(wake) != 0) {
        next_close(pair[0]);
        next_close(pair[1]);
        return -1;
    }
    tracked[pair[0]] = 1;
    peer_fd[pair[0]] = pair[1];
    wake_read[pair[0]] = wake[0];
    wake_write[pair[0]] = wake[1];
    return pair[0];
}

int listen(int descriptor, int backlog) {
    if (descriptor >= 0 && descriptor < TRACKED_FDS && tracked[descriptor]) {
        (void)backlog;
        return 0;
    }
    return next_listen(descriptor, backlog);
}

int accept(int descriptor, struct sockaddr *address, socklen_t *length) {
    if (descriptor >= 0 && descriptor < TRACKED_FDS && tracked[descriptor]) {
        char signal_byte;
        (void)address;
        (void)length;
        if (wake_read[descriptor] >= 0) {
            (void)next_read(wake_read[descriptor], &signal_byte, 1);
        }
        errno = ECONNABORTED;
        return -1;
    }
    return next_accept(descriptor, address, length);
}

int close(int descriptor) {
    if (descriptor >= 0 && descriptor < TRACKED_FDS && tracked[descriptor]) {
        tracked[descriptor] = 0;
        if (wake_write[descriptor] >= 0) {
            char signal_byte = 0;
            ssize_t written = write(wake_write[descriptor], &signal_byte, 1);
            (void)written;
            next_close(wake_write[descriptor]);
            wake_write[descriptor] = -1;
        }
        if (wake_read[descriptor] >= 0) {
            next_close(wake_read[descriptor]);
            wake_read[descriptor] = -1;
        }
        if (peer_fd[descriptor] >= 0) {
            next_close(peer_fd[descriptor]);
            peer_fd[descriptor] = -1;
        }
    }
    return next_close(descriptor);
}
