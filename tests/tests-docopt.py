#!/usr/bin/python

"""Set preferences for a virtual machine domain.

Usage:
  qvm.prefs [--force-root] [--strict] <vmname> <action>
            [--label=<color>]
            [--template NAME]
            [--netvm SERVICEVM]
            [--memory=<n>]
            [--maxmem=<n>]
            [--vcpus=<n>]
            [--include-in-backups=<bool>]
            [--autostart=<bool>]
            [--default-user NAME]
            [--mac MAC]
            [--timezone TIMEZONE]
            [--pcidevs DEVICES]
            [--kernel KERNEL]
            [--kernelopts OPTS_STRING]
            [--drive DRIVE]
            [--seamless-gui-mode=<bool>]
            [--guiagent-installed=<bool>]
            [--qrexec-installed=<bool>]
            [--qrexec-timeout=<seconds>]
            [--internal=<bool>]
            [--debug=<bool>]

Examples:
  qubesctl qvm.prefs sys-net
  qubesctl qvm.prefs sys-net list
  qubesctl qvm.prefs sys-net set template=fedora-21 label=red

Arguments:
  vmname  Virtual machine name
  action  Action (list | set | gry) [default: list]

Options:
  --autostart=<bool>           Starts VM automatically on boot
  --debug=<bool>               Debug mode (default: False)
  --default-user NAME          Default users name
  --drive DRIVE                Drive
  --guiagent-installed=<bool>  Gui-agent
  --include-in-backups=<bool>  Include in qubes backups (default: True)
  --internal=<bool>            Internal
  --kernel KERNEL              Selected kernel
  --kernelopts OPTS_STRING     Kernel options string (include in quotes)
  --label=<color>              VM label color
                               [red|yellow|green|blue|purple|orange|gray|black]
  --memory=<n>                 VM assigned memory
  --mac MAC                    MAC address (default: auto)
  --maxmem=<n>                 VM maximum memory
  --netvm SERVICEVM            Selected network service VM
  --pcidevs DEVICES            Quoted list of attached pci devices [string,]
  --seamless-gui-mode=<bool>   Seamless GUI mode
  --template NAME              Template Name
  --timezone TIMEZONE          Timezone information (UTC)
  --qrexec-installed=<bool>    Qrexec installed
  --qrexec-timeout=<seconds>   Time for qrexec timeout (default: 60)
  --vcpus=<n>                  Number of virtual CPUs to attach to VM
  --force-root                 Force to run, even with root privileges
"""

from docopt import docopt
if __name__ == '__main__':
    argv = ['--force-root', 'salt-testvm2', 'set', '--kernel', 'default', '--pcidevs', '', '--include-in-backups', 'False', '--template', 'debian-jessie', '--default-user', 'user', '--netvm', 'sys-firewall', '--memory', '400', '--drive', '', '--label', 'green', '--vcpus', '4', '--mac', 'auto', '--kernelopts', 'nopat', '--autostart', 'False', '--qrexec-installed', 'True', '--debug', 'False', '--timezone', 'UTC', '--qrexec-timeout', '60', '--guiagent-installed', 'True', '--seamless-gui-mode', 'False', '--internal', 'False', '--maxmem', '4000']
    arguments = docopt(__doc__, argv=argv, version='1.0.0rc2')
    print(arguments)

