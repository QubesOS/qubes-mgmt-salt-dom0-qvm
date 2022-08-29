===========
QVM Formula
===========

Salt can manage many Qubes settings via the qvm state module.

Management declarations are typically rather simple:

.. code-block:: yaml

    appvm:
      qvm.prefs
        - label: green

.. note::

Also see _modules/ext_module_qvm.py for inline documentation

Available State Commands
========================

.. contents::
    :local:

``qvm.exists``
--------------

Verify the named VM is present or exists.
Return True only if the named VM exists.  Will not create the VM if missing.

.. code-block:: yaml

    qvm.exists:
        - name: <vmname>
            - flags:
                - quiet

``qvm.missing``
---------------

Verify the named VM is missing.
Return True only if the named VM is missing.  Will not remove the VM if present.

.. code-block:: yaml

    qvm-missing-id:
        qvm.missing:
            - name: <vmname>
            - flags:
                - quiet

``qvm.running``
---------------

Return True is vmname is running.

.. code-block:: yaml

    qvm-running-id:
        qvm.running:
            - name: <vmname>

``qvm.halted``
--------------

Return True is vmname is halted.

.. code-block:: yaml

    qvm-halted-id:
        qvm.halted:
            - name: <vmname>

``qvm.start``
-------------

Start vmname.

.. code-block:: yaml

    qvm-start-id:
        qvm.start:
            - name: <vmname>
            - drive: <string>
            - hddisk: <string>
            - cdrom: <string>
            - custom-config: <string>
            - flags:
                - quiet  # *** salt default ***
                - no-guid  # *** salt default ***
                - tray
                - dvm
                - debug
                - install-windows-tools

``qvm.shutdown``
----------------

Shutdown vmname.

.. code-block:: yaml

    qvm-shutdown-id:
        qvm.shutdown:
            - name: <vmname>
            - exclude: [exclude_list,]
            - flags:
                - quiet
                - force
                - wait
                - all
                - kill

``qvm.kill``
------------

Kill vmname.

.. code-block:: yaml

    qvm-kill-id:
        qvm.kill:
            - name: <vmname>

``qvm.pause``
-------------

Pause vmname.

.. code-block:: yaml

    qvm-pause-id:
        qvm.pause:
            - name: <vmname>

``qvm.unpause``
---------------

Unpause vmname.

.. code-block:: yaml

    qvm-unpause-id:
        qvm.unpause:
            - name: <vmname>

``qvm.present``
---------------

Make sure the named VM is present.  VM will be created if missing.

.. code-block:: yaml

    qvm-present-id:
        qvm.present:
            - name: <vmname>
            - template: fedora-21
            - label: red
            - mem: 3000
            - vcpus: 4
            - root-move-from: </path/xxx>
            - root-copy-from: </path/xxx>
            - flags:
                - proxy
                - hvm
                - hvm-template
                - net
                - standalone
                - internal
                - force-root
                - quiet

``qvm.absent``
--------------

Make sure the named VM is absent.  VM will be deleted (removed) if present.

.. code-block:: yaml

    qvm-absent-id:
        qvm.absent:
            - name: <vmname>
            - flags:
                - just-db
                - force-root
                - quiet

``qvm.clone``
-------------

Clone a VM.

.. code-block:: yaml

    qvm-clone-id:
        qvm.clone:
            - name: <vmname>-clone
            - source: <vmname>
            - path: </path/xxx>
            - flags:
                - shutdown
                - quiet
                - force-root

``qvm.run``
-----------

Run command in virtual machine domain.

.. code-block:: yaml

    qvm-run-id:
        qvm.run:
            - name: <vmname>
            - cmd: gnome-terminal
            - user: <string>
            - exclude: [sys-net, sys-firewall]
            - localcmd: </dev/null>
            - color-output: 31
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

``qvm.prefs``
-------------

Set vmname preferences. Use `*default*` special value to reset property to its
default value.

.. code-block:: yaml

    qvm-prefs-id:
        qvm.prefs:
            - name:               <vmname>
            - label:              orange
            - template:           debian-jessie
            - memory:             400
            - maxmem:             4000
            - include-in-backups: True
            - netvm:              sys-firewall
            - pcidevs:            ['04:00.0']
            - kernel:             default
            - vcpus:              2
            - kernelopts:         nopat iommu=soft swiotlb=8192
            - mac:                auto
            - debug:              true
            - virt-mode:          hvm
            - default-user:       tester
            - qrexec-timeout:     120
            - internal:           true
            - autostart:          true
            - flags:
                - force-root

List vmname preferences.

.. code-block:: yaml

    qvm-prefs-list1-id:
        qvm.prefs:
            - name: <vmname>
            - action: list

    qvm-prefs-list2-id:
        qvm.prefs:
            - name: <vmname>

Get vmname preferences.

.. code-block:: yaml

    qvm-prefs-get-id:
        qvm.prefs:
            - name: <vmname>
            - get:
                - label
                - template
                - memory
                - maxmem
                - include-in-backups

``qvm.service``
---------------

Backward compatibility wrapper. Use features with `service.` prefix.

.. code-block:: yaml

    qvm-service-id:
        qvm.service:
            - name: <vmname>
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

``qvm.features``
---------------

Manage vmname features.

.. code-block:: yaml

    qvm-features-id:
        qvm.features:
            - name: <vmname>
            - enable:
                - test
                - test2
                - another_test
                - another_test2
                - another_test3
            - disable:
                - service.meminfo-writer
                - test3
                - test4
                - another_test4
                - another_test5
            - default:
                - another_test5
                - does_not_exist
            - set:
                - example.key: key value
                - example.test: test value
            # list: []
            # list: [string,]

``qvm.tags``
---------------

Manage vmname tags.

.. code-block:: yaml

    qvm-tags-id:
        qvm.tags:
            - name: <vmname>
            - add:
                - test
                - test2
                - another_test
                - another_test2
                - another_test3
            - del:
                - test3
                - test4
                - another_test4
                - another_test5
            # list: []
            # list: [string,]


``qvm.template_installed``
---------------

Ensure given template is installed.

.. code-block:: yaml

    qvm-template-installed:
        qvm.template_installed:
            - name: <template name>
            - fromrepo: <repository name>


``qvm.vm``
----------

Wrapper to contain all VM state functions.

- State:

    - exists
    - missing

    - present
    - absent
    - clone

    - prefs
    - service
    - features
    - tags

- Power:

    - running
    - halted

    - start
    - shutdown
    - kill
    - pause
    - unpause

    - run

Sample test VM creation containing all of the state actions:

.. code-block:: yaml

    qvm-vm-id:
        qvm.vm:
        - name: <vmname>
        - actions:
            - kill: pass
            - halted: pass
            - absent: pass
            - missing
            - present
            - exists
            - prefs
            - features
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
        - features:
            - enable:
                - test
                - test2
                - another_test
                - another_test2
                - another_test3
            - disable:
                - service.meminfo-writer
                - test3
                - test4
                - another_test4
                - another_test5
            - default:
                - another_test5
                - does_not_exist
        - tags:
            - add:
                - tag1
                - tag2
            - del:
                - tag3
                - tag4
        - start: []
        - running: []
        - pause: []
        - unpause: []
        - shutdown: []
        - run:
            - cmd: gnome-terminal
            - flags:
                - auto
