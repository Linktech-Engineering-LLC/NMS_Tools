# check_interfaces — Network Interface State & Attribute Monitoring Tool
![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-under--construction-yellow)
![Nagios Plugin](https://img.shields.io/badge/Nagios-plugin-success)
![NMS_Tools](https://img.shields.io/badge/NMS_Tools-check__interfaces-blueviolet)

`check_interfaces.py` is an operator‑grade network interface monitoring tool designed for deterministic, rule‑driven validation of interface state, speed, and attributes across network devices.  
This tool is currently **under active development** and will serve as the template for future NMS_Tools monitoring plugins.

---

## Current Status

The tool is in early development and the following components are in progress:

- CLI parser and argument model  
- SNMP interface discovery  
- Canonical filtering logic (alias, virtual, local, ignore, require)  
- Speed enforcement  
- Deterministic JSON and verbose output models  
- Nagios‑compatible exit codes and output formatting  

Additional enforcement rules, documentation, and backend logic will be added as development continues.

---

## Planned Capabilities

Once complete, `check_interfaces.py` will provide:

- Deterministic interface enumeration  
- Attribute‑based filtering (alias, virtual, local, ignored, required)  
- Speed validation and enforcement  
- Administrative vs operational state checks  
- Duplex and MTU validation  
- JSON, verbose, and Nagios output modes  
- Suite‑wide logging and metadata consistency  

---

## Documentation

Full documentation (Usage, Operation, Enforcement, Metadata Schema) will be added once the tool reaches its first stable milestone.

For now, this README serves as a placeholder and identity document for the tool within the NMS_Tools suite.

---

## License

This tool is part of the **NMS_Tools** suite.  
See the root project for licensing, documentation, and contributor guidelines.
