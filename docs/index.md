# NMS_Tools Documentation

**Suite:** NMS_Tools Monitoring Suite
**Maintainer:** Leon McClatchey, Linktech Engineering LLC
**Document Type:** Documentation Index
**Last Updated:** 2026‑08‑30

## 📘 Table of Contents
1. [Overview](#1-overview)
2. [Available Tools](#2-available-tools)
    * [check_ports](#check_ports)
    * [check_weather](#check_weather)
    * [check_cert](#check_cert)
    * [check_html](#check_html)
    * [check_interfaces](#check_interfaces)
    * [check_ticker](#check_ticker)
3. [Documentation Suite](#3-documentation-suite)
4. [Project Website](#4-project-website)
5. [Philosophy](#5-philosophy)
6. [Status](#6-status)

---

## 1. Overview

Welcome to the documentation for **NMS_Tools**, a suite of deterministic,
audit‑transparent monitoring and network‑inspection tools used across Linktech
Engineering infrastructure.

This documentation covers installation, usage, operation, enforcement, metadata
schema details, and the project roadmap.

---

## 2. Available Tools

### check_ports
Deterministic multi‑port TCP connectivity checker.

* Supports lists, ranges, and mixed port sets  
* JSON, verbose, quiet, and Nagios modes  
* Operator‑grade logging with rotation  
* Deterministic evaluation rules  
* Tool documentation: [`check_ports/README.md`](../check_ports/README.md)  
* Flags reference: [`check_ports/FLAGS.md`](../check_ports/FLAGS.md)

---

### check_weather
Rule‑based weather condition evaluator using deterministic JSON schemas.

* Supports temperature, wind, visibility, precipitation, and condition rules  
* JSON, verbose, quiet, and Nagios modes  
* Deterministic rule engine  
* Tool documentation: [`check_weather/README.md`](../check_weather/README.md)  
* Flags reference: [`check_weather/FLAGS.md`](../check_weather/FLAGS.md)

---

### check_cert
Deterministic TLS certificate inspection and policy enforcement.

* JSON, verbose, and Nagios output modes  
* TLS version, cipher, SAN, issuer, signature algorithm, and key metadata  
* AIA chain reconstruction and OCSP metadata extraction  
* Deterministic JSON schema for automation  
* Tool documentation: [`check_cert/README.md`](../src/check_cert/README.md)

---

### check_html
Deterministic HTTP/HTTPS inspection and content‑validation tool.

* TLS‑aware request pipeline  
* HTTP status, headers, content‑type, and HTML body capture  
* Backend fingerprinting and enforcement  
* Deterministic JSON schema for automation  
* Tool documentation: [`check_html/README.md`](../src/check_html/README.md)

---

### check_interfaces
Network interface state and SNMP‑based status checker.

* Deterministic interface enumeration  
* SNMP‑based operational state evaluation  
* JSON, verbose, and Nagios modes  
* Tool documentation: [`check_interfaces/README.md`](../src/check_interfaces/README.md)

---

### check_ticker
Deterministic ticker ingestion and movement analysis.
* JSON output mode
* FastAPI backend integration
* DOM‑driven demo frontend
* Rolling update loop
* Color‑coded movement indicators
* Tool documentation: [`check_ticker/README.md`](../src/check_ticker/README.md)

---

## 3. Documentation Suite

### Core Guides
* **Installation Guide** — [`Installation.md`](../Installation.md)  

### Project
* **Roadmap** — [`roadmap.md`](roadmap.md)  
* **Contributing Guidelines** — [`CONTRIBUTING.md`](../CONTRIBUTING.md)
* **Changelog** — [`CHANGELOG.md`](../CHANGELOG.md)

Each document has a single responsibility:

| Document | Purpose |
|----------|---------|
| Installation | How to install and run the suite |
| Usage | CLI flags, examples, Nagios integration |
| Operation | Runtime behavior, exit codes, troubleshooting |
| Enforcement | Policy engine, rule semantics, failure behavior |
| Metadata Schema | Canonical JSON structure for automation |
| Roadmap | Planned enhancements and future tools |
| CONTRIBUTING | Guidelines for contributors |
| CHANGELOG | Version history and schema changes |

---

## 4. Project Website

The official project page for NMS_Tools is available at:

**https://www.linktechengineering.net/projects/nms-tools/**

This site provides:

* Suite overview  
* Tool descriptions  
* Branding and identity  
* Cross‑project navigation  
* Public documentation  
* Related ecosystem projects  

---

## 5. Philosophy

NMS_Tools follows Linktech Engineering’s deterministic engineering principles:

* Predictable, reproducible behavior  
* No hidden state  
* Audit‑transparent output  
* Strict separation between human and machine modes  
* Minimal dependencies  
* Monitoring‑friendly design  

---

## 6. Status

Active development.  
See [`roadmap.md`](roadmap.md) for planned enhancements and upcoming tools.
