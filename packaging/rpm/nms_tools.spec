Name:           nms_tools
Version:        1.0.0
Release:        1%{?dist}
Summary:        Deterministic operator-grade monitoring tools

License:        MIT
URL:            https://www.linktechengineering.net/projects/nms-tools/
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3
BuildRequires:  pandoc

%description
NMS_Tools is a suite of deterministic, operator-grade monitoring tools for
Linux and Nagios environments. Each tool is self-contained, reproducible,
and designed for automation workflows.

%prep
%setup -q

%build
# Nothing to build (Python scripts + man pages already generated)

%install
mkdir -p %{buildroot}/usr/local/bin
mkdir -p %{buildroot}/usr/share/man/man1
mkdir -p %{buildroot}/usr/share/man/man7

# Install all tools dynamically
install -m 0755 check_*/check_*.py %{buildroot}/usr/local/bin/

# Install generated man pages
install -m 0644 man/generated/*.1 %{buildroot}/usr/share/man/man1/
install -m 0644 man/generated/*.7 %{buildroot}/usr/share/man/man7/

# Compress man pages
gzip -9 %{buildroot}/usr/share/man/man1/*.1
gzip -9 %{buildroot}/usr/share/man/man7/*.7

%files
%license LICENSE.md
%doc README.md

/usr/local/bin/check_*.py
/usr/share/man/man1/check_*.1.gz
/usr/share/man/man7/*.7.gz

%changelog
* Tue Apr 21 2026 Linktech Engineering <support@linktechengineering.net> - 1.0.0-1
- Initial dynamic packaging system
