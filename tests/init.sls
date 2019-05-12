# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.tests
# =========
# 
# Qubes qvm-* state, and module tests
#
# Debug Environment:
#   qubesctl state.highstate
#   qubesctl state.highstate -l debug
#   qubesctl state.highstate test=true
#   qubesctl state.single test=true qvm.absent salt-testvm just-db
#
# Execute:
#   qubesctl state.sls qvm test
##

{% set test_vm_name = 'salt-testvm6' %}
{% set tests = [
        'debug-mode',
        'qvm-kill',
        'qvm-halted',
        'qvm-absent',
        'qvm-missing',
        'qvm-present',
        'qvm-exists',
        'qvm-prefs-list',
        'qvm-prefs-get',
        'qvm-prefs',
        'qvm-service',
        'qvm-start',
        'qvm-running',
        'qvm-pause',
        'qvm-unpause',
        'qvm-shutdown',
        'qvm-run',
        'qvm-clone',

        'qvm-vm',
    ]
%}

#===============================================================================
# Set salt state result debug mode (enable/disable)                   debug-mode
#===============================================================================
{% if 'debug-mode' in tests %}
qvm-test-debug-mode-id:
  debug.mode:
    - enable-all: true
    # enable: [qvm.absent, qvm.start]
    # disable: [qvm.absent]
    # disable-all: true
{% endif %}

#===============================================================================
# Kill VM                                                               qvm-kill
#===============================================================================
{% if 'qvm-kill' in tests %}
qvm-kill-id:
  qvm.kill:
    - name: {{ test_vm_name }}
{% endif %}

#===============================================================================
# Confirm VM is halted (halted)                                       qvm-halted
#===============================================================================
{% if 'qvm-halted' in tests %}
qvm-halted-id:
  qvm.halted:
    - name: {{ test_vm_name }}
{% endif %}

#===============================================================================
# Remove VM                                                           qvm-absent
#===============================================================================
{% if 'qvm-absent' in tests %}
qvm-absent-id:
  qvm.absent:
    - name: {{ test_vm_name }}
    # flags:
      # just-db
      # force-root
      # quiet
{% endif %}

#===============================================================================
# Confirm VM does not exist                                          qvm-missing
#===============================================================================
{% if 'qvm-missing' in tests %}
qvm-missing-id:
  qvm.missing:
    - name: {{ test_vm_name }}
    # flags:
      # quiet
{% endif %}

#===============================================================================
# Create VM                                                          qvm-present
#===============================================================================
{% if 'qvm-present' in tests %}
qvm-present-id:
  qvm.present:
    - name: {{ test_vm_name }}
    - template: fedora-21
    - label: red
    - mem: 3000
    - vcpus: 4
    # root-move-from: </path/xxx>
    # root-copy-from: </path/xxx>
    - flags:
      - proxy
      # hvm
      # hvm-template
      # net
      # standalone
      # internal
      # force-root
      # quiet
{% endif %}

#===============================================================================
# Confirm vm exists                                                   qvm-exists
#===============================================================================
{% if 'qvm-exists' in tests %}
qvm-exists-id:
  qvm.exists:
    - name: {{ test_vm_name }}
    # flags:
      # quiet
{% endif %}

#===============================================================================
# List VM preferences                                             qvm-prefs-list
#===============================================================================
{% if 'qvm-prefs-list' in tests %}
qvm-prefs-list1-id:
  qvm.prefs:
    - name:               {{ test_vm_name }}
    - action:             list
qvm-prefs-list2-id:
  qvm.prefs:
    - name:               {{ test_vm_name }}
{% endif %}

#===============================================================================
# Get VM preferences                                               qvm-prefs-get
#===============================================================================
{% if 'qvm-prefs-get' in tests %}
qvm-prefs-get-id:
  qvm.prefs:
    - name:               {{ test_vm_name }}
    - get:
      - label
      - template
      - memory
      - maxmem
      - include-in-backups
{% endif %}

#===============================================================================
# Modify VM preferences                                                qvm-prefs
#===============================================================================
{% if 'qvm-prefs' in tests %}
qvm-prefs-id:
  qvm.prefs:
    - name:               {{ test_vm_name }}
    - label:              orange
    - template:           debian-jessie
    - memory:             400
    - maxmem:             4000
    - include-in-backups: True
    - netvm:              sys-firewall
    # pcidevs:            ['04:00.0']
    # kernel:             default
    # vcpus:              2
    # kernelopts:         nopat iommu=soft swiotlb=8192
    # mac:                auto
    # debug:              true
    # default-user:       tester
    # qrexec-timeout:     120
    # internal:           true
    # autostart:          true
    # flags:
      # force-root

    # The following keys do not seem to exist in Qubes prefs DB
    # drive:              ''
    # timezone:           UTC
    # qrexec-installed:   true
    # guiagent-installed: true
    # seamless-gui-mode:  false
{% endif %}

#===============================================================================
# Modify VM services                                                 qvm-service
#===============================================================================
{% if 'qvm-service' in tests %}
qvm-service-id:
  qvm.service:
    - name: {{ test_vm_name }}
    - enable:
      - test
      - test2
      - another_test
      - another_test2
      - another_test3
    - disable:
      - meminfo-writer
      - test3
      - test4
      - another_test4
      - another_test5
    - default:
      - another_test5
      - does_not_exist
    # list: []
    # list: [string,]
{% endif %}

#===============================================================================
# Start VM                                                             qvm-start
#===============================================================================
{% if 'qvm-start' in tests %}
qvm-start-id:
  qvm.start:
    - name: {{ test_vm_name }}
    # drive: <string>
    # hddisk: <string>
    # cdrom: <string>
    # custom-config: <string>
    # flags:
      # quiet  # *** salt default ***
      # debug
      # install-windows-tools
{% endif %}

#===============================================================================
# Confirm VM is running                                              qvm-running
#===============================================================================
{% if 'qvm-running' in tests %}
qvm-running-id:
  qvm.running:
    - name: {{ test_vm_name }}
{% endif %}

#===============================================================================
# Pause VM                                                             qvm-pause
#===============================================================================
{% if 'qvm-pause' in tests %}
qvm-pause-id:
  qvm.pause:
    - name: {{ test_vm_name }}
{% endif %}

#===============================================================================
# Unpause VM                                                         qvm-unpause
#===============================================================================
{% if 'qvm-unpause' in tests %}
qvm-unpause-id:
  qvm.unpause:
    - name: {{ test_vm_name }}
{% endif %}

#===============================================================================
# Shutdown VM                                                       qvm-shutdown
#===============================================================================
{% if 'qvm-shutdown' in tests %}
qvm-shutdown-id:
  qvm.shutdown:
    - name: {{ test_vm_name }}
    # exclude: [exclude_list,]
    - flags:
      # quiet
      - force
      - wait
      # all
      # kill
{% endif %}

#===============================================================================
# Run 'gnome-terminal' in VM                                             qvm-run
#
# TODO: Test auto-start
#===============================================================================
{% if 'qvm-run' in tests %}
qvm-run-id:
  qvm.run:
    - name: {{ test_vm_name }}
    - cmd: gnome-terminal
    # user: <string>
    # exclude: [sys-net, sys-firewall]
    # localcmd: </dev/null>
    # color-output: 31
    - flags:
      # quiet
      - auto
      # tray
      # all
      # pause
      # unpause
      # pass-io
      # nogui
      # filter-escape-chars
      # no-filter-escape-chars
      # no-color-output
{% endif %}

#===============================================================================
# Clone VM                                                             qvm-clone
#===============================================================================
{% if 'qvm-clone' in tests %}
qvm-clone-id:
  qvm.clone:
    - name: {{ test_vm_name }}-clone
    - source: {{ test_vm_name }}
    # path:                 </path/xxx>
    - flags:
      - shutdown
      # quiet
      # force-root

qvm-clone-absent-id:
  qvm.absent:
    - name: {{ test_vm_name }}-clone
    - flags:
      - shutdown
{% endif %}

#===============================================================================
# Combined states (all qvm-* commands available within one id)           qvm-all
#===============================================================================
{% if 'qvm-vm' in tests %}
qvm-vm-id:
  qvm.vm:
    - name: {{ test_vm_name }}
    - actions:
      - kill: pass
      - halted: pass
      - absent: pass
      - missing
      - present
      - exists
      - prefs
      - service
      - start
      - running
      - pause
      - unpause
      - shutdown
      - run
      - clone
    - kill: []
    - halted: []
    - absent: []
    - missing: []
    - present:
      - template: fedora-21
      - label: red
      - mem: 3000
      - vcpus: 4
      - flags:
        - proxy
    - exists: []
    - prefs:
      - label: green  # red|yellow|green|blue|purple|orange|gray|black
      - template: debian-jessie
      - memory: 400
      - maxmem: 4000
      - include-in-backups: false
      - netvm: sys-firewall
    - service:
      - enable:
        - test
        - test2
        - another_test
        - another_test2
        - another_test3
      - disable:
        - meminfo-writer
        - test3
        - test4
        - another_test4
        - another_test5
      - default:
        - another_test5
        - does_not_exist
    - start: []
    - running: []
    - pause: []
    - unpause: []
    - shutdown: []
    - run:
      - cmd: gnome-terminal
      - flags:
        - auto
{% endif %}
