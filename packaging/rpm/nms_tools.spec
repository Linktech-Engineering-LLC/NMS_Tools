Name:           nms_tools
Version:        1.0.0
Release:        1%{?dist}
Summary:        Deterministic network monitoring and inspection tool suite

License:        MIT
URL:            https://www.linktechengineering.net/projects/nms-tools/
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

Requires:       python3
Requires:       python3-requests
Requires:       python3-pyyaml

%description
NMS_Tools is a deterministic, audit-transparent suite of monitoring and
inspection utilities designed for operator-grade workflows. Tools include:

- check_ports: multi-port TCP checker
- check_weather: deterministic weather evaluator
- check_cert: TLS certificate inspector
- check_html: HTTP/HTTPS validator
- check_interfaces: SNMP interface state checker

All tools follow strict engineering principles: predictable behavior, clean
output modes, JSON support, and monitoring-friendly exit codes.

%prep
%setup -q

%build
# Build man pages using the project's Makefile
make man

%install
# Install executables
install -d %{buildroot}/usr/bin
install -m 0755 check_ports/check_ports.py %{buildroot}/usr/bin/check_ports
install -m 0755 check_weather/check_weather.py %{buildroot}/usr/bin/check_weather
install -m 0755 check_cert/check_cert.py %{buildroot}/usr/bin/check_cert
install -m 0755 check_html/check_html.py %{buildroot}/usr/bin/check_html
install -m 0755 check_interfaces/check_interfaces.py %{buildroot}/usr/bin/check_interfaces

# Install man pages
install -d %{buildroot}/usr/share/man/man1
install -d %{buildroot}/usr/share/man/man7
install -m 0644 man/*.1 %{buildroot}/usr/share/man/man1/
install -m 0644 man/*.7 %{buildroot}/usr/share/man/man7/

%files
%license LICENSE
%doc README.md

/usr/bin/check_ports
/usr/bin/check_weather
/usr/bin/check_cert
/usr/bin/check_html
/usr/bin/check_interfaces

/usr/share/man/man1/check_ports.1*
/usr/share/man/man1/check_weather.1*
/usr/share/man/man1/check_cert.1*
/usr/share/man/man1/check_html.1*
/usr/share/man/man1/check_interfaces.1*

/usr/share/man/man7/nms_tools.7*

%changelog
* Mon Apr 20 2026 Leon McClatchey <engineering@linktechengineering.net> - 1.0.0-1
- Initial RPM release of NMS_Tools
