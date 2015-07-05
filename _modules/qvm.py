# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:platform:      all

============================
Qubes qvm-* modules for salt
============================

The following erros are used and raised in the circumstances as indicated:

    SaltInvocationError
        raise when criteria is not met

    CommandExecutionError
        raise when error executing command

-----
TODO:
-----

prefs:
    Currently using `execfile` to parse `/usr/bin/qvm-prefs` in order to obtain
    the property list of valid fields that can be set.  Find a better
    alternative solution to retreive the property list.
'''

# Import python libs
import argparse
import logging

from inspect import getargvalues, stack

# Salt + Qubes libs
import module_utils

from differ import ListDiffer
from qubes_utils import function_alias as _function_alias
from module_utils import ModuleBase as _ModuleBase
from module_utils import Status

# Qubes libs
from qubes.qubes import QubesVmCollection

# Enable logging
log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'qvm'


def __virtual__():
    '''
    Confine this module to Qubes dom0 based systems
    '''
    try:
        virtual_grain = __grains__['virtual'].lower()
        virtual_subtype = __grains__['virtual_subtype'].lower()
    except Exception:
        return False

    enabled = ('xen dom0')
    if virtual_grain == 'qubes' or virtual_subtype in enabled:
        return __virtualname__
    return False

#__outputter__ = {
#    'get_prefs': 'txt',
#}


class _VMAction(argparse.Action):
    '''Custom action to retreive virtual machine settings object.
    '''
    @staticmethod
    def get_vm(vmname):
        '''
        '''
        qvm_collection = QubesVmCollection()
        qvm_collection.lock_db_for_reading()
        qvm_collection.load()
        qvm_collection.unlock_db()
        vm = qvm_collection.get_vm_by_name(vmname)
        if not vm or vm.qid not in qvm_collection:
            return None
        return vm

    def __call__(self, parser, namespace, values, options_string=None):
        '''
        '''
        if not values:
            return None

        vm = self.get_vm(values)
        #if not vm:
        #    raise SaltInvocationError('Error! No VM found with the name of: {0}'.format(values))

        setattr(namespace, self.dest, values)
        setattr(namespace, 'vm', vm)


class _QVMBase(_ModuleBase):
    '''Overrides.
    '''
    def __init__(self, *varargs, **kwargs):
        '''
        '''
        frame = stack()[1][0]
        self.__info__ = getargvalues(frame)._asdict()

        # XXX: Find a better way to do this; need to make sure other modules
        #      that import module_utils will have access to __opts__ if this
        #      module is never loaded or used
        if not hasattr(module_utils, '__opts__'):
            module_utils.__opts__ = __opts__
        if not hasattr(module_utils, '__salt__'):
            module_utils.__salt__ = __salt__

        super(_QVMBase, self).__init__(*varargs, **kwargs)


@_function_alias('check')
class _Check(_QVMBase):
    '''
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
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        self.arg_options_create()['skip'].append('varargs')
        super(_Check, self).__init__(vmname, *varargs, **kwargs)

        # Remove 'check' variable from varargs since qvm-check does not support it
        try:
            self.arg_info['__argv'].remove(self.args.check)
        except ValueError:
            pass

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        parser.add_argument('--quiet', action='store_true', help='Quiet')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

        # Optional Positional
        parser.add_argument('check', nargs='?', default='exists', choices=('exists', 'missing'), help='Check if virtual machine exists or not')

    def run_post(self, cmd, status, data):
        '''Called by run to allow additional post-processing of status before
        the status get stored to self.stdout, etc
        '''
        if self.args.check.lower() == 'missing':
            status.retcode = not status.retcode

    def __call__(self):
        args = self.args

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-check {0}'.format(' '.join(self.arg_info['__argv']))
        status = self.run(cmd, test_ignore=True)

        # Returns the status 'data' dictionary
        return self.status()


@_function_alias('state')
class _State(_QVMBase):
    '''
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
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_State, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

        # Optional Positional
        parser.add_argument('state', nargs='*', default='status', choices=('status', 'running', 'halted', 'transient', 'paused'), help='Check power state of virtual machine')

    def __call__(self):
        args = self.args

        # Check VM power state
        retcode = 0
        stdout = self.vm().get_power_state()
        power_state = stdout.strip().lower()

        if 'status' not in args.state:
            if power_state not in args.state:
                retcode = 1

        # Create status
        status = Status(
            retcode = retcode,
            data    = power_state,
            stdout  = stdout,
            stderr  = '',
            message = '{0} {1}'.format(self.__virtualname__, ' '.join(args.state))
        )

        # Merge status
        self.save_status(status)

        # Returns the status 'data' dictionary
        return self.status()


@_function_alias('create')
class _Create(_QVMBase):
    '''
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
          - internal
          - force-root
          - quiet
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Create, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--proxy', action='store_true', help='Create ProxyVM')
        parser.add_argument('--hvm', action='store_true', help='Create HVM (standalone unless --template option used)')
        parser.add_argument('--hvm-template', action='store_true', help='Create HVM template')
        parser.add_argument('--net', action='store_true', help='Create NetVM')
        parser.add_argument('--standalone', action='store_true', help='Create standalone VM - independent of template')
        parser.add_argument('--internal', action='store_true', help='Create VM for internal use only (hidden in qubes- manager, no appmenus)')
        parser.add_argument('--force-root', action='store_true', help='Force to run, even with root privileges')

        # Optional
        parser.add_argument('--template', nargs=1, help='Specify the TemplateVM to use')
        parser.add_argument('--label', nargs=1, help='Specify the label to use for the new VM (e.g. red, yellow, green, ...)')
        parser.add_argument('--root-move-from', nargs=1, help='Use provided root.img instead of default/empty one (file will be MOVED)')
        parser.add_argument('--root-copy-from', nargs=1, help='Use provided root.img instead of default/empty one (file will be COPIED)')
        parser.add_argument('--mem', nargs=1, help='Initial memory size (in MB)')
        parser.add_argument('--vcpus', nargs=1, help='VCPUs count')

        # Required Positional
        parser.add_argument('vmname', help='Virtual machine name')

    def __call__(self):
        args = self.args

        def missing_post_hook(cmd, status, data):
            if status.retcode:
                status.result = status.retcode

        # Confirm VM is missing
        missing_status = check(args.vmname, *['missing'], **{'run-post-hook': missing_post_hook})
        self.save_status(missing_status)
        if missing_status.failed():
            return self.status()

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-create {0}'.format(' '.join(self.arg_info['__argv']))
        status = self.run(cmd)

        # Confirm VM has been created (don't fail in test mode)
        if not __opts__['test']:
            self.save_status(check(args.vmname, *['exists']))

        # Returns the status 'data' dictionary
        return self.status()


@_function_alias('remove')
class _Remove(_QVMBase):
    '''
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
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        self.arg_options_create()['skip'].append('shutdown')
        super(_Remove, self).__init__(vmname, *varargs, **kwargs)

        # Remove 'shutdown' flag from argv as its not a valid qvm.clone option
        #if '--shutdown' in self.arg_info['__argv']:
        #    self.arg_info['__argv'].remove('--shutdown')

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        parser.add_argument('--just-db', action='store_true', help='Remove only from the Qubes Xen DB, do not remove any files')
        parser.add_argument('--shutdown', action='store_true', help='Shutdown / kill VM if its running')
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--force-root', action='store_true', help='Force to run, even with root privileges')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

    def __call__(self):
        # Check VM power state
        def is_halted():
            halted_status = state(args.vmname, *['halted'])
            self.save_status(halted_status)
            return halted_status

        args = self.args

        if not is_halted():
            if args.shutdown:
                # 'shutdown' VM ('force' mode will kill on failed shutdown)
                shutdown_status = self.save_status(shutdown(args.vmname, **{'flags': ['wait', 'force']}))
                if shutdown_status.failed():
                    return self.status()

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-remove {0}'.format(' '.join(self.arg_info['__argv']))
        status = self.run(cmd)

        # Confirm VM has been removed (don't fail in test mode)
        if not __opts__['test']:
            self.save_status(check(args.vmname, *['missing']))

        # Returns the status 'data' dictionary and adds comments in 'test' mode
        return self.status()


@_function_alias('clone')
class _Clone(_QVMBase):
    '''
    Clone a new virtual machine::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.clone <name> <source> [shutdown=true|false] [path=]

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
    '''
    def __init__(self, source, clone, *varargs, **kwargs):
        '''
        '''
        self.arg_options_create()['skip'].append('varargs')
        super(_Clone, self).__init__(source, clone, *varargs, **kwargs)

        # Remove 'shutdown' flag from argv as its not a valid qvm.clone option
        if '--shutdown' in self.arg_info['__argv']:
            self.arg_info['__argv'].remove('--shutdown')

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        parser.add_argument('--shutdown', action='store_true', help='Will shutdown a running or paused VM to allow cloning')
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--force-root', action='store_true', help='Force to run, even with root privileges')

        # Optional
        parser.add_argument('--path', nargs=1, help='Specify path to the template directory')

        # Required Positional
        parser.add_argument('source', nargs=1, help='Source VM name to clone')
        parser.add_argument('clone', action=_VMAction, help='New clone VM name')

    def __call__(self):
        # Check VM power state
        def is_halted():
            halted_status = state(args.source, *['halted'])
            self.save_status(halted_status)
            return halted_status

        args = self.args

        # Check if 'clone' VM exists; fail if it does and return
        clone_check_status = self.save_status(check(args.clone, *['missing']))
        if clone_check_status.failed():
            return self.status()

        if not is_halted():
            if args.shutdown:
                # 'shutdown' VM ('force' mode will kill on failed shutdown)
                shutdown_status = self.save_status(shutdown(args.source, **{'flags': ['wait', 'force']}))
                if shutdown_status.failed():
                    return self.status()

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-clone {0}'.format(' '.join(self.arg_info['__argv']))
        status = self.run(cmd)

        if __opts__['test']:
            message = 'VM is set to be cloned'
            status = self.save_status(message=message)
            return self.status()

        # Confirm VM has been cloned
        self.save_status(check(args.clone, *['exists']))

        # Returns the status 'data' dictionary
        return self.status()


@_function_alias('prefs')
class _Prefs(_QVMBase):
    '''
    Set preferences for a virtual machine domain

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.prefs <vm_name> label=orange

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
        - include-in-backups:   true|false
        - internal:             true|(false)
        - kernel:               <string>
        - kernelopts:           <string>
        - label:                red|yellow|green|blue|purple|orange|gray|black
        - mac:                  <string> (auto)
        - maxmem:               <int>
        - memory:               <int>
        - netvm:                <string>
        - pcidevs:              [string,]
        - template:             <string>
        - qrexec-timeout:       <int> (60)
        - vcpus:                <int>

        # Optional Flags
        - flags:
          - force-root
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        self.arg_options_create(argv_ordering=['flags', 'args', 'varargs', 'keywords'])['skip'].append('action')
        super(_Prefs, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Defaults override
        parser.add_argument('--status-mode', nargs='*', default=['all'], choices=('last', 'all', 'debug', 'debug-changes'), help=argparse.SUPPRESS)

        # ======================================================================
        # XXX:
        # TODO: Need to make sure set contains a keyword AND value
        # ======================================================================

        # Optional Flags
        parser.add_argument('--force-root', action='store_true', help='Force to run, even with root privileges')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        parser.add_argument('action', nargs='?', default='list', choices=('list', 'get', 'gry', 'set'))

        # Exclusive Positional
        # Optional
        parser.add_argument('--autostart', nargs='?', type=bool, default=False)
        parser.add_argument('--debug', nargs='?', type=bool, default=False)
        parser.add_argument('--default-user', nargs='?')
        parser.add_argument('--label', nargs='?', choices=('red', 'yellow', 'green', 'blue', 'purple', 'orange', 'gray', 'black'))
        parser.add_argument('--include-in-backups', nargs='?', type=bool)
        parser.add_argument('--internal', nargs='?', type=bool, default=False)
        parser.add_argument('--kernel', nargs='?')
        parser.add_argument('--kernelopts', nargs='?')
        parser.add_argument('--mac', nargs='?')
        parser.add_argument('--maxmem', nargs='?', type=int)
        parser.add_argument('--memory', nargs='?', type=int)
        parser.add_argument('--netvm', nargs='?')
        parser.add_argument('--pcidevs', nargs='*', default=[])
        parser.add_argument('--template', nargs='?')
        parser.add_argument('--qrexec-timeout', nargs='?', type=int, default=60)
        parser.add_argument('--vcpus', nargs='?', type=int)

        ## The following args seem not to exist in the Qubes R3.0 DB
        ## parser.add_argument('--timezone', nargs='?')
        ## parser.add_argument('--drive', nargs='?')
        ## parser.add_argument('--qrexec-installed', nargs='?', type=bool)
        ## parser.add_argument('--guiagent-installed', nargs='?', type=bool)
        ## parser.add_argument('--seamless-gui-mode', nargs='?', type=bool)

    def run_post(self, cmd, status, data):
        '''Called by run to allow additional post-processing of status before
        the status get stored to self.stdout, etc
        '''
        if status.passed():
            status.changes.setdefault(data['key'], {})
            status.changes[data['key']]['old'] = data['value_old']
            status.changes[data['key']]['new'] = data['value_new']

    def __call__(self):
        args = self.args
        vm = self.vm()

        label_width = 19
        fmt="{{0:<{0}}}: {{1}}".format(label_width)

        if args.action in ['list', 'get', 'gry']:
            if args.action in ['list']:
                # ==============================================================
                # XXX: TODO: Find alternative to using `execfile` to obtain
                #            qvm-prefs properties
                #
                # runpy, execfile
                #
                import os
                import sys
                _locals = dict()
                _globals = dict()
                try:
                    execfile('/usr/bin/qvm-prefs', _globals, _locals)
                except NameError:
                    pass
                properties = _locals.get('properties', []).keys()
                # ==============================================================
            else:
                properties = self.arg_info['kwargs'].keys()

            for key in properties:
                # Qubes keys are stored with underscrores ('_'), not hyphens ('-')
                key = key.replace('-', '_')

                value_current = getattr(vm, key, self.MARKER)
                value_current = getattr(value_current, 'name', value_current)

                if value_current == self.MARKER:
                    continue

                self.save_status(prefix='', message=fmt.format(key, value_current))
                continue

        else:
            for key, value_new in self.arg_info['kwargs'].items():
                # Qubes keys are stored with underscrores ('_'), not hyphens ('-')
                key = key.replace('-', '_')

                value_current = getattr(vm, key, self.MARKER)
                value_current = getattr(value_current, 'name', value_current)

                # Key does not exist in vm database
                if value_current == self.MARKER:
                    message = fmt.format(key, 'Invalid key!')
                    status = Status(retcode=1)
                    self.save_status(status, message=message)
                    continue

                # Value matches; no need to update
                if value_current == value_new:
                    message = fmt.format(key, value_current)
                    self.save_status(prefix='[SKIP] ', message=message)
                    continue

                # Execute command (will not execute in test mode)
                data = dict(key=key, value_old=value_current, value_new=value_new)
                cmd = '/usr/bin/qvm-prefs {0} --set {1} {2} "{3}"'.format(' '.join(self.arg_info['_argparse_flags']), args.vmname, key, value_new)
                status = self.run(cmd, data=data)

        # Returns the status 'data' dictionary
        return self.status()


@_function_alias('service')
class _Service(_QVMBase):
    '''
    Manage a virtual machine domain services::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.service <vm-name> [action] [service-name]

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
        - action:               [list|enable|disable|default]
        - service_names:        [string,]
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''Only varargs are processed.

        arg_info is also not needed for argparse.
        '''
        self.arg_options_create(argv_ordering=['flags', 'args', 'varargs', 'keywords'])
        super(_Service, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Defaults override
        parser.add_argument('--status-mode', nargs='*', default=['all'], choices=('last', 'all', 'debug', 'debug-changes'), help=argparse.SUPPRESS)

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

        # ======================================================================
        # XXX: Test with CLI interface.
        #
        # Current YAML interface:
        #   qvm.service:
        #     - enable:
        #       - service1
        #       - service2
        #       - service3
        #     - disable:
        #       - service4
        #       - service5
        #
        # Current CLI interface:
        #   qubesctl qvm.service enable="service1 service2 service3" disable="service4 service5"
        #
        # Additional CLI interface??? (TODO)
        #
        # ======================================================================
        #parser.add_argument('action', nargs='?', default='list', choices=('list', 'enable', 'disable', 'default'), help='Action to take on service')
        #parser.add_argument('service_names', nargs='*', default=[], help='List of Service names to reset')

        parser.add_argument('--list', nargs='*', help='List services')
        parser.add_argument('--enable', nargs='*', default=[], help='List of service names to enable')
        parser.add_argument('--disable', nargs='*', default=[], help='List of service names to disable')
        parser.add_argument('--default', nargs='*', default=[], help='List of service names to default')

    def run_post(self, cmd, status, data):
        '''Called by run to allow additional post-processing of status before
        the status get stored to self.stdout, etc
        '''
        if status.passed():
            status.changes.setdefault(data['key'], {})
            status.changes[data['key']]['old'] = data['value_old']
            status.changes[data['key']]['new'] = data['value_new']

    def __call__(self):
        def label(value):
            if value is True:
                return 'Enabled'
            elif value is False:
                return 'Disabled'
            elif value is None:
                return 'Missing'
            return value

        # action value map
        action_map = dict(
            enable  = True,
            disable = False,
            default = None
        )

        args = self.args
        current_services = self.vm().services

        # Return all current services if a 'list' only was selected
        if args.list is not None or not (args.enable or args.disable or args.default):
            for service_name, value in current_services.items():
                if value:
                    prefix = '[ENABLED]  '
                else:
                    prefix = '[DISABLED] '
                self.save_status(prefix=prefix, message=service_name)
            return self.status()

        # Remove duplicate service names; keeping order listed
        seen = set()
        for action in [args.default, args.disable, args.enable]:
            for value in action:
                if value not in seen:
                    seen.add(value)
                else:
                    action.remove(value)

        for action in ['enable', 'disable', 'default']:
            service_names = getattr(args, action, [])
            for service_name in service_names:
                value_current = current_services.get(service_name, None)
                value_new = action_map[action]

                # Value matches; no need to update
                if value_current == value_new:
                    message = 'Service already in desired state: {0} \'{1}\' = {2}'.format(action.upper(), service_name, label(value_current))
                    self.save_status(prefix='[SKIP] ', message=message)
                    continue

                # Execute command (will not execute in test mode)
                data = dict(key=service_name, value_old=label(value_current), value_new=label(value_new))
                cmd = '/usr/bin/qvm-service {0} --{1} {2}'.format(args.vmname, action, service_name)
                status = self.run(cmd, data=data)

        # Returns the status 'data' dictionary
        return self.status()


@_function_alias('run')
class _Run(_QVMBase):
    '''
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
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Run, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--auto', action='store_true', help='Auto start the VM if not running')
        parser.add_argument('--tray', action='store_true', help='Use tray notifications instead of stdout')
        parser.add_argument('--all', action='store_true', help='Run command on all currently running VMs (or all paused, in case of --unpause)')
        parser.add_argument('--pause', action='store_true', help="Do 'xl pause' for the VM(s) (can be combined this with --all)")
        parser.add_argument('--unpause', action='store_true', help="Do 'xl unpause' for the VM(s) (can be combined this with --all)")
        parser.add_argument('--pass-io', action='store_true', help='Pass stdin/stdout/stderr from remote program (implies -q)')
        parser.add_argument('--nogui', action='store_true', help='Run command without gui')
        parser.add_argument('--filter-escape-chars', action='store_true', help='Filter terminal escape sequences (default if output is terminal)')
        parser.add_argument('--no-filter-escape-chars', action='store_true', help='Do not filter terminal escape sequences - overrides --filter-escape-chars, DANGEROUS when output is terminal')
        parser.add_argument('--no-color-output', action='store_true', help='Disable marking VM output with red color')

        # Optional
        parser.add_argument('--user', nargs=1, help='Run command in a VM as a specified user')
        parser.add_argument('--localcmd', nargs=1, help='With --pass-io, pass stdin/stdout/stderr to the given program')
        parser.add_argument('--color-output', nargs=1, help='Force marking VM output with given ANSI style (use 31 for red)')
        parser.add_argument('--exclude', default=list, nargs='*', help='When --all is used: exclude this VM name (may be repeated)')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        parser.add_argument('cmd', nargs='*', default=list, type=list, help='Command to run')

    def __call__(self):
        args = self.args

        # Check VM power state and start if 'auto' is enabled
        if args.auto:
            start_status = self.save_status(start(args.vmname, **{'flags': ['quiet', 'no-guid']}))
            if start_status.failed():
                return self.status()

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-run {0}'.format(' '.join(self.arg_info['__argv']))
        status = self.run(cmd)

        # Returns the status 'data' dictionary
        return self.status()


@_function_alias('start')
class _Start(_QVMBase):
    '''
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
          - tray
          - no-guid
          - dvm
          - debug
          - install-windows-tools
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Start, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--tray', action='store_true', help='Use tray notifications instead of stdout')
        parser.add_argument('--no-guid', action='store_true', help='Do not start the GUId (ignored)')
        parser.add_argument('--install-windows-tools', action='store_true', help='Attach Windows tools CDROM to the VM')
        parser.add_argument('--dvm', action='store_true', help='Do actions necessary when preparing DVM image')
        parser.add_argument('--debug', action='store_true', help='Enable debug mode for this VM (until its shutdown)')

        # Optional
        parser.add_argument('--drive', help="Temporarily attach specified drive as CD/DVD or hard disk (can be specified with prefix 'hd:' or 'cdrom:', default is cdrom)")
        parser.add_argument('--hddisk', help='Temporarily attach specified drive as hard disk')
        parser.add_argument('--cdrom', help='Temporarily attach specified drive as CD/DVD')
        parser.add_argument('--custom-config', help='Use custom Xen config instead of Qubes-generated one')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

    def __call__(self):
        # Prevents startup status showing as 'Transient'
        def start_guid():
            try:
                if not self.vm().is_guid_running():
                    self.vm().start_guid()
            except AttributeError:
                # AttributeError: CEncodingAwareStringIO instance has no attribute 'fileno'
                pass

        def is_running(message='', error_message=''):
            running_status = state(args.vmname, *['running'])
            self.save_status(running_status, retcode=running_status.retcode, message=message, error_message=error_message)
            return running_status

        def is_transient():
            # Start guid if VM is 'transient'
            transient_status = state(args.vmname, *['transient'])
            if transient_status.passed():
                if __opts__['test']:
                    message = '\'guid\' will be started since in \'transient\' state!'
                    self.save_status(transient_status, message=message)
                    return self.status()

                # 'start_guid' then confirm 'running' power state
                start_guid()
                return not is_running(error_message='\'guid\' failed to start!')
            return False

        args = self.args

        # No need to start if VM is already 'running'
        if is_running():
            return self.status()

        # 'unpause' VM if its 'paused'
        paused_status = state(args.vmname, *['paused'])
        if paused_status.passed():
            resume_status = unpause(args.vmname)
            self.save_status(resume_status, error_message='VM failed to resume from pause!')
            if not resume_status:
                return self.status()

        if is_transient():
            return self.status()

        # XXX: TODO:
        # Got this failure to start... need to make sure messages are verbose, so
        # try testing in this state again once we get around to testing this function
        # if ret == -1: raise libvirtError ('virDomainCreateWithFlags() failed', dom=self)
        # libvirt.libvirtError: Requested operation is not valid: PCI device 0000:04:00.0 is in use by driver xenlight, domain salt-testvm4

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-start {0}'.format(' '.join(self.arg_info['__argv']))
        status = self.run(cmd)

        # Confirm VM has been started (don't fail in test mode)
        if not __opts__['test']:
            if is_transient():
                return self.status()

            is_running()

        # Returns the status 'data' dictionary
        return self.status()


@_function_alias('shutdown')
class _Shutdown(_QVMBase):
    '''
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
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Shutdown, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        parser.add_argument('--quiet', action='store_true', default=False, help='Quiet')
        parser.add_argument('--kill', action='store_true', default=False, help='Kill VM')
        parser.add_argument('--force', action='store_true', help='Force operation, even if may damage other VMs (eg shutdown of NetVM)')
        parser.add_argument('--wait', action='store_true', help='Wait for the VM(s) to shutdown')
        parser.add_argument('--all', action='store_true', help='Shutdown all running VMs')

        # Optional
        parser.add_argument('--exclude', action='store', default=[], nargs='*',
                            help='When --all is used: exclude this VM name (may be repeated)')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

    def __call__(self):
        def is_halted(message=''):
            halted_status = state(args.vmname, *['halted'])
            self.save_status(halted_status, retcode=halted_status.retcode, error_message=message)
            return halted_status

        def is_transient():
            # Kill if transient and 'force' option enabled
            transient_status = state(args.vmname, *['transient'])
            if transient_status.passed():
                modes = 'force' if args.force else ''
                modes += ' + ' if modes and args.kill else ''
                modes = 'kill' if args.kill else ''

                if __opts__['test']:
                    if force:
                        message = 'VM will be killed in \'transient\' state since {0} enabled!'.format(' + '.join(force))
                    else:
                        message = 'VM is \'transient\'. \'kill\' or \'force\' mode not enabled!'
                        transient_status.retcode = 1
                    self.save_status(transient_status, message=message)
                    return self.status()

                # 'kill' then confirm 'halted' power state
                cmd = '/usr/bin/qvm-kill {0}'.format(args.vmname)
                status = self.run(cmd)
                #return not is_halted(message='\'guid\' failed to halt!')
                return not self.save_status(is_halted(message='\'guid\' failed to halt!'))
            return False

        args = self.args
        differ = ListDiffer(['force', 'kill'], self.arg_info['__flags'])
        force = list(differ.unchanged())

        if __opts__['test']:
            if args.kill:
                message = 'VM is set to be killed'
            else:
                message = 'VM is set for shutdown'
            self.save_status(message=message)
            return self.status()

        # No need to start if VM is already 'halted'
        if is_halted():
            return self.status()

        # 'unpause' VM then if its 'paused', then confirm 'halted' power state
        paused_status = state(args.vmname, *['paused'])
        if paused_status.passed():
            self.vm().unpause()
            halted = self.save_status(is_halted(message='VM failed to resume from pause!'))
            return self.status()

        if is_transient():
            return self.status()

        # Execute command (will not execute in test mode)
        if self.args.kill:
            cmd = '/usr/bin/qvm-kill {0}'.format(args.vmname)
        else:
            cmd = '/usr/bin/qvm-shutdown {0}'.format(' '.join(self.arg_info['__argv']))
        status = self.run(cmd)

        # Kill if still not 'halted' only if 'force' enabled
        if not is_halted() and args.force:
            cmd = '/usr/bin/qvm-kill {0}'.format(args.vmname)
            status = self.run(cmd)

        is_halted()

        # Returns the status 'data' dictionary
        return self.status()


@_function_alias('kill')
class _Kill(_QVMBase):
    '''
    Kills a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.kill <vmname>

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Kill, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

    def __call__(self):
        args = self.args
        self.arg_info['kwargs'].setdefault('flags', [])
        self.arg_info['kwargs']['flags'].append('kill')

        # 'kill' VM
        halted_status = shutdown(args.vmname, *self.arg_info['varargs'], **self.arg_info['kwargs'])

        # Returns the status 'data' dictionary
        self.save_status(halted_status)
        return self.status()


@_function_alias('pause')
class _Pause(_QVMBase):
    '''
    Pause a virtual machine::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.pause <vm-name>

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Pause, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

    def __call__(self):
        args = self.args

        # Check VM power state
        def is_running(message=''):
            running_status = state(args.vmname, *['running', 'paused', 'transient'])
            self.save_status(running_status, retcode=running_status.retcode, error_message=message)
            return running_status

        # Can't pause VM if it's not running
        if not is_running():
            message = 'VM is not running'
            self.save_status(result=True, message=message)
            return self.status()

        if __opts__['test']:
            message = 'VM is set to be paused'
            self.save_status(message=message)
            return self.status()

        # Execute command (will not execute in test mode)
        self.vm().pause()

        paused_status = state(args.vmname, *['paused'])
        self.save_status(paused_status, retcode=paused_status.retcode)

        # Returns the status 'data' dictionary
        return self.status()


@_function_alias('unpause')
class _Unpause(_QVMBase):
    '''
    Unpause a virtual machine::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.unpause <vm-name>

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Unpause, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

    def __call__(self):
        # Check VM power state
        def is_paused(message=''):
            paused_status = state(args.vmname, *['paused'])
            self.save_status(paused_status, retcode=paused_status.retcode, error_message=message)
            return paused_status

        args = self.args

        # Can't resume VM if it's not paused
        if not is_paused():
            message = 'VM is not paused'
            self.save_status(result=True, message=message)
            return self.status()

        if __opts__['test']:
            message = 'VM set to be resumed'
            self.save_status(message=message)
            return self.status()

        # Execute command (will not execute in test mode)
        self.vm().unpause()

        running_status = state(args.vmname, *['running'])
        self.save_status(running_status, retcode=running_status.retcode, error_message='VM failed to resume from pause!')

        # Returns the status 'data' dictionary
        return self.status()
