/* Qualification-only fault injection for a launched process. The original cache
 * files stay regular, unchanged files; only their read calls receive a delay. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

ssize_t read(int fd, void *buffer, size_t count) {
    ssize_t (*original)(int, void *, size_t) = dlsym(RTLD_NEXT, "read");
    char descriptor[64], path[4096];
    snprintf(descriptor, sizeof descriptor, "/proc/self/fd/%d", fd);
    ssize_t length = readlink(descriptor, path, sizeof path - 1);
    if (length >= 0) {
        path[length] = '\0';
        if (strstr(path, "/frames/frame-") && strstr(path, ".mpc")) {
            const char *setting = getenv("MAELSTROM_QUALIFY_READ_DELAY_US");
            unsigned long delay = setting ? strtoul(setting, NULL, 10) : 100000;
            if (delay > 1000000) delay = 1000000;
            struct timespec remaining = { delay / 1000000, (delay % 1000000) * 1000 };
            while (nanosleep(&remaining, &remaining) && errno == EINTR) {}
        }
    }
    return original(fd, buffer, count);
}
