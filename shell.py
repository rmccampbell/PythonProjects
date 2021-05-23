#!/usr/bin/env python3

import sys, os

PROMPT = '>'

if __name__ == '__main__':
    running = True
    while running:
        try:
            line = input(PROMPT)
        except EOFError:
            break
        try:
            tokens = line.split()
            tok_groups = []
            tok_group = []
            tok = None
            for tok in tokens:
                if tok == '|':
                    if not tok_group:
                        print('error: empty token group', file=sys.stderr)
                        tok_groups = []
                        break
                    tok_groups.append(tok_group)
                    tok_group = []
                else:
                    tok_group.append(tok)
            if tok_group:
                tok_groups.append(tok_group)
            elif tok_groups and tok == '|':
                print('error: empty token group', file=sys.stderr)
                tok_groups = []
            if not tok_groups:
                continue

            files = []
            pids = []
            read_pipe = None
            for i, tok_group in enumerate(tok_groups):
                file = tok_group[0]
                if file == 'exit':
                    running = False
                    break
                args = []
                stdin = stdout = None
                for j, arg in enumerate(tok_group):
                    if arg == '>':
                        stdout = tok_group.pop(j+1)
                    elif arg == '<':
                        stdin = tok_group.pop(j+1)
                    else:
                        args.append(arg)
                next_read_pipe = write_pipe = None
                if i < len(tok_groups)-1:
                    next_read_pipe, write_pipe = os.pipe()
                pid = os.fork()
                if pid == 0:
                    if read_pipe:
                        os.dup2(read_pipe, 0)
                    elif stdin:
                        fd = os.open(stdin, os.O_RDONLY)
                        os.dup2(fd, 0)
                    if write_pipe:
                        os.close(next_read_pipe)
                        os.dup2(write_pipe, 1)
                    elif stdout:
                        fd = os.open(stdout, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
                        os.dup2(fd, 1)
                    os.execv(file, args)
                files.append(file)
                pids.append(pid)
                if read_pipe:
                    os.close(read_pipe)
                if write_pipe:
                    os.close(write_pipe)
                read_pipe = next_read_pipe

            statuses = []
            for pid in pids:
                pid, status = os.waitpid(pid, 0)
                statuses.append(os.WEXITSTATUS(status))
            for file, status in zip(files, statuses):
                print('%s exited with exit code %d' % (file, status))

        except KeyboardInterrupt:
            pass
