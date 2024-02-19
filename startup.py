import sys, os

from utils import *

# if 'colorama' in sys.modules: # and 'WT_SESSION' in os.environ:
#     import colorama
#     colorama.deinit()
#     del colorama

# Fix slow long lines in IDLE
# if sys.stdout.__class__.__module__.split('.')[0] == 'idlelib':
#    from breaklonglines import BreakLongLines
#    sys.stdout = BreakLongLines(sys.stdout)
#    del BreakLongLines

if sys.version_info < (3, 4):
    # from site.py
    def register_readline():
        import atexit
        try:
            import readline
            import rlcompleter
        except ImportError:
            return
        readline_doc = getattr(readline, '__doc__', '')
        if readline_doc is not None and 'libedit' in readline_doc:
            readline.parse_and_bind('bind ^I rl_complete')
        else:
            readline.parse_and_bind('tab: complete')
        try:
            readline.read_init_file()
        except OSError:
            pass
        if readline.get_current_history_length() == 0:
            history = os.path.join(os.path.expanduser('~'), '.python_history')
            try:
                readline.read_history_file(history)
            except OSError:
                pass
            def write_history():
                try:
                    readline.write_history_file(history)
                except (FileNotFoundError, PermissionError):
                    pass
            atexit.register(write_history)

    register_readline()
