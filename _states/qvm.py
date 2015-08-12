# -*- coding: utf-8 -*-
#
# vim: set ts=4 sw=4 sts=4 et :
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:platform:      all

===========================
Qubes qvm-* state functions
===========================

Salt can manage many Qubes settings via the qvm state module.

Management declarations are typically rather simple:

.. code-block:: yaml

    appvm:
      qvm.prefs
        - label: green


=====
TODO:
=====

States and functions to implement (qvm-commands):

[ ] Not Implemented
[X] Implemented
[1-9] Next to Implement

[ ] qvm-add-appvm       [X] qvm-create              [ ] qvm-ls                       [X] qvm-shutdown
[ ] qvm-add-template    [ ] qvm-create-default-dvm  [ ] qvm-pci                      [X] qvm-start
[ ] qvm-backup          [ ] qvm-firewall            [X] qvm-prefs                    [ ] qvm-sync-appmenus
[ ] qvm-backup-restore  [ ] qvm-grow-private        [X] qvm-remove                   [ ] qvm-sync-clock
[ ] qvm-block           [ ] qvm-grow-root           [ ] qvm-revert-template-changes  [ ] qvm-template-commit
[X] qvm-check           [ ] qvm-init-storage        [X] qvm-run                      [ ] qvm-trim-template
[X] qvm-clone           [X] qvm-kill                [X] qvm-service                  [ ] qvm-usb

[X] qvm-pause
[X] qvm-unpause

[X] qvm-present (qvm-create)
[X] qvm-absent (qvm-remove)
[X] qvm-exists (qvm-check)
[X] qvm-missing (qvm-check)
'''

# Import python libs
import collections
import logging

# Salt libs
from salt.output import nested
from salt.utils.odict import OrderedDict as _OrderedDict
from salt.exceptions import (
    CommandExecutionError, SaltInvocationError
)

# Salt + Qubes libs
import qubes_utils

from qubes_utils import Status

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only make these states available if a qvm provider has been detected or
    assigned for this minion
    '''
    # XXX: TEMP
    if not hasattr(qubes_utils, '__opts__'):
        qubes_utils.__opts__ = __opts__
    if not hasattr(qubes_utils, '__salt__'):
        qubes_utils.__salt__ = __salt__

    return 'qvm.prefs' in __salt__


def _nested_output(obj):
    '''
    Serialize obj and format for output.
    '''
    nested.__opts__ = __opts__
    ret = nested.output(obj).rstrip()
    return ret


def _state_action(_action, *varargs, **kwargs):
    '''
    State utility to standardize calling Qubes modules.

    Python State Example:

    .. code-block:: python

        from qubes_state_utils import state_action as _state_action

        def exists(name, *varargs, **kwargs):
            varargs = list(varargs)
            varargs.append('exists')
            return _state_action('qvm.check', name, *varargs, **kwargs)
    '''
    try:
        status = __salt__[_action](*varargs, **kwargs)
    except (SaltInvocationError, CommandExecutionError), e:
        status = Status(retcode=1, result=False, stderr=e.message + '\n')
    return vars(status)


def exists(name, *varargs, **kwargs):
    '''
    Verify the named VM is present or exists. This returns True only if the
    named VM existst but does not create the VM if missing (qvm-exists).
    '''
    varargs = list(varargs)
    varargs.append('exists')
    return _state_action('qvm.check', name, *varargs, **kwargs)


def missing(name, *varargs, **kwargs):
    '''
    Verify the named VM is missing. This returns True only if the named VM is
    missing but does not remove the VM if present (qvm-mising).
    '''
    varargs = list(varargs)
    varargs.append('missing')
    return _state_action('qvm.check', name, *varargs, **kwargs)


def running(name, *varargs, **kwargs):
    '''
    Returns True is vmname is running (qvm-running).
    '''
    varargs = list(varargs)
    varargs.append('running')
    return _state_action('qvm.state', name, *varargs, **kwargs)


def halted(name, *varargs, **kwargs):
    '''
    Returns True is vmname is halted (qvm-halted).
    '''
    varargs = list(varargs)
    varargs.append('halted')
    # Return if VM already halted (stderr will contain message if VM absent)
    halted_status = Status(**_state_action('qvm.state', name, *varargs, **kwargs))
    if halted_status.passed() or halted_status.stderr:
        message = halted_status.stderr or "'{0}' is already halted.".format(name)
        status = Status()._format(prefix='[SKIP] ', message=message)
        return vars(status._finalize(test_mode=__opts__['test']))
    return _state_action('qvm.state', name, *varargs, **kwargs)


def start(name, *varargs, **kwargs):
    '''
    Start vmname (qvm-start).
    '''
    kwargs.setdefault('flags', [])
    kwargs['flags'].extend(['quiet', 'no-guid'])
    return _state_action('qvm.start', name, *varargs, **kwargs)


def shutdown(name, *varargs, **kwargs):
    '''
    Shutdown vmname (qvm-shutdown).
    '''
    kwargs.setdefault('flags', [])
    kwargs['flags'].append('wait')
    return _state_action('qvm.shutdown', name, *varargs, **kwargs)


def kill(name, *varargs, **kwargs):
    '''
    Kill vmname (qvm-kill).
    '''
    # Return if VM already halted (stderr will contain message if VM absent)
    halted_status = Status(**_state_action('qvm.state', name, *['halted']))
    if halted_status.passed():
        message = halted_status.stderr or "'{0}' is already halted.".format(name)
        status = Status()._format(prefix='[SKIP] ', message=message)
        return vars(status._finalize(test_mode=__opts__['test']))
    return _state_action('qvm.kill', name, *varargs, **kwargs)


def pause(name, *varargs, **kwargs):
    '''
    Pause vmname (qvm-pause).
    '''
    return _state_action('qvm.pause', name, *varargs, **kwargs)


def unpause(name, *varargs, **kwargs):
    '''
    Unpause vmname (qvm-unpause).
    '''
    return _state_action('qvm.unpause', name, *varargs, **kwargs)


def present(name, *varargs, **kwargs):
    '''
    Make sure the named VM is present. If it is missing, it will be created
    (qvm-present).
    '''
    # Return if VM already exists
    exists_status = Status(**_state_action('qvm.check', name, *['exists']))
    if exists_status.passed():
        message = "A VM with the name '{0}' already exists.".format(name)
        status = Status()._format(prefix='[SKIP] ', message=message)
        return vars(status._finalize(test_mode=__opts__['test']))
    return _state_action('qvm.create', name, *varargs, **kwargs)


def absent(name, *varargs, **kwargs):
    '''
    Make sure the named VM is absent. If it exists, it will be deleted.
    (qvm-absent).
    '''
    # Return if VM already absent
    missing_status = Status(**_state_action('qvm.check', name, *['missing']))
    if missing_status.passed():
        message = "The VM with the name '{0}' is already missing.".format(name)
        status = Status()._format(prefix='[SKIP] ', message=message)
        return vars(status._finalize(test_mode=__opts__['test']))
    return _state_action('qvm.remove', name, *varargs, **kwargs)


def clone(name, source, *varargs, **kwargs):
    '''
    Clone a VM (qvm-clone).
    '''
    # Return if VM already exists
    exists_status = Status(**_state_action('qvm.check', name, *['exists']))
    if exists_status.passed():
        message = "A VM with the name '{0}' already exists.".format(name)
        status = Status()._format(prefix='[SKIP] ', message=message)
        return vars(status._finalize(test_mode=__opts__['test']))
    return _state_action('qvm.clone', source, name, *varargs, **kwargs)


def run(name, *varargs, **kwargs):
    '''
    Run command in virtual machine domain (qvm-run).
    '''
    return _state_action('qvm.run', name, *varargs, **kwargs)


def prefs(name, *varargs, **kwargs):
    '''
    Sets vmname preferences (qvm-prefs).
    '''
    return _state_action('qvm.prefs', name, *varargs, **kwargs)


def service(name, *varargs, **kwargs):
    '''
    Manage vmname service (qvm-service).
    '''
    return _state_action('qvm.service', name, *varargs, **kwargs)


def vm(name, *varargs, **kwargs):
    '''
    Wrapper to contain all VM state functions.

    State:

        exists
        missing

        present
        absent
        clone

        prefs
        service

    Power:

        running
        halted

        start
        shutdown
        kill
        pause
        unpause

        run
    '''
    def get_action(action):
        action_value = 'fail'
        if isinstance(action, collections.Mapping):
            action, action_value = action.items()[0]
        return action, action_value

    actions = [
        'exists',
        'running',
        'missing',
        'halted',
        'absent',
        'present',
        'clone',
        'prefs',
        'service',
        'unpause',
        'pause',
        'shutdown',
        'kill',
        'start',
        'run',
    ]

    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    if __opts__['test']:
        ret['result'] =  None

    # Action ordering from state file
    actions = kwargs.pop('actions', actions)

    # Store only the actions; no values
    _actions = []
    for action in actions:
        action, action_value = get_action(action)
        _actions.append(action)

    for action in kwargs.keys():
        if action not in _actions:
            ret['result'] = False
            ret['comment'] = 'Unknown action keyword: {0}'.format(action)
            return   ret

    def parse_options(options):
        varargs = []
        keywords = _OrderedDict()
        for option in options:
            if isinstance(option, collections.Mapping):
                keywords.update(option)
            else:
                varargs.append(option)
        return varargs, keywords

    for index, action in enumerate(actions):
        action, action_value = get_action(action)

        if action in kwargs:
            # Parse kwargs and create varargs + keywords
            _varargs, keywords = parse_options(kwargs[action])

            # Execute action
            if ret['result'] or __opts__['test']:
                status = globals()[action](name, *_varargs, **keywords)
            else:
                linefeed = '\n\n' if ret['comment'] else ''
                ret['comment'] += '{0}====== [\'{1}\'] ======\n'.format(linefeed, action)
                ret['comment'] += '[SKIP] Skipping due to previous failure!'
                continue

            # Don't fail if action_value set to pass
            if not status['result'] and 'pass' not in action_value.lower():
                ret['result'] = status['result']

            if 'changes' in status and status['changes']:
                ret['changes']['qvm.' + action] = status['changes']

            linefeed = '\n\n' if ret['comment'] else ''
            ret['comment'] += '{0}====== [\'{1}\'] ======\n'.format(linefeed, action)

            if 'comment' in status and status['comment'].strip():
                ret['comment'] += status['comment']
            elif 'stdout' in status and status['stdout'].strip():
                ret['comment'] += status['stdout'].strip()
            elif 'stderr' in status and status['stderr'].strip():
                ret['comment'] += status['stderr'].strip()

    return ret
