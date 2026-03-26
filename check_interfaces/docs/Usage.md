# Usage.md — CLI Reference & Examples

## Synopsis

`check_interfaces.py -H <host> [options]`


---

## Required Arguments

| Flag            | Description                                                            |
|-----------------|------------------------------------------------------------------------|
| -H, --host      | Target hostname or IP address. Determines local vs remote detection automatically. A resolvable hostname is required. |

---

## Core Options

| Flag                | Description                                      | Default |
|---------------------|--------------------------------------------------|---------|
| -t, --timeout       | General connection timeout in seconds            | 5       |
| --log-dir DIR       | Directory to store logs (verbose/JSON only)      | —       |
| --log-max-mb MB     | Maximum log size before rotation                 | 50      |

Logging is disabled in Nagios mode.

---

## SNMP Options

Required for remote hosts. Ignored when the target is detected as local.

| Flag                    | Description                                           | Default |
|-------------------------|-------------------------------------------------------|---------|
| -C, --community         | SNMPv2c community string (required for remote hosts) | —       |
| -p, --snmp-port         | SNMP port                                             | 161     |
| -T, --snmp-timeout      | SNMP timeout; overrides --timeout for SNMP           | —       |

---

## Evaluation

| Flag               | Description                                                        | Default        |
|--------------------|--------------------------------------------------------------------|----------------|
| --status <attr>    | Attribute to evaluate on each interface                            | oper-status    |

### Evaluation Attributes

| Value          | Meaning                                                                |
|----------------|------------------------------------------------------------------------|
| oper-status    | Operational status (is the interface up?)                              |
| admin-status   | Administrative status (is the interface enabled?)                      |
| linkspeed      | Negotiated link speed (non-zero required)                              |
| duplex         | Duplex mode (full required; bridges pass automatically)                |
| mtu            | MTU value (must be > 0)                                                |
| alias          | Alias identity (fails if interface is an alias)                        |
| flags          | Kernel flags (evaluates presence of UP/RUNNING)                        |
| iftype         | SNMP ifType (evaluates type validity)                                  |

All attribute violations result in CRITICAL.  
There is no WARNING tier.

---

## Perfdata Metrics

The `--perfdata` flag selects a single SNMP counter to output in Nagios perfdata.

Valid values:

Inbound:

- in_octets  
- in_ucast  
- in_multicast  
- in_broadcast  
- in_discards  
- in_errors  

Outbound:

- out_octets  
- out_ucast  
- out_multicast  
- out_broadcast  
- out_discards  
- out_errors  

Only one metric may be selected.

Perfdata is only emitted in Nagios mode.

---

## Filtering & Selection

| Flag                  | Description                                                              | Repeatable |
|-----------------------|--------------------------------------------------------------------------|------------|
| --ifaces LIST         | Comma‑delimited list or regex pattern of interfaces to evaluate          | No         |
| --ignore PATTERN      | Exclude interfaces matching substring or regex                           | Yes        |
| --ignore-virtual      | Exclude virtual interfaces (vnet*, virbr*, docker0, etc.)                | No         |
| --exclude-local       | Exclude loopback and local‑only interfaces (lo)                          | No         |
| --include-aliases     | Include alias interfaces (excluded by default)                           | No         |

Filtering always occurs before selection.  
See Enforcement.md for full pipeline details.

---

## Output Modes

| Flag              | Mode    | Description                                                     |
|-------------------|---------|-----------------------------------------------------------------|
| *(default)*       | Nagios  | Single‑line output with exit code; logging disabled             |
| -v, --verbose     | Verbose | Human‑readable table; logging enabled                           |
| -j, --json        | JSON    | Full structured output including counters; logging enabled      |
| -q, --quiet       | Quiet   | Exit code only                                                  |

Output mode precedence:

1. JSON  
2. Verbose  
3. Nagios (default)  

If both -j and -v are provided, JSON wins.

---

## Logging

Logging is opt‑in and only active in verbose and JSON modes.

| Flag                | Description                                            | Default |
|---------------------|--------------------------------------------------------|---------|
| --log-dir PATH      | Directory for log output                               | —       |
| --log-max-mb MB     | Maximum log size before rotation                       | 50      |

Nagios mode never logs.

---

## General

| Flag              | Description                                      | Default |
|-------------------|--------------------------------------------------|---------|
| --timeout SEC     | General timeout for all operations               | 5       |
| -V, --version     | Print version and exit                           | —       |

---

## Examples

### Local Host

Check all local interfaces:

`./check_interfaces.py -H localhost`


Verbose diagnostics:

`./check_interfaces.py -H localhost -v`


### Remote Host (SNMP)

`/check_interfaces.py -H switch01 -C public`


### Targeted Interfaces

Literal list:

`./check_interfaces.py -H switch01 -C public --ifaces "eth0,eth1"`


Regex:

`./check_interfaces.py -H switch01 -C public --ifaces "GigabitEthernet0/[0-3]"`


### Attribute Checks

Linkspeed:

`./check_interfaces.py -H switch01 -C public --status linkspeed`


Duplex:

`./check_interfaces.py -H switch01 -C public --status duplex`


MTU:

`./check_interfaces.py -H switch01 -C public --status mtu`


Alias identity:

`./check_interfaces.py -H switch01 -C public --status alias`


### Filtering

Exclude virtual and local interfaces:

`./check_interfaces.py -H linux01 --ignore-virtual --exclude-local`


Ignore patterns:

`./check_interfaces.py -H switch01 -C public --ignore "vnet.*" --ignore "docker0"`


Include alias interfaces:

`./check_interfaces.py -H switch01 -C public --include-aliases`


### Combined Filtering + Selection

`./check_interfaces.py -H switch01 -C public --ignore "mgmt" --ifaces "GigabitEthernet0/[0-9]"`


### JSON Output

`/check_interfaces.py -H switch01 -C public -j`

### Logging

`./check_interfaces.py -H switch01 -C public -v --log-dir /var/log/nms_tools`

Custom rotation:

`./check_interfaces.py -H switch01 -C public -v --log-dir /var/log/nms_tools --log-max-mb 100`

### SNMP Options

Non‑standard port:

`./check_interfaces.py -H switch01 -C public -p 1161`

Extended timeout:

`./check_interfaces.py -H switch01 -C public -T 30`

---

## Exit Codes

| Code | Status   | Meaning                                                                  |
|------|----------|--------------------------------------------------------------------------|
| 0    | OK       | All evaluated interfaces pass                                            |
| 2    | CRITICAL | Attribute failure, unmatched --ifaces pattern, or SNMP failure           |
| 3    | UNKNOWN  | DNS failure, timeout, invalid arguments, or unhandled error              |

There is no WARNING tier.

---

## See Also

[Installation.md](Installation.md)
[Enforcement.md](Enforcement.md)
[Operation.md](Operation.md)
[Metadata_schema.md](Metadata_schema.md)
