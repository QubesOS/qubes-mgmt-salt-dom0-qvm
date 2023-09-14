# -*- coding: utf-8 -*-
#
# vim: set ts=4 sw=4 sts=4 et :
"""
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:platform:      all

============================
Qubes qvm-* modules for salt
============================

The following errors are used and raised in the circumstances as indicated:

    SaltInvocationError
        raise when criteria is not met

    CommandExecutionError
        raise when error executing command
"""

# pylint: disable=E1101,E1103

# Import python libs
from __future__ import absolute_import
import argparse  # pylint: disable=E0598
import logging
import json

# Import salt libs
from salt.exceptions import SaltInvocationError, CommandExecutionError

# Import custom libs
import module_utils  # pylint: disable=F0401
from module_utils import ModuleBase as _ModuleBase  # pylint: disable=F0401
from module_utils import Status  # pylint: disable=F0401
from nulltype import Null

import qubesadmin
import qubesadmin.devices
import qubesadmin.firewall

# Enable logging
log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'qvm'


def __virtual__():
    return __virtualname__


def _vm():
    """
    Get Qubes VM object from qvm.collection.
    """
    _vm = Null

    @property
    def vm(self):  # pylint: disable=C0103
        """
        Return VM object.
        """
        if not self._vm:  # pylint: disable=W0212
            raise SaltInvocationError(
                message='Virtual Machine does not exist!'
            )
        return self._vm  # pylint: disable=W0212

    @vm.setter
    def vm(self, value):  # pylint: disable=C0103
        """
        Get Qubes VM object from qvm.collection and set it here.
        """
        if value:
            app = qubesadmin.Qubes()
            try:
                self._vm = app.domains[value]
            except KeyError:
                self._vm = None  # pylint: disable=W0212

    return vm


# pylint: disable=R0903
class _Namespace(argparse.Namespace):
    """
    Re-purpose argparse's Namespace object to hold data for qvm base module.
    """

    vm = _vm()  # pylint: disable=C0103

    def __init__(self, **kwargs):
        super(_Namespace, self).__init__(**kwargs)


# pylint: disable=R0903
class _VMAction(argparse.Action):
    """
    Custom action to retrieve virtual machine settings object.
    """

    def __call__(self, parser, namespace, values, options_string=None):
        """
        """
        if not values:
            return None

        namespace.vm = values
        setattr(namespace, self.dest, values)


# pylint: disable=R0903
class _QVMBase(_ModuleBase):
    """
    Overrides.
    """

    # pylint: disable=E1002
    def __init__(self, __virtualname, *varargs, **kwargs):
        # XXX: Find a better way to do this; need to make sure other modules
        #      that import module_utils will have access to __opts__ if this
        #      module is never loaded or used
        if not hasattr(module_utils, '__opts__'):
            module_utils.__opts__ = __opts__

        if not hasattr(module_utils, '__salt__'):
            module_utils.__salt__ = __salt__

        super(_QVMBase, self).__init__(__virtualname, *varargs, **kwargs)
        self.argparser.options['namespace'] = _Namespace()


def is_halted(qvm, prefix=None, message=None, error_message=None):
    """
    Check VM power state.
    """
    try:
        halted_status = state(qvm.args.vm.name, *['halted'])

    except SaltInvocationError as err:
        halted_status = Status()
        prefix = '[SKIP] '
        message = err.message

    qvm.save_status(
        halted_status,
        prefix=prefix,
        message=message,
        error_message=error_message
    )
    return halted_status


def is_running(qvm, prefix=None, message=None, error_message=None):
    """
    Check if VM is running.
    """
    running_status = state(qvm.args.vm.name, *['running'])

    qvm.save_status(
        running_status,
        retcode=running_status.retcode,
        prefix=prefix,
        message=message,
        error_message=error_message
    )
    return running_status


def is_paused(qvm, prefix=None, message=None, error_message=None):
    """
    Check if VM is in a paused state.
    """
    paused_status = state(qvm.args.vm.name, *['paused'])

    qvm.save_status(
        paused_status,
        retcode=paused_status.retcode,
        prefix=prefix,
        message=message,
        error_message=error_message
    )
    return paused_status


def check(vmname, *varargs, **kwargs):
    """
    Check if a virtual machine exists::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.check <vmname> exists flags=[quiet]

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>

        # Optional Positional
        - check:                (exists)|missing

        # Optional Flags
        - flags:
          - quiet
    """
    # Hide 'check' flag from argv as its not a valid qvm.check option
    qvm = _QVMBase('qvm.check', **kwargs)
    qvm.argparser.options['hide'] = ['check']

    qvm.parser.add_argument('--quiet', action='store_true', help='Quiet')
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    qvm.parser.add_argument(
        'check',
        nargs='?',
        default='exists',
        choices=('exists', 'missing'),
        help='Check if virtual machine exists or not'
    )
    args = qvm.parse_args(vmname, *varargs, **kwargs)

    # pylint: disable=W0613
    def run_post(cmd, status, data):
        """
        Called by run to allow additional post-processing of status.
        """
        if args.check.lower() == 'missing':
            status.retcode = not status.retcode

    # Execute command (will not execute in test mode)
    cmd = '/usr/bin/qvm-check {0}'.format(' '.join(args._argv))  # pylint: disable=W0212

    # pylint: disable=W0612
    status = qvm.run(
        cmd,
        post_hook=run_post,
        test_ignore=True
    )

    # Returns the status 'data' dictionary
    return qvm.status()


def state(vmname, *varargs, **kwargs):
    """
    Return virtual machine state::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.state <vmname> running

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>

        # Optional Positional
        - state:                (status)|running|halted|transient|paused
    """
    qvm = _QVMBase('qvm.state', **kwargs)
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    qvm.parser.add_argument(
        'state',
        nargs='*',
        default='status',
        choices=('status', 'running', 'halted', 'transient', 'paused'),
        help='Check power state of virtual machine'
    )
    args = qvm.parse_args(vmname, *varargs, **kwargs)

    # Check VM power state
    retcode = 0
    stdout = args.vm.get_power_state()
    power_state = stdout.strip().lower()

    if 'status' not in args.state:
        if power_state not in args.state:
            retcode = 1

    # Create status
    status = Status(
        retcode=retcode,
        data=power_state,
        stdout=stdout,
        stderr='',
        message='{0} {1}'.format(qvm.__virtualname__, ' '.join(args.state))
    )

    # Merge status
    qvm.save_status(status)

    # Returns the status 'data' dictionary
    return qvm.status()


def create(vmname, *varargs, **kwargs):
    """
    Create a new virtual machine::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.create <vmname> label=red template=fedora-21 flags=[proxy]

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>

        # Optional
        - template:             <template>
        - label:                <label>
        - class:                <class>
        - mem:                  <mem>
        - vcpus:                <vcpus>
        - root-move-from:       <root_move>
        - root-copy-from:       <root_copy>

        # Optional Flags
        - flags:
          - proxy
          - hvm
          - hvm-template
          - net
          - standalone
          - quiet
    """
    qvm = _QVMBase('qvm.create', **kwargs)
    qvm.parser.add_argument('--quiet', action='store_true', help='Quiet')
    qvm.parser.add_argument(
        '--net',
        action='store_true',
        help='Create NetVM'
    )
    qvm.parser.add_argument(
        '--proxy',
        action='store_true',
        help='Create ProxyVM'
    )
    qvm.parser.add_argument(
        '--hvm',
        action='store_true',
        help='Create HVM (standalone unless --template option used)'
    )
    qvm.parser.add_argument(
        '--hvm-template',
        action='store_true',
        help='Create HVM template'
    )
    qvm.parser.add_argument(
        '--standalone',
        action='store_true',
        help='Create standalone VM - independent of template'
    )
    qvm.parser.add_argument(
        '--template',
        nargs=1,
        help='Specify the TemplateVM to use'
    )
    qvm.parser.add_argument(
        '--label',
        nargs=1,
        help=
        'Specify the label to use for the new VM (e.g. red, yellow, green, ...)'
    )
    qvm.parser.add_argument(
        '--class',
        nargs=1,
        dest='klass',
        help='Class of the new domain (default: "AppVM"'
             ' - see documentation for qvm-create for possible values)'
    )
    qvm.parser.add_argument(
        '--mem',
        nargs=1,
        help=
        'Specify the initial memory size of the VM'
    )
    qvm.parser.add_argument(
        '--root-move-from',
        nargs=1,
        help=
        'Use provided root.img instead of default/empty one (file will be MOVED)'
    )
    qvm.parser.add_argument(
        '--root-copy-from',
        nargs=1,
        help=
        'Use provided root.img instead of default/empty one (file will be COPIED)'
    )
    qvm.parser.add_argument('--vcpus', nargs=1, help='VCPUs count')
    qvm.parser.add_argument('vmname', help='Virtual machine name')
    args = qvm.parse_args(vmname, *varargs, **kwargs)

    vmclass = 'AppVM'
    if args.hvm_template:
        vmclass = 'TemplateVM'
    elif args.standalone:
        vmclass = 'StandaloneVM'
    elif args.klass:
        vmclass = args.klass[0]

    properties = {}
    if args.mem:
        properties['memory'] = args.mem[0]
    if args.vcpus:
        properties['vcpus'] = args.vcpus[0]
    if args.hvm:
        properties['virt_mode'] = 'hvm'
    if args.proxy or args.net:
        properties['provides_network'] = 'True'
    if args.net:
        properties['netvm'] = ''

    options = ['--class=' + vmclass]
    if args.root_move_from:
        options.append('--root-move-from=' + args.root_move_from[0])
    if args.root_copy_from:
        options.append('--root-copy-from=' + args.root_copy_from[0])
    if args.template:
        options.append('--template=' + args.template[0])
    if args.label:
        options.append('--label=' + args.label[0])

    for name, value in properties.items():
        options.append('--property=' + name + '=' + value)

    # pylint: disable=W0613
    def missing_post_hook(cmd, status, data):
        """
        Post-run hook called after `check` for missing status.
        """
        if status.retcode:
            status.result = status.retcode

    # Confirm VM is missing
    missing_status = check(
        args.vmname, *['missing'], **{
            'run-post-hook': missing_post_hook
        }
    )
    qvm.save_status(missing_status)
    if missing_status.failed():
        return qvm.status()

    # Execute command (will not execute in test mode)
    cmd = '/usr/bin/qvm-create {} {}'.format(args.vmname, ' '.join(options))  # pylint: disable=W0212
    status = qvm.run(cmd)  # pylint: disable=W0612

    # Returns the status 'data' dictionary
    return qvm.status()


def remove(vmname, *varargs, **kwargs):
    """
    Remove an existing virtual machine::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.remove <vmname> flags=[just-db]

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>

        # Optional Flags
        - flags:
          - just-db:
          - force-root
          - quiet
    """
    # Hide 'shutdown' flag from argv as its not a valid qvm.remove option
    qvm = _QVMBase('qvm.remove', **kwargs)
    qvm.parser.add_argument(
        '--just-db',
        action='store_true',
        help='Remove only from the Qubes Xen DB, do not remove any files'
    )
    qvm.parser.add_argument('--quiet', action='store_true', help='Quiet')
    qvm.parser.add_argument(
        '--force-root',
        action='store_true',
        help='Force to run, even with root privileges'
    )
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    args = qvm.parse_args(vmname, *varargs, **kwargs)

    if not is_halted(qvm):
        # 'shutdown' VM ('force' mode will kill on failed shutdown)
        shutdown_status = qvm.save_status(
            shutdown(
                args.vmname, **{'flags': ['wait', 'force']}
            )
        )
        if shutdown_status.failed():
            return qvm.status()

    # Execute command (will not execute in test mode)
    cmd = '/usr/bin/qvm-remove --force {0}'.format(' '.join(args._argv))  # pylint: disable=W0212
    status = qvm.run(cmd)  # pylint: disable=W0612

    # Confirm VM has been removed (don't fail in test mode)
    if not __opts__['test']:
        qvm.save_status(check(args.vmname, *['missing']))

    # Returns the status 'data' dictionary and adds comments in 'test' mode
    return qvm.status()


# pylint: disable=W0621
def clone(vmname, clone, *varargs, **kwargs):
    """
    Clone a new virtual machine::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.clone <source> <clone> [shutdown=true|false] [path=]

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - clone:                name
        - source:               vmname

        # Optional
        - path:                 /PATH/xxx

        # Optional Flags
        - flags:
          - shutdown
          - force-root
          - quiet
    """
    qvm = _QVMBase('qvm.clone', **kwargs)
    qvm.parser.add_argument(
        '--shutdown',
        action='store_true',
        help='Will shutdown a running or paused VM to allow cloning'
    )
    qvm.parser.add_argument('--quiet', action='store_true', help='Quiet')
    qvm.parser.add_argument(
        '--force-root',
        action='store_true',
        help='Force to run, even with root privileges'
    )
    qvm.parser.add_argument(
        '--path',
        nargs=1,
        help='Specify path to the template directory'
    )
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Source VM name to clone'
    )
    qvm.parser.add_argument('clone', help='New clone VM name')
    args = qvm.parse_args(vmname, clone, *varargs, **kwargs)

    # Remove 'shutdown' flag from argv as its not a valid qvm.clone option
    if '--shutdown' in args._argv:  # pylint: disable=W0212
        args._argv.remove('--shutdown')  # pylint: disable=W0212

    # Check if 'clone' VM exists; fail if it does and return
    clone_check_status = qvm.save_status(check(args.clone, *['missing']))
    if clone_check_status.failed():
        return qvm.status()

    if is_halted(qvm).failed():
        if args.shutdown:
            # 'shutdown' VM ('force' mode will kill on failed shutdown)
            shutdown_status = qvm.save_status(
                shutdown(
                    args.vmname, **{'flags': ['wait', 'force']}
                )
            )
            if shutdown_status.failed():
                return qvm.status()

    # Execute command (will not execute in test mode)
    cmd = '/usr/bin/qvm-clone {0}'.format(' '.join(args._argv))  # pylint: disable=W0212
    status = qvm.run(cmd)  # pylint: disable=W0612

    if __opts__['test']:
        message = 'VM is set to be cloned'
        status = qvm.save_status(message=message)
        return qvm.status()

    # Confirm VM has been cloned
    qvm.save_status(check(args.clone, *['exists']))

    # Returns the status 'data' dictionary
    return qvm.status()


def prefs(vmname, *varargs, **kwargs):
    """
    Set preferences for a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        # List
        qubesctl qvm.prefs sys-net

        # Get
        qubesctl qvm.prefs <vm_name> memory maxmem
        qubesctl qvm.prefs <vm_name> get='[memory, maxmem]'

        # Set
        qubesctl qvm.prefs <vm_name> memory=600 maxmem=6000
        qubesctl qvm.prefs <vm_name> set='[{memory: 600, maxmem: 6000}]'


    Calls the qubes utility directly since the currently library really has
    no validation routines whereas the script does.

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
        - action:               (list)|set|get|gry

        # Exclusive Positional
        - autostart:            true|(false)
        - debug:                true|(false)
        - default-user:         <string>
        - default-dispvm:       <string>
        - management-dispvm:    <string>
        - guivm:                <string>
        - audiovm:              <string>
        - template-for-dispvms: true|false
        - virt-mode:            (hvm|pv)
        - include-in-backups:   true|false
        - installed-by-rpm:     true|false
        - ip:                   <string>
        - kernel:               <string>
        - kernelopts:           <string>
        - label:                red|yellow|green|blue|purple|orange|gray|black
        - last-backup:          <string>
        - mac:                  <string> (auto)
        - maxmem:               <int>
        - memory:               <int>
        - netvm:                <string>
          # pci-strictreset applies only to devices in pcidevs here, for full
          # control use qvm.device (TBD)
        - pci-strictreset:      true|false
        - pcidevs:              [string,]
        - template:             <string>
        - qrexec-timeout:       <int> (60)
        - vcpus:                <int>

    Example:

    .. code-block:: yaml

        # List
        test-vm-1:  # (test-vm-1 is the VM name)
          qvm.prefs:
            - action: list

        test-vm-2:
          qvm.prefs: []

        some-lable-that-is-not-the-vm-name:
          qvm.prefs:
            - name: test-vm-3

        # Get
        test-vm-4:
          qvm.prefs:
            - get:
              - memory
              - maxmem

        # Set
        test-vm-5:
          qvm.prefs:
            - memory: 400
            - maxmem: 4000
    """
    # Also allow CLI qubesctl qvm.prefs <vm_name> memory maxmem
    if varargs:
        properties = []
        for property_ in varargs:
            properties.append(property_)
        if properties:
            kwargs['get'] = properties

    # Also allow 'get' instead of 'action=get'
    if 'get' in kwargs:
        # pylint: disable=E0598
        kwargs.update(
            {
                k: Null
                for k in kwargs.pop('get')
            }
        )  # pylint: disable=E0598
        kwargs['action'] = 'get'

    # Also allow 'set' instead of 'action=set'
    elif 'set' in kwargs:
        kwargs.update(
            {
                k: v
                for d in kwargs.pop('set') for k, v in d.items()
            }
        )  # pylint: disable=E0598
        kwargs['action'] = 'set'

    # Set default status-mode to show all status entries
    kwargs.setdefault('status-mode', 'all')

    # Hide 'action' flag from argv as its not a valid qvm.pref option
    qvm = _QVMBase('qvm.create', **kwargs)
    qvm.argparser.options['hide'] = ['action']
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    qvm.parser.add_argument(
        'action',
        nargs='?',
        default='list',
        choices=('list', 'get', 'gry', 'set')
    )

    qvm.argparser.add_argument_group('properties')
    properties = qvm.argparser.get_argument_group('properties')
    properties.add_argument('--autostart', nargs=1, type=bool, default=False)
    properties.add_argument('--debug', nargs=1, type=bool, default=False)
    properties.add_argument('--default-user', '--default_user', nargs=1)
    properties.add_argument('--default-dispvm', '--default_dispvm', nargs=1)
    properties.add_argument('--management-dispvm', '--management_dispvm', nargs=1)
    properties.add_argument('--guivm', nargs=1)
    properties.add_argument('--audiovm', nargs=1)
    properties.add_argument(
        '--template-for-dispvms',
        '--template_for_dispvms',
        '--dispvm-allowed',
        nargs=1, type=bool)
    properties.add_argument('--virt-mode', '--virt_mode', nargs=1)
    properties.add_argument(
        '--label',
        nargs=1,
        choices=(
            'red', 'yellow', 'green', 'blue', 'purple', 'orange', 'gray',
            'black'
        )
    )
    properties.add_argument('--last-backup', '--last_backup', nargs=1)
    properties.add_argument(
        '--include-in-backups',
        '--include_in_backups',
        nargs=1,
        type=bool
    )
    properties.add_argument(
        '--installed-by-rpm',
        '--installed_by_rpm',
        nargs=1,
        type=bool
    )
    properties.add_argument('--ip', nargs=1)
    properties.add_argument('--kernel', nargs=1)
    properties.add_argument('--kernelopts', nargs=1)
    properties.add_argument('--mac', nargs=1)
    properties.add_argument('--maxmem', nargs=1, type=int)
    properties.add_argument('--memory', nargs=1, type=int)
    properties.add_argument('--netvm', nargs=1)
    properties.add_argument(
        '--pci-strictreset',
        '--pci_strictreset',
        nargs=1,
        type=bool,
        default=True
    )
    properties.add_argument('--pcidevs', nargs='*', default=[])
    properties.add_argument('--provides-network', nargs=1, type=bool,
                            default=False)
    properties.add_argument('--template', nargs=1)
    properties.add_argument(
        '--qrexec-timeout',
        '--qrexec_timeout',
        nargs=1,
        type=int,
        default=60
    )
    properties.add_argument('--updateable', nargs=1, type=bool)
    properties.add_argument('--vcpus', nargs=1, type=int)

    # Maps property keys to vm attributes
    property_map = {
        'last_backup': 'backup_timestamp',
        'dispvm_allowed': 'template_for_dispvms',
    }

    # pylint: disable=W0613

    args = qvm.parse_args(vmname, *varargs, **kwargs)
    label_width = 19
    fmt = "{{0:<{0}}}: {{1}}".format(label_width)

    all_properties = qvm.argparser.get_argument_group_keys('properties')
    selected_properties = qvm.argparser.get_argument_group_keys(
        'properties', kwargs
    )

    # Default action is list, but allow no action for set
    if args.action in ['list']:
        if selected_properties:
            args.action = 'set'
        else:
            selected_properties = all_properties

    if 'action' in kwargs and kwargs['action'] == 'get' and varargs:
        result = set(varargs).difference(set(selected_properties))
        if result:
            for r in result:
                message = fmt.format(r, 'Invalid key!')
                status = Status(retcode=1)
                qvm.save_status(status, message=message)

    # compatibility with Qubes 3.x
    pci_strictreset = kwargs.get('pci_strictreset', None)
    current_pci_strictreset = None

    changed = False
    for key in selected_properties:

        # Qubes keys are stored with underscrores ('_'), not hyphens ('-')
        dest = key.replace('-', '_')
        dest = property_map.get(dest, dest)

        if dest == 'pcidevs':
            value_current = [str(dev.ident).replace('_', ':') for dev
                             in args.vm.devices['pci'].attached()]
        elif dest == 'pci_strictreset':
            value_current = all(not assignment.options.get('no-strict-reset', False)
                                for assignment in args.vm.devices['pci'].assignments(True))
            current_pci_strictreset = value_current
        elif args.vm.property_is_default(dest):
            value_current = '*default*'
        else:
            value_current = getattr(args.vm, dest, Null)
            value_current = getattr(value_current, 'name', value_current)

        if args.action in ['list', 'get', 'gry']:
            qvm.save_status(prefix='', message=fmt.format(dest, value_current))
            continue

        value_new = kwargs[key]
        if key in ('netvm', 'guivm', 'audiovm', 'default_dispvm', 'management_dispvm'):
            if value_new in ('none', ''):
                value_new = None

        # Value matches; no need to update
        if value_current == value_new and (
                dest != 'pcidevs' or pci_strictreset == current_pci_strictreset):
            message = fmt.format(dest, value_current)
            qvm.save_status(prefix='[SKIP] ', message=message)
            continue

        data = dict(key=dest, value_old=value_current, value_new=value_new)

        if dest == 'pci_strictreset':
            if 'pcidevs' in kwargs:
                status = qvm.save_status(retcode=0)
                status.changes.setdefault(data['key'], {})
                status.changes[data['key']]['old'] = data['value_old']
                status.changes[data['key']]['new'] = data['value_new']
            else:
                message = fmt.format(dest,
                    "Setting 'pci_strictreset' works only together with 'pcidevs'")
                qvm.save_status(retcode=1, message=message)
            # "setting" pci_strictreset handled in 'pcidevs' property
            continue

        # Execute command (will not execute in test mode)
        # pylint: disable=W0212
        if dest == 'pcidevs':
            value_combined = value_current[:]
            for dev_id in value_new:
                dev_id_api = dev_id.strip().replace(':', '_')
                current_assignment = None
                for a in args.vm.devices['pci'].assignments():
                    if a.ident == dev_id_api:
                        current_assignment = a
                if current_assignment and \
                        pci_strictreset is not None and \
                        current_assignment.options.get('no-strict-reset', False) != \
                            (not pci_strictreset):
                    # detach and attach again to adjust options
                    args.vm.devices['pci'].detach(current_assignment)
                    value_combined.remove(dev_id)

                try:
                    options = {}
                    if pci_strictreset is not None:
                        options['no-strict-reset'] = not pci_strictreset
                    assignment = qubesadmin.devices.DeviceAssignment(
                        args.vm.app.domains['dom0'],
                        dev_id_api,
                        options,
                        persistent=True)
                    args.vm.devices['pci'].attach(assignment)
                except qubesadmin.exc.DeviceAlreadyAttached:
                    continue
                value_combined.append(dev_id)
                changed = True
            status = qvm.save_status(retcode=0)
            status.changes.setdefault(data['key'], {})
            status.changes[data['key']]['old'] = data['value_old']
            status.changes[data['key']]['new'] = value_combined
        else:
            log.info("Setting %s to %s", dest, value_new)
            if value_new == '*default*':
                delattr(args.vm, dest)
            else:
                setattr(args.vm, dest, value_new)
            status = qvm.save_status(retcode=0)
            status.changes.setdefault(data['key'], {})
            status.changes[data['key']]['old'] = data['value_old']
            status.changes[data['key']]['new'] = data['value_new']
            changed = True

    # Returns the status 'data' dictionary
    return qvm.status()


def devices(vmname, *varargs, **kwargs):
    """
    Manage a virtual machine domain devices::

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
        - action:               [list|attach|detach]
        - devices:             [string,]

    Example:

    .. code-block:: yaml

        # List
        test-vm-1:  # (test-vm-1 is the VM name)
          qvm.devices:
            - list: []

        test-vm-2:
          qvm.devices: []

        some-label-that-is-not-the-vm-name:
          qvm.devices:
            - name: test-vm-3

        # Attach, detach
        test-vm-4:
          qvm.devices:
            - attach:
              - pci:dom0:01_00.0: []
              - pci:dom0:02_00.0:
                - pci_strictreset: false
              - bridge:sys-net-interfaces:br0:
                - ip: 192.168.0.1
                - netmask: 255.255.255.0
            - detach:
              - pci:dom0:28_00.3: []
              - bridge:sys-net-interfaces:br1: []
    """

    # CLI 'qubesctl qvm.devices <vm_name> (attach|detach) device [device...]'
    if varargs and varargs[0] in ['attach', 'detach']:
        devices = []
        for device in varargs[1:]:
            device_type, backend, dev_id = device.split(':')
            devices.append({'device_type': device_type, 'backend': backend, 'dev_id': dev_id})
        if devices:
            kwargs[varargs[0]] = devices

    # Convert kwargs to string for argparse
    for action in ['attach', 'detach']:
        if action in kwargs:
            kwargs[action] = json.dumps(kwargs[action])

    # Set default status-mode to show all status entries
    kwargs.setdefault('status-mode', 'all')

    qvm = _QVMBase('qvm.devices', **kwargs)
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    qvm.parser.add_argument('--list', nargs='*', help='List devices')
    qvm.parser.add_argument(
        '--attach',
        nargs='*',
        default=[],
        help='List of devices to attach'
    )
    qvm.parser.add_argument(
        '--detach',
        nargs='*',
        default=[],
        help='List of devices to detach'
    )

    args = qvm.parse_args(vmname, *varargs, **kwargs)

    current_devices = []
    for device_type in args.vm.devices:
        for device in args.vm.devices[device_type].assignments():
            current_devices.append(
                {'device_type': device_type, 'backend': device.backend_domain.name, 'dev_id': device.ident,
                 'options': device.options})

    # Return all current devices if a 'list' only was selected
    if args.list is not None or not (args.attach or args.detach):
        message = []
        for device in current_devices:
            msg_options = '(' + ', '.join('{}={}'.format(key, value) for key, value in device['options'].items()) + ')'
            message.append(
                '    ' + device['device_type'] + ':' + device['backend'] + ':' + device['dev_id'] + ' ' + msg_options)

        return {'result': True, 'comment': '[ATTACHED]:\n' + '\n'.join(message)}

    # Helping function for parsing devices in args.attach and args.detach
    def parse_device(raw_dev):
        """
        Example:
            args.attach = [{u'bridge:sys-bridge:bridge0': [{u'ip': u'192.168.0.1'}, {u'netmask': u'255.255.255.0'}]}]
        """
        device = None

        inline_dev = list(raw_dev.keys())[0]
        inline_dev_split = inline_dev.split(':')

        if len(inline_dev_split) == 3:
            device = {'device_type': str(inline_dev_split[0]), 'backend': str(inline_dev_split[1]),
                      'dev_id': str(inline_dev_split[2]), 'options': {}}
            for opt in raw_dev[inline_dev]:
                device['options'].update(opt)
        else:
            raise SaltInvocationError(
                message="Missing either 'device_type', 'backend' or 'dev_id' in '%s'" % inline_dev
            )

        return device

    # post-process argparse 'attach' and 'detach' values converted from string
    if args.attach:
        args.attach = [parse_device(raw_dev) for raw_dev in json.loads(args.attach[0])]

    if args.detach:
        args.detach = [parse_device(raw_dev) for raw_dev in json.loads(args.detach[0])]

    for device in args.attach:
        device_type = device['device_type']
        device_skip = False
        message_old = None
        for a in args.vm.devices[device_type].assignments():
            if a.ident == device['dev_id'] and a.backend_domain == device['backend']:
                current_assignment = a
                if current_assignment.options != device['options']:
                    # detach and attach again to adjust options
                    args.vm.devices[device_type].detach(current_assignment)
                    msg_options = '(' + ', '.join(
                        '{}={}'.format(key, value) for key, value in current_assignment.options.items()) + ')'
                    message_old = '[ATTACHED] ' + msg_options
                else:
                    device_skip = True
                break

        msg_options = '(' + ', '.join('{}={}'.format(key, value) for key, value in device['options'].items()) + ')'
        if not device_skip:
            try:
                assignment = qubesadmin.devices.DeviceAssignment(
                    backend_domain=args.vm.app.domains[device['backend']],
                    ident=device['dev_id'],
                    options=device['options'],
                    persistent=True)

                args.vm.devices[device_type].attach(assignment)
                message_new = '[ATTACHED] ' + msg_options

                device_name = device['device_type'] + ':' + device['backend'] + ':' + device['dev_id']
                status = qvm.save_status(retcode=0)
                status.changes.setdefault(device_name, {})
                status.changes[device_name]['old'] = message_old
                status.changes[device_name]['new'] = message_new
            except qubesadmin.exc.QubesException as e:
                qvm.save_status(retcode=1, message=str(e))
        else:
            message = 'Device already attached: {type}:{backend}:{id} '.format(type=device_type,
                                                                               backend=device['backend'],
                                                                               id=device['dev_id']) + msg_options
            qvm.save_status(prefix='[SKIP] ', message=message)

    for device in args.detach:
        device_type = device['device_type']

        try:
            assignment = qubesadmin.devices.DeviceAssignment(
                backend_domain=args.vm.app.domains[device['backend']],
                ident=device['dev_id'])

            args.vm.devices[device_type].detach(assignment)

            message_old = '[ATTACHED]'
            message_new = '[DETACHED]'

            device_name = device['device_type'] + ':' + device['backend'] + ':' + device['dev_id']
            status = qvm.save_status(retcode=0)
            status.changes.setdefault(device_name, {})
            status.changes[device_name]['old'] = message_old
            status.changes[device_name]['new'] = message_new
        except qubesadmin.exc.QubesException as e:
            qvm.save_status(retcode=1, message=str(e))

    return qvm.status()


def service(vmname, *varargs, **kwargs):
    """
    Manage a virtual machine domain services::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.service <vm-name> [list]
        qubesctl qvm.service <vm_name> (enable|disable|default) service [service...]

        # List
        qubesctl qvm.service sys-net

        # Enable
        qubesctl qvm.service <vm_name> enable service1 service2

        # Disable
        qubesctl qvm.service <vm_name> disable service1 service2

        # Default
        qubesctl qvm.service <vm_name> default service1 service2

        # Combined
        qubesctl qvm.service <vm_name> enable='[service1, service2, service3]' disable='[service4, service5]'

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
        - action:               [list|enable|disable|default]
        - service_names:        [string,]

    Example:

    .. code-block:: yaml

        # List
        test-vm-1:  # (test-vm-1 is the VM name)
          qvm.service:
            - list: []

        test-vm-2:
          qvm.service: []

        some-lable-that-is-not-the-vm-name:
          qvm.service:
            - name: test-vm-3

        # Enable, disable, default
        test-vm-4:
          qvm.service:
            - enable:
              - service1
              - service2
            - disable:
              - service3
              - service4
            - default:
              - service5
              - service6
    """
    # Also allow CLI qubesctl qvm.service <vm_name> (enable|disable|default) service [service...]
    if varargs and varargs[0] in ['enable', 'disable', 'defualt']:
        services = []
        for service in varargs[1:]:
            services.append(service)
        if services:
            kwargs[varargs[0]] = services

    # Set default status-mode to show all status entries
    kwargs.setdefault('status-mode', 'all')

    qvm = _QVMBase('qvm.service', **kwargs)
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    qvm.parser.add_argument('--list', nargs='*', help='List services')
    qvm.parser.add_argument(
        '--enable',
        nargs='*',
        default=[],
        help='List of service names to enable'
    )
    qvm.parser.add_argument(
        '--disable',
        nargs='*',
        default=[],
        help='List of service names to disable'
    )
    qvm.parser.add_argument(
        '--default',
        nargs='*',
        default=[],
        help='List of service names to default'
    )

    # pylint: disable=W0613
    def run_post(cmd, status, data):
        """
        Called by run to allow additional post-processing of status.
        """
        if status.passed():
            status.changes.setdefault(data['key'], {})
            status.changes[data['key']]['old'] = data['value_old']
            status.changes[data['key']]['new'] = data['value_new']

    def label(value):
        """
        Return a mapped service label.
        """
        if value == '1':
            return 'Enabled'
        elif value == '':
            return 'Disabled'
        elif value is None:
            return 'Missing'
        return value

    # action value map
    action_map = dict(enable='1', disable='', default=None)

    args = qvm.parse_args(vmname, *varargs, **kwargs)
    current_services = dict([(k[len('service.'):], v) for k, v
                             in args.vm.features.items() if k.startswith('service.')])

    # Return all current services if a 'list' only was selected
    if args.list is not None or not (
            args.enable or args.disable or args.default
    ):
        for service_name, value in current_services.items():
            if value:
                prefix = '[ENABLED]  '
            else:
                prefix = '[DISABLED] '
            qvm.save_status(prefix=prefix, message=service_name)
        return qvm.status()

    # Remove duplicate service names; keeping order listed
    seen = set()
    for action in [args.default, args.disable, args.enable]:
        for value in action:
            if value not in seen:
                seen.add(value)
            else:
                action.remove(value)

    changed = False
    for action in ['enable', 'disable', 'default']:
        service_names = getattr(args, action, [])
        for service_name in service_names:
            value_current = current_services.get(service_name, None)
            value_new = action_map[action]

            # Value matches; no need to update
            if value_current == value_new:
                message = 'Service already in desired state: {0} \'{1}\' = {2}'.format(
                    action.upper(), service_name, label(value_current)
                )
                qvm.save_status(prefix='[SKIP] ', message=message)
                continue

            # Execute command (will not execute in test mode)
            data = dict(
                key=service_name,
                value_old=label(value_current),
                value_new=label(value_new)
            )

            if not __opts__['test']:
                if value_new is None:
                    del args.vm.features['service.' + service_name]
                else:
                    args.vm.features['service.' + service_name] = value_new
                changed = True
            status = qvm.save_status(retcode=0)
            status.changes.setdefault(service_name, {})
            status.changes[service_name]['old'] = label(current_services.get(service_name, None))
            status.changes[service_name]['new'] = label(value_new)

    # Returns the status 'data' dictionary
    return qvm.status()


def features(vmname, *varargs, **kwargs):
    """
    Manage a virtual machine domain features::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.features <vm-name> [list]
        qubesctl qvm.features <vm_name> (enable|disable|default) feature [feature...]

        # List
        qubesctl qvm.features sys-net

        # Enable
        qubesctl qvm.features <vm_name> enable feature1 feature2

        # Disable
        qubesctl qvm.features <vm_name> disable feature1 feature2

        # Default
        qubesctl qvm.features <vm_name> default feature1 feature2

        # Combined
        qubesctl qvm.features <vm_name> enable='[feature1, feature2, feature3]' disable='[feature4, feature5]'

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
        - action:               [list|enable|disable|default]
        - features:             [string,]

    Example:

    .. code-block:: yaml

        # List
        test-vm-1:  # (test-vm-1 is the VM name)
          qvm.features:
            - list: []

        test-vm-2:
          qvm.features: []

        some-label-that-is-not-the-vm-name:
          qvm.features:
            - name: test-vm-3

        # Enable, disable, default
        test-vm-4:
          qvm.features:
            - enable:
              - feature1
              - feature2
            - disable:
              - feature3
              - feature4
            - default:
              - feature5
              - feature6

        # Set particular feature with value
        test-vm-5:
          qvm.features:
            - set:
              - bridge_name: br0

    """
    # Also allow CLI qubesctl qvm.features <vm_name> (enable|disable|default) feature [feature...]
    if varargs and varargs[0] in ['enable', 'disable', 'default']:
        features = []
        for feature in varargs[1:]:
            features.append(feature)
        if features:
            kwargs[varargs[0]] = features
    elif varargs and varargs[0] in ['set']:
        features = {}
        for feature in varargs[1:]:
            feature_name, feature_value = feature.split('=', 1)
            features[feature_name] = feature_value
        if features:
            kwargs[varargs[0]] = features

    # Convert OrderedDict to dict:
    if 'set' in kwargs:
        for i in range(len(kwargs['set'])):
            kwargs['set'][i] = dict(kwargs['set'][i])

        kwargs['set'] = json.dumps(kwargs['set'])

    # Set default status-mode to show all status entries
    kwargs.setdefault('status-mode', 'all')

    qvm = _QVMBase('qvm.features', **kwargs)
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    qvm.parser.add_argument('--list', nargs='*', help='List features')
    qvm.parser.add_argument(
        '--enable',
        nargs='*',
        default=[],
        help='List of feature names to enable'
    )
    qvm.parser.add_argument(
        '--disable',
        nargs='*',
        default=[],
        help='List of feature names to disable'
    )
    qvm.parser.add_argument(
        '--default',
        nargs='*',
        default=[],
        help='List of feature names to default'
    )
    qvm.parser.add_argument(
        '--set',
        nargs='*',
        default=[],
        help='List of feature names to set'
    )

    # pylint: disable=W0613
    def run_post(cmd, status, data):
        """
        Called by run to allow additional post-processing of status.
        """
        if status.passed():
            status.changes.setdefault(data['key'], {})
            status.changes[data['key']]['old'] = data['value_old']
            status.changes[data['key']]['new'] = data['value_new']

    def label(value):
        """
        Return a mapped service label.
        """
        if value == '1':
            return 'Enabled'
        elif value == '':
            return 'Disabled'
        elif value is None:
            return 'Missing'
        return value

    # action value map
    action_map = dict(enable='1', disable='', default=None)

    args = qvm.parse_args(vmname, *varargs, **kwargs)
    current_features = dict([(k, v) for k, v in args.vm.features.items()])

    # post-process argparse 'set' values converted from string
    if args.set:
        args.set = json.loads(args.set[0])

    # Return all current features if a 'list' only was selected
    if args.list is not None or not (
            args.enable or args.disable or args.default or args.set
    ):
        for feature_name, value in current_features.items():
            message = feature_name
            if value == '1':
                prefix = '[ENABLED]  '
            elif not value:
                prefix = '[DISABLED] '
            else:
                prefix = '[SET]      '
                message += ': ' + value
            qvm.save_status(prefix=prefix, message=message)
        return qvm.status()

    # Remove duplicate feature names; keeping order listed
    seen = set()
    for action in [args.default, args.disable, args.enable]:
        for value in action:
            if value not in seen:
                seen.add(value)
            else:
                action.remove(value)

    changed = False
    for action in ['enable', 'disable', 'default', 'set']:
        feature_names = getattr(args, action, [])
        for feature_name in feature_names:
            if action == 'set':
                (feature_name, value_new), = feature_name.items()
            else:
                value_new = action_map[action]

            value_current = current_features.get(feature_name, None)

            # Value matches; no need to update
            if value_current == value_new:
                message = 'Feature already in desired state: {0} \'{1}\' = {2}'.format(
                    action.upper(), feature_name, label(value_current)
                )
                qvm.save_status(prefix='[SKIP] ', message=message)
                continue

            # Execute command (will not execute in test mode)
            data = dict(
                key=feature_name,
                value_old=label(value_current),
                value_new=label(value_new)
            )

            if not __opts__['test']:
                if value_new is None:
                    del args.vm.features[feature_name]
                else:
                    args.vm.features[feature_name] = value_new
                changed = True
            status = qvm.save_status(retcode=0)
            status.changes.setdefault(feature_name, {})
            status.changes[feature_name]['old'] = current_features.get(feature_name, None)
            status.changes[feature_name]['new'] = value_new

    # Returns the status 'data' dictionary
    return qvm.status()


def tags(vmname, *varargs, **kwargs):
    """
    Manage a virtual machine domain tags::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.tags <vm-name> [list]
        qubesctl qvm.tags <vm_name> (add|del) tag [tag...]
        qubesctl qvm.tags <vm_name> (present|absent) tag [tag...]

        # List
        qubesctl qvm.tags sys-net

        # Add
        qubesctl qvm.tags <vm_name> add tag1 tag2

        # Delete
        qubesctl qvm.tags <vm_name> del tag1 tag2

        # Combined
        qubesctl qvm.tags <vm_name> add='[tag1, tag2, tag3]' del='[tag4, tag5]'

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
        - action:               [list|add|del|present|absent]
        - tags:             [string,]

    Example:

    .. code-block:: yaml

        # List
        test-vm-1:  # (test-vm-1 is the VM name)
          qvm.tags:
            - list: []

        test-vm-2:
          qvm.tags: []

        some-label-that-is-not-the-vm-name:
          qvm.tags:
            - name: test-vm-3

        # Add, delete
        test-vm-4:
          qvm.tags:
            - add:
              - tag1
              - tag2
            - del:
              - tag3
              - tag4

    """
    # Also allow CLI qubesctl qvm.tags <vm_name> (add|del) tag [tag...]
    if varargs and varargs[0] in ['add', 'del', 'present', 'absent']:
        tags = []
        for tag in varargs[1:]:
            tags.append(tag)
        if tags:
            kwargs[varargs[0]] = tags

    qvm = _QVMBase('qvm.tags', **kwargs)
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    qvm.parser.add_argument('--list', dest='do_list', nargs='*', help='List tags')
    qvm.parser.add_argument(
        '--add', '--present', dest='do_add',
        nargs='*',
        default=[],
        help='List of tag names to enable'
    )
    qvm.parser.add_argument(
        '--del', '--absent', dest='do_del',
        nargs='*',
        default=[],
        help='List of tag names to disable'
    )

    args = qvm.parse_args(vmname, *varargs, **kwargs)
    current_tags = set(args.vm.tags)

    # Return all current tags if a 'list' only was selected
    if args.do_list is not None or not (
            args.do_add or args.do_del):
        for tag in current_tags:
            qvm.save_status(message=tag)
        return qvm.status()

    # Remove duplicate tag names; keeping order listed
    seen = set()
    for action in [args.do_del, args.do_add]:
        for value in action:
            if value not in seen:
                seen.add(value)
            else:
                action.remove(value)

    if not __opts__['test']:
        try:
            for tag in args.do_add:
                args.vm.tags.add(tag)
            for tag in args.do_del:
                args.vm.tags.discard(tag)
        except qubesadmin.exc.QubesException as e:
            status = qvm.save_status(retcode=1, message=str(e))
            return qvm.status()
        new_tags = set(args.vm.tags)
    else:
        new_tags = current_tags.copy()
        for tag in args.do_add:
            new_tags.add(tag)
        for tag in args.do_del:
            new_tags.discard(tag)

    if new_tags != current_tags:
        status = qvm.save_status(retcode=0)
        status.changes['old'] = list(sorted(current_tags))
        status.changes['new'] = list(sorted(new_tags))
    else:
        qvm.save_status(prefix='[SKIP] ',
                        message='All requested tags already set: ' +
                                ','.join(sorted(current_tags)))

    # Returns the status 'data' dictionary
    return qvm.status()


def firewall(vmname, *varargs, **kwargs):
    """
    Manage a virtual machine domain firewall::

    CLI example:

    .. code-block:: bash

        qubesctl qvm.firewall <vm-name> [list]
        qubesctl qvm.firewall <vm-name> set rule1 rule2

        # List
        qybesctl qvm.firewall sys-net

        # Set.  Note that the `=` is important to prevent SaltStack from
        # interpreting the rule as a dictionary.
        qubesctl qvm.firewall <vm_name> set='action=accept'

        # Combined
        qubesctl qvm.firewall <vm_name> set=['action=accept proto=tcp', 'action=drop']

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:     <vmname>
        - action:   [list|set]
        - rules:    [rule,]

    Example:

    .. code-block:: yaml

        # List
        test-vm-1:  # (test-vm-1 is the VM name)
          qvm.firewall:
            - list: []

        test-vm-2:
          qvm.firewall: []

        test-vm-3:
          qvm.firewall:
            - set:
              - action=accept dstports=443 proto=tcp
              - action=drop
    """
    qvm = _QVMBase('qvm.firewall', **kwargs)
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    qvm.parser.add_argument(
        '--list',
        dest='do_list',
        nargs='*',
        help='List rules'
    )
    qvm.parser.add_argument(
        '--set',
        dest='do_set',
        nargs='*',
        default=[],
        help='List of rules to set'
    )
    args = qvm.parse_args(vmname, *varargs, **kwargs)
    current_rules = args.vm.firewall.rules

    if args.do_list is not None or not args.do_set:
        for rule in current_rules:
            qvm.save_status(message=rule.rule)
        return qvm.status()

    try:
        new_rules = [qubesadmin.firewall.Rule(r) for r in args.do_set]
    except (qubesadmin.exc.QubesException, ValueError) as e:
        status = qvm.save_status(retcode=1, message=str(e))
        return qvm.status()

    if current_rules != new_rules:
        if not __opts__['test']:
            args.vm.firewall.rules = new_rules
        status = qvm.save_status(retcode=0)
        status.changes['old'] = '\n'.join(r.rule for r in current_rules)
        status.changes['new'] = '\n'.join(r.rule for r in new_rules)
    else:
        qvm.save_status(prefix='[SKIP] ',
                        message='All requested rules already set:\n' +
                                '\n'.join(r.rule for r in current_rules))
    return qvm.status()


def run(vmname, *varargs, **kwargs):
    """
    Run an application within a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.run [options] <vm-name> [<cmd>]

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
        - cmd:                  <run command>

        # Optional
        - user:                 <user>
        - exclude:              <exclude_list>
        - localcmd:             <localcmd>
        - color-output:         <color_output>

        # Optional Flags
        - flags:
          - quiet
          - auto
          - tray
          - all
          - pause
          - unpause
          - pass-io
          - nogui
          - filter-escape-chars
          - no-filter-escape-chars
          - no-color-output
    """
    qvm = _QVMBase('qvm.run', **kwargs)
    qvm.parser.add_argument('--quiet', action='store_true', help='Quiet')
    qvm.parser.add_argument(
        '--auto',
        action='store_true',
        help='Auto start the VM if not running'
    )
    qvm.parser.add_argument(
        '--tray',
        action='store_true',
        help='Use tray notifications instead of stdout'
    )
    qvm.parser.add_argument(
        '--all',
        action='store_true',
        help=
        'Run command on all currently running VMs (or all paused, in case of --unpause)'
    )
    qvm.parser.add_argument(
        '--pause',
        action='store_true',
        help="Do 'xl pause' for the VM(s) (can be combined this with --all)"
    )
    qvm.parser.add_argument(
        '--unpause',
        action='store_true',
        help="Do 'xl unpause' for the VM(s) (can be combined this with --all)"
    )
    qvm.parser.add_argument(
        '--pass-io',
        action='store_true',
        help='Pass stdin/stdout/stderr from remote program (implies -q)'
    )
    qvm.parser.add_argument(
        '--nogui',
        action='store_true',
        help='Run command without gui'
    )
    qvm.parser.add_argument(
        '--filter-escape-chars',
        action='store_true',
        help='Filter terminal escape sequences (default if output is terminal)'
    )
    qvm.parser.add_argument(
        '--no-filter-escape-chars',
        action='store_true',
        help=
        'Do not filter terminal escape sequences - overrides --filter-escape-chars, DANGEROUS when output is terminal'
    )
    qvm.parser.add_argument(
        '--no-color-output',
        action='store_true',
        help='Disable marking VM output with red color'
    )
    qvm.parser.add_argument(
        '--user',
        nargs=1,
        help='Run command in a VM as a specified user'
    )
    qvm.parser.add_argument(
        '--localcmd',
        nargs=1,
        help='With --pass-io, pass stdin/stdout/stderr to the given program'
    )
    qvm.parser.add_argument(
        '--color-output',
        nargs=1,
        help='Force marking VM output with given ANSI style (use 31 for red)'
    )
    qvm.parser.add_argument(
        '--exclude',
        default=list,
        nargs='*',
        help='When --all is used: exclude this VM name (may be repeated)'
    )
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    qvm.parser.add_argument(
        'cmd',
        nargs='*',
        default=list,
        type=list,
        help='Command to run'
    )
    args = qvm.parse_args(vmname, *varargs, **kwargs)

    # Check VM power state and start if 'auto' is enabled
    if args.auto:
        start_status = qvm.save_status(
            start(
                args.vmname, **{'flags': ['quiet']}
            )
        )
        if start_status.failed():
            return qvm.status()

    # Execute command (will not execute in test mode)
    cmd = '/usr/bin/qvm-run {0}'.format(' '.join(args._argv))  # pylint: disable=W0212
    status = qvm.run(cmd)  # pylint: disable=W0612

    # Returns the status 'data' dictionary
    return qvm.status()


def start(vmname, *varargs, **kwargs):
    """
    Start a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.start <vm-name>

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>

        # Optional
        - drive:                <drive>
        - hddisk:               <drive_hd>
        - cdrom:                <drive_cdrom>
        - custom-config:        <custom_config>

        # Optional Flags
        - flags:
          - quiet
          - debug
          - install-windows-tools
    """
    qvm = _QVMBase('qvm.start', **kwargs)
    qvm.parser.add_argument('--quiet', action='store_true', help='Quiet')
    qvm.parser.add_argument(
        '--install-windows-tools',
        action='store_true',
        help='Attach Windows tools CDROM to the VM'
    )
    qvm.parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode for this VM (until its shutdown)'
    )
    qvm.parser.add_argument(
        '--drive',
        help="Temporarily attach specified drive as CD/DVD or hard disk "
             "(can be specified with prefix 'hd:' or 'cdrom:', default is cdrom)"
    )
    qvm.parser.add_argument(
        '--hddisk',
        help='Temporarily attach specified drive as hard disk'
    )
    qvm.parser.add_argument(
        '--cdrom',
        help='Temporarily attach specified drive as CD/DVD'
    )
    qvm.parser.add_argument(
        '--custom-config',
        help='Use custom Xen config instead of Qubes-generated one'
    )
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    args = qvm.parse_args(vmname, *varargs, **kwargs)

    def start_guid():
        """
        Prevent startup status showing as `Transient`.
        """
        try:
            if not args.vm.is_guid_running():
                args.vm.start_guid()
        except AttributeError:
            # AttributeError: CEncodingAwareStringIO instance has no attribute 'fileno'
            pass

    def is_transient():
        """
        Start guid if VM is `transient`.
        """
        transient_status = state(args.vmname, *['transient'])
        if transient_status.passed():
            if __opts__['test']:
                message = '\'guid\' will be started since in \'transient\' state!'
                qvm.save_status(transient_status, message=message)
                return qvm.status()

            # 'start_guid' then confirm 'running' power state
            start_guid()
            return not is_running(
                qvm,
                error_message='\'guid\' failed to start!'
            )
        return False

    # No need to start if VM is already 'running'
    if is_running(qvm):
        return qvm.status()

    # 'unpause' VM if its 'paused'
    paused_status = state(args.vmname, *['paused'])
    if paused_status.passed():
        resume_status = unpause(args.vmname)
        qvm.save_status(
            resume_status,
            error_message='VM failed to resume from pause!'
        )
        if not resume_status:
            return qvm.status()

    if is_transient():
        return qvm.status()

    # Execute command (will not execute in test mode)
    cmd = '/usr/bin/qvm-start {0}'.format(' '.join(args._argv))  # pylint: disable=W0212
    status = qvm.run(cmd)  # pylint: disable=W0612

    # Confirm VM has been started (don't fail in test mode)
    if not __opts__['test']:
        if is_transient():
            return qvm.status()

        is_running(qvm)

    # Returns the status 'data' dictionary
    return qvm.status()


def shutdown(vmname, *varargs, **kwargs):
    """
    Shutdown a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.shutdown <vm-name>

    Valid actions:

    .. code-block:: yaml

        - name:                 <vmname>

        # Optional
        - exclude:              [exclude_list]

        # Optional Flags
        - flags:
          - quiet
          - force
          - wait
          - all
          - kill
    """
    qvm = _QVMBase('qvm.shutdown', **kwargs)
    qvm.parser.add_argument(
        '--quiet',
        action='store_true',
        default=False,
        help='Quiet'
    )
    qvm.parser.add_argument(
        '--kill',
        action='store_true',
        default=False,
        help='Kill VM'
    )
    qvm.parser.add_argument(
        '--force',
        action='store_true',
        help=
        'Force operation, even if may damage other VMs (eg shutdown of NetVM)'
    )
    qvm.parser.add_argument(
        '--wait',
        action='store_true',
        help='Wait for the VM(s) to shutdown'
    )
    qvm.parser.add_argument(
        '--all',
        action='store_true',
        help='Shutdown all running VMs'
    )
    qvm.parser.add_argument(
        '--exclude',
        action='store',
        default=[],
        nargs='*',
        help='When --all is used: exclude this VM name (may be repeated)'
    )
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    args = qvm.parse_args(vmname, *varargs, **kwargs)

    def is_transient():
        """
        Kill if transient and `force` option enabled.
        """
        transient_status = state(args.vmname, *['transient'])
        if transient_status.passed():
            if __opts__['test']:
                force = set(['force', 'kill']).intersection(kwargs)
                if force:
                    message = 'VM will be killed in \'transient\' state since {0} enabled!'.format(
                        ' + '.join(force)
                    )
                else:
                    message = 'VM is \'transient\'. \'kill\' or \'force\' mode not enabled!'
                    transient_status.retcode = 1
                qvm.save_status(transient_status, message=message)
                return qvm.status()

            # 'kill' then confirm 'halted' power state
            cmd = '/usr/bin/qvm-kill {0}'.format(args.vmname)
            status = qvm.run(cmd)  # pylint: disable=W0612
            return not qvm.save_status(
                is_halted(
                    qvm,
                    message='\'guid\' failed to halt!'
                )
            )
        return False

    if __opts__['test']:
        if args.kill:
            message = 'VM is set to be killed'
        else:
            message = 'VM is set for shutdown'
        qvm.save_status(message=message)
        return qvm.status()

    # No need to start if VM is already 'halted'
    if is_halted(qvm):
        return qvm.status()

    # 'unpause' VM then if its 'paused', then confirm 'halted' power state
    paused_status = state(args.vmname, *['paused'])
    if paused_status.passed():
        args.vm.unpause()
        # pylint: disable=W0612
        halted = qvm.save_status(
            is_halted(
                qvm,
                message='VM failed to resume from pause!'
            )
        )
        return qvm.status()

    if is_transient():
        return qvm.status()

    # Execute command (will not execute in test mode)
    if qvm.args.kill:
        cmd = '/usr/bin/qvm-kill {0}'.format(args.vmname)
    else:
        cmd = '/usr/bin/qvm-shutdown {0}'.format(' '.join(args._argv))  # pylint: disable=W0212
    status = qvm.run(cmd)  # pylint: disable=W0612

    # Kill if still not 'halted' only if 'force' enabled
    if not is_halted(qvm) and args.force:
        cmd = '/usr/bin/qvm-kill {0}'.format(args.vmname)
        status = qvm.run(cmd)

    is_halted(qvm)

    # Returns the status 'data' dictionary
    return qvm.status()


def kill(vmname, *varargs, **kwargs):
    """
    Kill a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.kill <vmname>

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
    """
    qvm = _QVMBase('qvm.kill', **kwargs)
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    args = qvm.parse_args(vmname, *varargs, **kwargs)

    kwargs.setdefault('flags', [])
    kwargs['flags'].append('kill')

    # 'kill' VM
    halted_status = shutdown(args.vmname, *varargs, **kwargs)

    # Returns the status 'data' dictionary
    qvm.save_status(halted_status)
    return qvm.status()


def pause(vmname, *varargs, **kwargs):
    """
    Pause a virtual machine::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.pause <vm-name>

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
    """
    qvm = _QVMBase('qvm.pause', **kwargs)
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    args = qvm.parse_args(vmname, *varargs, **kwargs)

    # Can't pause VM if it's not running
    if not is_running(qvm):
        message = 'VM is not running'
        qvm.save_status(result=True, message=message)
        return qvm.status()

    if __opts__['test']:
        message = 'VM is set to be paused'
        qvm.save_status(message=message)
        return qvm.status()

    # Execute command (will not execute in test mode)
    args.vm.pause()

    paused_status = state(args.vmname, *['paused'])
    qvm.save_status(paused_status, retcode=paused_status.retcode)

    # Returns the status 'data' dictionary
    return qvm.status()


def unpause(vmname, *varargs, **kwargs):
    """
    Unpause a virtual machine::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.unpause <vm-name>

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
    """
    qvm = _QVMBase('qvm.unpause', **kwargs)
    qvm.parser.add_argument(
        'vmname',
        action=_VMAction,
        help='Virtual machine name'
    )
    args = qvm.parse_args(vmname, *varargs, **kwargs)

    # Can't resume VM if it's not paused
    if not is_paused(qvm):
        message = 'VM is not paused'
        qvm.save_status(result=True, message=message)
        return qvm.status()

    if __opts__['test']:
        message = 'VM set to be resumed'
        qvm.save_status(message=message)
        return qvm.status()

    # Execute command (will not execute in test mode)
    args.vm.unpause()

    running_status = state(args.vmname, *['running'])
    qvm.save_status(
        running_status,
        retcode=running_status.retcode,
        error_message='VM failed to resume from pause!'
    )

    # Returns the status 'data' dictionary
    return qvm.status()


def template_info(name, **kwargs):
    """
    Get info about installed template

    Returns dict of: 'name', 'version', 'reponame' (if found)
    or empty dict if not found
    """
    info_ret = __salt__['cmd.run_all'](
            'qvm-template info --installed --machine-readable-json {}'.format(name),
            ignore_retcode=True)
    if info_ret['retcode']:
        # not found
        return {}
    # just take the first line:
    info = json.loads(info_ret['stdout'])
    assert 'installed' in info
    assert len(info['installed']) == 1
    ret = info['installed'][0]
    return ret


def template_install(name, version=None, fromrepo=None, pool=None, **kwargs):
    """
    Install a specified template

    name
        name of the template to install

    version
        version of the template to install, in form [EPOCH:]VERSION[-RELEASE]

    fromrepo
        download the template from this specific repo, instead of the system default

    pool
        install into specific storage pool
    """

    cmd = 'qvm-template install --quiet'
    if fromrepo:
        cmd += ' --repoid={}'.format(fromrepo)
    if pool:
        cmd += ' --pool={}'.format(pool)
    cmd += ' ' + name
    if version:
        cmd += '-' + version

    ret = __salt__['cmd.run_all'](cmd)
    if ret['retcode']:
        raise CommandExecutionError (
            message='Failed to install template {}'.format(name),
            info=ret['stderr']
        )
    return {
        'info': ret['stderr']
    }
