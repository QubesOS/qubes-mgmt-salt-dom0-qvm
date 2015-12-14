%{!?version: %define version %(cat version)}

Name:      qubes-mgmt-salt-dom0-qvm
Version:   %{version}
Release:   1%{?dist}
Summary:   Salt formula to interface to many of the Qubes dom0 qvm-* tools via a state file or module
License:   GPL 2.0
URL:	   http://www.qubes-os.org/

Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt
Requires:  qubes-mgmt-salt-dom0

%define _builddir %(pwd)

%description
Salt formula to interface to many of the Qubes dom0 qvm-* tools via a state file or module

%prep
# we operate on the current directory, so no need to unpack anything
# symlink is to generate useful debuginfo packages
rm -f %{name}-%{version}
ln -sf . %{name}-%{version}
%setup -T -D

%build

%install
make install DESTDIR=%{buildroot} LIBDIR=%{_libdir} BINDIR=%{_bindir} SBINDIR=%{_sbindir} SYSCONFDIR=%{_sysconfdir}

%post
# Update Salt Configuration
qubesctl state.sls config -l quiet --out quiet > /dev/null || true
qubesctl saltutil.clear_cache -l quiet --out quiet > /dev/null || true
qubesctl saltutil.sync_all refresh=true -l quiet --out quiet > /dev/null || true

# Enable Test States
#qubesctl top.enable qvm saltenv=test -l quiet --out quiet > /dev/null || true

%files
%defattr(-,root,root)
%doc LICENSE README.rst
%attr(750, root, root) %dir /srv/salt/_modules
/srv/salt/_modules/ext_module_qvm.py*

%attr(750, root, root) %dir /srv/salt/_states
/srv/salt/_states/ext_state_qvm.py*

%attr(750, root, root) %dir /srv/formulas/test/qvm-formula
/srv/formulas/test/qvm-formula/LICENSE
/srv/formulas/test/qvm-formula/README.rst
/srv/formulas/test/qvm-formula/qvm/tests-salt-call
/srv/formulas/test/qvm-formula/qvm/init.sls
/srv/formulas/test/qvm-formula/qvm/init.top

%changelog
