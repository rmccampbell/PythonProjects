import dis, types, functools, inspect

def implicit_self(func, paramname='self'):
    (LOAD_FAST, STORE_FAST, DELETE_FAST,
     LOAD_GLOBAL, STORE_GLOBAL, DELETE_GLOBAL) = [dis.opmap[n] for n in
        ('LOAD_FAST', 'STORE_FAST', 'DELETE_FAST',
         'LOAD_GLOBAL', 'STORE_GLOBAL', 'DELETE_GLOBAL')]

    opchanges = {LOAD_GLOBAL: LOAD_FAST, STORE_GLOBAL: STORE_FAST,
                 DELETE_GLOBAL: DELETE_FAST}

    code = func.__code__
    bytecode = bytearray(code.co_code)

    if code.co_argcount >= 255:
        raise ValueError('Function has too many parameters.')

    #index of self in co_varnames
    try:
        selfi = code.co_varnames.index(paramname)
    except ValueError:
        selfi = len(code.co_varnames)
        varnames = (paramname,) + code.co_varnames
        nlocals = code.co_nlocals + 1
    else:
        varnames = (paramname,) + code.co_varnames[:selfi] + \
                   code.co_varnames[selfi+1:]
        nlocals = code.co_nlocals

    index = 0
    while index < len(bytecode):
        op = bytecode[index]

        if op in opchanges:
            oparg = int.from_bytes(bytecode[index+1:index+3], 'little')
            if code.co_names[oparg] == paramname:
                bytecode[index] = opchanges[op]
                bytecode[index+1:index+3] = (0).to_bytes(2, 'little')

        elif op in (LOAD_FAST, STORE_FAST, DELETE_FAST):
            oparg = int.from_bytes(bytecode[index+1:index+3], 'little')
            if oparg == selfi:
                bytecode[index+1:index+3] = (0).to_bytes(2, 'little')
            elif oparg < selfi:
                bytecode[index+1:index+3] = (oparg + 1).to_bytes(2, 'little')

        if op < dis.HAVE_ARGUMENT:
            index += 1
        else:
            index += 3

    code = types.CodeType(code.co_argcount + 1,
                          code.co_kwonlyargcount,
                          nlocals,
                          code.co_stacksize,
                          code.co_flags,
                          bytes(bytecode),
                          code.co_consts,
                          code.co_names,
                          varnames,
                          code.co_filename,
                          code.co_name,
                          code.co_firstlineno,
                          code.co_lnotab,
                          code.co_freevars,
                          code.co_cellvars)
    func.__code__ = code
    return func

##    func2 = types.FunctionType(code, func.__globals__,
##                               argdefs=func.__defaults__,
##                               closure=func.__closure__)
##    func2.__kwdefaults__ = func.__kwdefaults__
##    functools.update_wrapper(func2, func)
##    del func2.__wrapped__
##    return func2


def implicit_this(func):
    return implicit_self(func, 'this')

def implicit_first_param(paramname='self'):
    return functools.partial(implicit_self, paramname=paramname)

