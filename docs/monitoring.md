# Monitoring Integration Guide  
Operator‑grade Nagios/Icinga integration for all NMS_Tools binaries.

NMS_Tools provides deterministic, standalone monitoring utilities designed for production environments.  
All tools:

- return Nagios‑compatible exit codes  
- produce stable, machine‑readable output  
- behave consistently across distributions  
- require no Python runtime  
- install into `/usr/local/bin`  

This guide provides integration examples for **all tools** in the suite.

---

# Exit Codes

| Code | Meaning |
|------|---------|
| `0` | OK |
| `1` | WARNING |
| `2` | CRITICAL |
| `3` | UNKNOWN |

All tools follow this convention.

---

# Nagios Plugin Path

NMS_Tools installs into:

/usr/local/bin


You may optionally create symlinks:

/usr/lib/nagios/plugins/check_cert -> /usr/local/bin/check_cert


…but this is not required.  
All examples below reference the canonical install path.

---

# 1. check_cert — TLS Certificate Monitoring

## Command Definition

```bash
define command {
    command_name    check_cert
    command_line    /usr/local/bin/check_cert --host $HOSTADDRESS$ --port $ARG1$
}
```

## Service Definition

```bash
define service {
    use                     generic-service
    host_name               webserver01
    service_description     TLS Certificate
    check_command           check_cert!443
}
```

## Example Outputs

### OK:

```Code
OK - Certificate valid (expires in 42 days)
```

### WARNING:

```Code
WARNING - Certificate expires in 7 days
```

### CRITICAL:

```Code
CRITICAL - Certificate expired 2 days ago
```

# 2. check_html — HTTP/HTTPS Content Validation

## Command Definition

```bash
define command {
    command_name    check_html
    command_line    /usr/local/bin/check_html --url $ARG1$ --expect-title "$ARG2$"
}
```

## Service Definition

```bash
define service {
    use                     generic-service
    host_name               webserver01
    service_description     Homepage HTML Check
    check_command           check_html!https://example.com!Example Domain
}
```

## Example Outputs

### OK:

```Code
OK - Title matches: Example Domain
```

### CRITICAL:

```Code
CRITICAL - Title mismatch (expected 'Example Domain', got 'Example')
```

# 3. check_interfaces — Network Interface Monitoring

## Command Definition

```bash
define command {
    command_name    check_interfaces
    command_line    /usr/local/bin/check_interfaces
}
```

## Service Definition

```bash
define service {
    use                     generic-service
    host_name               server01
    service_description     Interface Status
    check_command           check_interfaces
}
```

## Example Outputs

### OK:

```Code
OK - eth0 UP (1000Mbps), lo UP
```

### CRITICAL:

```Code
CRITICAL - eth1 DOWN
```

# 4. check_ports — Port Availability Monitoring

## Command Definition

```bash
define command {
    command_name    check_ports
    command_line    /usr/local/bin/check_ports --host $HOSTADDRESS$ --port $ARG1$
}
```

## Service Definition

```bash
define service {
    use                     generic-service
    host_name               server01
    service_description     SSH Port Check
    check_command           check_ports!22
}
```

## Example Outputs

### OK:

```Code
OK - Port 22 open (SSH)
```

### CRITICAL:

```Code
CRITICAL - Port 22 closed
```

# 5. check_weather — Deterministic Weather Monitoring

Useful for:

* environmental monitoring
* HVAC systems
* outdoor equipment
* weather‑dependent automation

## Command Definition

```bash
define command {
    command_name    check_weather
    command_line    /usr/local/bin/check_weather --city "$ARG1$"
}
```

## Service Definition

```bash
define service {
    use                     generic-service
    host_name               ops-dashboard
    service_description     Weather Status
    check_command           check_weather!Wichita, KS
}
```

## Example Outputs

### OK:

```Code
OK - Clear sky, 72°F
```

### WARNING:

```Code
WARNING - High wind advisory (28 mph)
```

### CRITICAL:

```Code
CRITICAL - Severe weather alert: Thunderstorm Warning
```

# Best Practices

## 1. Use explicit timeouts

Nagios example:

```Code
check_command check_cert!443! -t 10
```

## 2. Use retry intervals for weather and HTML checks

These are subject to transient network conditions.

## 3. Keep thresholds deterministic

Avoid fuzzy logic — NMS_Tools is designed for precision.

## 4. Prefer service‑specific hostgroups

Example:

```Code
hostgroup_name web-servers
```

# Icinga Integration

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

# Zabbix / Sensu Notes

These tools can call NMS_Tools binaries directly:

```Code
UserParameter=check_cert[*],/usr/local/bin/check_cert --host $1 --port $2
```

# Summary

NMS_Tools integrates cleanly with:

* Nagios
* Icinga
* Zabbix
* Sensu
* Custom monitoring pipelines

All tools behave deterministically and produce stable, machine‑readable output suitable for production environments.