import sys, subprocess

def main():
    guid = subprocess.check_output(['powercfg', '-getactivescheme'],
                                   universal_newlines=True).split()[3]

    args = sys.argv[1:]
    if '-h' in args or '--help' in args or len(args) not in (1, 2):
        print('''\
useage: closelid.py BATTERY CHARGING

values:
Do nothing: 0
Sleep: 1
Hibernate: 2
Shut down: 3
''')

        lines = subprocess.check_output(
            ['powercfg', '-query', guid, 'sub_buttons'],
            universal_newlines=True).splitlines()
        oldac, olddc = [int(lines[n].split()[-1], 16) for n in (14, 15)]
        print('current settings:', olddc, oldac)
        return

    dcval = args[0]
    acval = args[1] if len(args) == 2 else dcval

    subprocess.call(['powercfg', '-setdcvalueindex', guid, 'sub_buttons',
                     'lidaction', dcval])
    subprocess.call(['powercfg', '-setacvalueindex', guid, 'sub_buttons',
                     'lidaction', acval])
    subprocess.call(['powercfg', '-setactive', guid])

if __name__ == '__main__':
    main()
