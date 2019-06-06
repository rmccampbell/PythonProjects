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
            for tok in tokens:
                if tok == '|':
                    tok_groups.append(tok_group)
                    tok_group = []
                else:
                    tok_group.append(tok)
            if tok_group:
                tok_groups.append(tok_group)

            pids = []
            read_pipe = None
            for i, tok_group in enumerate(tok_groups):
                if not tok_group:
                    continue
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
                        os.dup2(os.open(stdin, os.O_RDONLY), 0)
                    if write_pipe:
                        os.close(next_read_pipe)
                        os.dup2(write_pipe, 1)
                    elif stdout:
                        os.dup2(os.open(stdout, os.O_WRONLY|os.O_CREAT), 1)
                    os.execv(file, args)
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
            for status in statuses:
                print(status, file=sys.stderr)

        except KeyboardInterrupt:
            pass
