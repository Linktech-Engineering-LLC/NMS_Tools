# Monitoring Integration Guide  

**Suite:** NMS_Tools Monitoring Suite
**Maintainer:** Leon McClatchey, Linktech Engineering LLC
**Document Type:** Monitoring Integration Guide
**Last Updated:** 2026‑08‑30

## 📘 Table of Contents
1. [Overview](#1-overview)
2. [Exit Codes](#2-exit-codes)
3. [Nagios Plugin Path](#3-nagios-plugin-path)
4. [check_cert — TLS Certificate Monitoring](#4-check_cert--tls-certificate-monitoring)
5. [check_html — HTTP/HTTPS Content Validation](#5-check_html--httphttps-content-validation)
6. [check_interfaces — Network Interface Monitoring](#6-check_interfaces--network-interface-monitoring)
7. [check_ports — Port Availability Monitoring](#7-check_ports--port-availability-monitoring)
8. [check_weather — Deterministic Weather Monitoring](#8-check_weather--deterministic-weather-monitoring)
9. [check_ticker — Ticker Movement Monitoring](#9-check_ticker--ticker-movement-monitoring)
10. [Best Practices](#10-best-practices)
11. [Icinga Integration](#11-icinga-integration)
12. [Zabbix / Sensu Notes](#12-zabbix--sensu-notes)
13. [Summary](#13-summary)

===

## 1. Overview

NMS_Tools provides deterministic, standalone monitoring utilities designed for production environments.  

All tools:
* return Nagios‑compatible exit codes  
* produce stable, machine‑readable output  
* behave consistently across distributions  
* require no Python runtime  
* install into `/usr/local/bin`  

This guide provides integration examples for **all tools** in the suite.

---

## 2. Exit Codes

| Code | Meaning |
| *---* | *--- |
| `0` | OK |
| `1` | WARNING |
| `2` | CRITICAL |
| `3` | UNKNOWN |

All tools follow this convention.

---

## 3. Nagios Plugin Path

NMS_Tools installs into:

/usr/local/bin

You may optionally create symlinks:

/usr/lib/nagios/plugins/check_cert -> /usr/local/bin/check_cert

…but this is not required.  
All examples below reference the canonical install path.

---

## 4. check_cert — TLS Certificate Monitoring

### Command Definition

```bash
define command {
    command_name    check_cert
    command_line    /usr/local/bin/check_cert --host $HOSTADDRESS$ --port $ARG1$
}
```

### Service Definition

```bash
define service {
    use                     generic-service
    host_name               webserver01
    service_description     TLS Certificate
    check_command           check_cert!443
}
```

### Example Outputs

#### OK:

```Code
OK - Certificate valid (expires in 42 days)
```

#### WARNING:

```Code
WARNING - Certificate expires in 7 days
```

#### CRITICAL:

```Code
CRITICAL - Certificate expired 2 days ago
```

## 5. check_html — HTTP/HTTPS Content Validation

### Command Definition

```bash
define command {
    command_name    check_html
    command_line    /usr/local/bin/check_html --url $ARG1$ --expect-title "$ARG2$"
}
```

### Service Definition

```bash
define service {
    use                     generic-service
    host_name               webserver01
    service_description     Homepage HTML Check
    check_command           check_html!https://example.com!Example Domain
}
```

### Example Outputs

#### OK:

```Code
OK - Title matches: Example Domain
```

#### CRITICAL:

```Code
CRITICAL - Title mismatch (expected 'Example Domain', got 'Example')
```

## 6. check_interfaces — Network Interface Monitoring

### Command Definition

```bash
define command {
    command_name    check_interfaces
    command_line    /usr/local/bin/check_interfaces
}
```

### Service Definition

```bash
define service {
    use                     generic-service
    host_name               server01
    service_description     Interface Status
    check_command           check_interfaces
}
```

### Example Outputs

#### OK:

```Code
OK - eth0 UP (1000Mbps), lo UP
```

#### CRITICAL:

```Code
CRITICAL - eth1 DOWN
```

## 7. check_ports — Port Availability Monitoring

### Command Definition

```bash
define command {
    command_name    check_ports
    command_line    /usr/local/bin/check_ports --host $HOSTADDRESS$ --port $ARG1$
}
```

### Service Definition

```bash
define service {
    use                     generic-service
    host_name               server01
    service_description     SSH Port Check
    check_command           check_ports!22
}
```

### Example Outputs

#### OK:

```Code
OK - Port 22 open (SSH)
```

#### CRITICAL:

```Code
CRITICAL - Port 22 closed
```

## 8. check_weather — Deterministic Weather Monitoring

Useful for:

* environmental monitoring
* HVAC systems
* outdoor equipment
* weather‑dependent automation

### Command Definition

```bash
define command {
    command_name    check_weather
    command_line    /usr/local/bin/check_weather --city "$ARG1$"
}
```

### Service Definition

```bash
define service {
    use                     generic-service
    host_name               ops-dashboard
    service_description     Weather Status
    check_command           check_weather!Wichita, KS
}
```

### Example Outputs

#### OK:

```Code
OK - Clear sky, 72°F
```

#### WARNING:

```Code
WARNING - High wind advisory (28 mph)
```

#### CRITICAL:

```Code
CRITICAL - Severe weather alert: Thunderstorm Warning
```

## 9. check_ticker — Ticker Movement Monitoring

Useful for:
* financial dashboards
* movement‑based alerting
* backend ingestion validation
* ticker‑driven automation

### Command Definition

```bash
define command {
    command_name    check_ticker
    command_line    /usr/local/bin/check_ticker --symbol "$ARG1$"
}
```

### Service Definition

```bash
define service {
    use                     generic-service
    host_name               ops-dashboard
    service_description     Ticker Movement
    check_command           check_ticker!AAPL
}
```

### Example Outputs

#### OK

```code
OK - AAPL stable (movement +0.12%)
```

#### WARNING

```code
WARNING - AAPL volatility elevated (movement +4.8%)
```

#### CRITICAL

```code
CRITICAL - AAPL severe drop detected (movement -9.3%)
```

## 10. Best Practices

### Use explicit timeouts

```Code
check_command check_cert!443! -t 10
```

### Use retry intervals for weather and HTML checks

These are subject to transient network conditions.

### Keep thresholds deterministic

Avoid fuzzy logic — NMS_Tools is designed for precision.

### Prefer service‑specific hostgroups

```Code
hostgroup_name web-servers
```

## 11. Icinga Integration

Icinga uses the same command definitions as Nagios.

Example:

```bash
object CheckCommand "check_cert" {
    command = [ "/usr/local/bin/check_cert" ]
    arguments = {
        "--host" = "$address$"
        "--port" = "$cert_port$"
    }
}
```

## 12. Zabbix / Sensu Notes

These tools can call NMS_Tools binaries directly:

```Code
UserParameter=check_cert[*],/usr/local/bin/check_cert --host $1 --port $2
```

## 13. Summary

NMS_Tools integrates cleanly with:

* Nagios
* Icinga
* Zabbix
* Sensu
* Custom monitoring pipelines

All tools behave deterministically and produce stable, machine‑readable output suitable for production environments.