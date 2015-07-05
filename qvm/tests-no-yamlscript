# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Qubes state, and module tests [not using yamlscript]
##

#salt-testvm2:
#  qvm.vm:
#    - check: []
#    - missing: []
#    - running: []
#    - dead: []

qvm-remove-id:
  qvm.remove:
    - name: salt-testvm

qvm-create-id:
  qvm.create:
    - name: salt-testvm
    - template: fedora-21
    - label: red
    - mem: 3000
    - vcpus: 4
    - options:
      - proxy


# Test qubes-dom0-update
$if 'qubes-dom0-update' in tests:
  git:
    pkg.installed:
      - name: git

$if 'qvm-remove' in tests:
  qvm-remove-id:
    qvm.remove:
      - name: $test_vm_name

$if 'qvm-create' in tests:
  qvm-create-id:
    qvm.create:
      - name: $test_vm_name
      - template: fedora-21
      - label: red
      - mem: 3000
      - vcpus: 4
      - options:
        - proxy

$if 'qvm-prefs' in tests:
  qvm-prefs-id:
    qvm.prefs:
      - name: $test_vm_name
      - label: green
      - template: debian-jessie
      - memory: 400
      - maxmem: 4000
      - include_in_backups: False

$if 'qvm-service' in tests:
  qvm-service-id:
    qvm.service:
      - name: $test_vm_name
      - disable:
        - test
        - test2
        - another_test
        - another_test2
        - another_test3
      - enable:
        - meminfo-writer
        - test3
        - test4
        - another_test4
        - another_test5

$if 'qvm-start' in tests:
  qvm-start-id:
    qvm.start:
      - name: $test_vm_name
      # options:
        # tray
        # no-guid
        # dvm
        # debug
        # install-windows-tools
        # drive: DRIVE
        # hddisk: DRIVE_HD
        # cdrom: DRIVE_CDROM
        # custom-config: CUSTOM_CONFIG

# TODO: TEST AUTO-START
$if 'qvm-run' in tests:
  qvm-run-id:
    qvm.run:
      - name: $test_vm_name
      - cmd: gnome-terminal

$if 'qvm-vm' in tests:
  qvm-vm-id:
    qvm.vm:
      - name: $test_vm_name
      - remove: []
      - create:
        - template: fedora-21
        - label: red
        - mem: 3000
        - vcpus: 4
        - options:
          - proxy
      # prefs:
        # label: green
        # template: debian-jessie
        # memory: 400
        # maxmem: 4000
        # include_in_backups: False
      # service:
        # disable:
          # test
          # test2
          # another_test
          # another_test2
          # another_test3
        # enable:
          # meminfo-writer
          # test3
          # test4
          # another_test4
          # another_test5
      - start: []
        # options:
          # tray
          # no-guid
          # dvm
          # debug
          # install-windows-tools
          # drive: DRIVE
          # hddisk: DRIVE_HD
          # cdrom: DRIVE_CDROM
          # custom-config: CUSTOM_CONFIG
      # TODO: TEST AUTO-START
      - run:
        - cmd: gnome-terminal

# ==============================================================================

#salt-testvm-pause:
#  qvm.vm:
#    - name: salt-testvm
#    - pause: []

#salt-testvm:
#  qvm.vm:
#    # shutdown: []
#    # kill: []
#    # start: []
#    # kill: []
#    # pause: []
#    # unpause: []
#    - run:
#      - cmd: gnome-terminal
#      - options:
#        - user: user
#        # exclude: [sys-net, sys-firewall]
#        # localcmd: /dev/null
#        # color-output: '31'
#        # quiet
#        # auto
#        # tray
#        # all
#        # pause
#        # unpause
#        # pass-io
#        # nogui
#        # filter-escape-chars
#        # no-filter-escape-chars
#        # no-color-output

#salt-testvm2:
#  qvm.vm:
#    - check: []
#    - missing: []
#    - running: []
#    - dead: []

#salt-testvm3:
#  qvm.vm:
#    - remove: []

#salt-testvm4:
#  qvm.vm:
#    - clone:
#      - target: test-clone

# ==============================================================================

#salt-testvm-remove:
#  qvm.remove:
#    - name: salt-testvm

#fedora-20-x64:
#  qvm.clone:
#    - target: fedora-clone
#fedora-clone:
#  qvm.remove: []

# Test prefs
#fc21:
#  qvm.prefs:
#    # label: oranges  # Deliberate error
#    - label: orange
#    - template: debian-jessie
#    - memory: 400
#    - maxmem: 4000
#    - include_in_backups: False
#  qvm.check: []

#fc21-prefs:
#  qvm.prefs:
#    - name: fc21
#    - label: green
#    - template: debian-jessie
#    - memory: 400
#    - maxmem: 4000
#    - include_in_backups: True

#fc21-check:
#  qvm.check:
#    - name: fc21

#fc211-missing:
#  qvm.missing:
#    - name: fc211

#fc21-running:
#  qvm.running:
#    - name: fc21

#fc21-dead:
#  qvm.dead:
#    - name: fc21

# Deliberate Fail
#fc211-running:
#  qvm.running:
#    - name: fc211

#netvm-running:
#  qvm.running:
#    - name: netvm

#fc21-service-test:
#  qvm.service:
#    - name: fc21
#    - enable:
#      - test
#      - another_test
#    - disable: meminfo-writer

#fc21-start:
#  qvm.start:
#    - name: fc21
#    # options:
#    # - tray
#    # - no-guid
#    # - dvm
#    # - debug
#    # - install-windows-tools
#    # - drive: DRIVE
#    # - hddisk: DRIVE_HD
#    # - cdrom: DRIVE_CDROM
#    # - custom-config: CUSTOM_CONFIG

# Test new state and module to verify detached signed file
#test-file:
#  gpg.verify:
#    - source: salt://vim/init.sls.asc
#    # homedir: /etc/salt/gpgkeys
#    - require:
#      - pkg: gnupg

# Test new state and module to import gpg key
# (moved to salt/gnupg.sls)
#nrgaway_key:
#  gpg.import_key:
#    - source: salt://dom0/nrgaway-qubes-signing-key.asc
#    # homedir: /etc/salt/gpgkeys

# Test new renderer that automatically verifies signed state files
# (vim/init.sls{.asc} is the test file for this)
