# NMS_Tools Documentation

**Suite:** NMS_Tools Monitoring Suite
**Maintainer:** Leon McClatchey, Linktech Engineering LLC
**Document Type:** Documentation Index
**Last Updated:** 2026‑08‑30

## 📘 Table of Contents
1. [Overview](#1-overview)
2. [Available Tools](#2-available-tools)
    1. [2.1 check_ports](#21-check_ports)
    2. [2.2 check_weather](#22-check_weather)
    3. [2.3 check_cert](#23-check_cert)
    4. [2.4 check_html](#24-check_html)
    5. [2.5 check_interfaces](#25-check_interfaces)
    6. [2.6 check_ticker](#26-check_ticker)
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

### 2.1 check_ports
Deterministic multi‑port TCP connectivity checker.

* Supports lists, ranges, and mixed port sets  
* JSON, verbose, quiet, and Nagios modes  
* Operator‑grade logging with rotation  
* Deterministic evaluation rules  
* Tool documentation: [check_ports/README.md](../src/check_ports/README.md)  
* Flags reference: [FLAGS.md](docs/FLAGS.md)

---

### 2.2 check_weather
Rule‑based weather condition evaluator using deterministic JSON schemas.

* Supports temperature, wind, visibility, precipitation, and condition rules  
* JSON, verbose, quiet, and Nagios modes  
* Deterministic rule engine  
* Tool documentation: [check_weather/README.md](../src/check_weather/README.md)  
* Flags reference: [FLAGS.md](docs/FLAGS.md)

---

### 2.3 check_cert
Deterministic TLS certificate inspection and policy enforcement.

* JSON, verbose, and Nagios output modes  
* TLS version, cipher, SAN, issuer, signature algorithm, and key metadata  
* AIA chain reconstruction and OCSP metadata extraction  
* Deterministic JSON schema for automation  
* Tool documentation: [check_cert/README.md](../src/check_cert/README.md)

---

### 2.4 check_html
Deterministic HTTP/HTTPS inspection and content‑validation tool.

* TLS‑aware request pipeline  
* HTTP status, headers, content‑type, and HTML body capture  
* Backend fingerprinting and enforcement  
* Deterministic JSON schema for automation  
* Tool documentation: [check_html/README.md](../src/check_html/README.md)

---

### 2.5 check_interfaces
Network interface state and SNMP‑based status checker.

* Deterministic interface enumeration  
* SNMP‑based operational state evaluation  
* JSON, verbose, and Nagios modes  
* Tool documentation: [check_interfaces/README.md](../src/check_interfaces/README.md)

---

### 2.6 check_ticker
Deterministic ticker ingestion and movement analysis.
* JSON output mode
* FastAPI backend integration
* DOM‑driven demo frontend
* Rolling update loop
* Color‑coded movement indicators
* Tool documentation: [check_ticker/README.md](../src/check_ticker/README.md)

---

## 3. Documentation Suite

### Global Documentation (under `/docs`)
* **Installation Guide** — [Installation.md](Installation.md)
* **Suite Layout** — [suite_layout.md](suite_layout.md)
* **Logging Guide** — [Logging.md](Logging.md)
* **Monitoring Guide** — [monitoring.md](Monitoring.md)
* **Bitmask Flag Engine (Internal)** — [FLAGS.md](FLAGS.md)
* **Roadmap** — [Roadmap.md](Roadmap.md)

### Project Governance (repo root)

The following files reside at the repository root and define project‑level governance, licensing, packaging, and release metadata. They are included here for completeness, but they are **not part of the documentation navigation tree** and therefore are not linked from this index. These documents support the development, distribution, and maintenance of NMS_Tools, while the technical documentation itself lives under the `/docs` directory.

* **README** — Project overview and quick start
* **Packaging** — Build and distribution details
* **Release Notes** — Version‑specific changes
* **Requirements** — Python dependencies
* **License** — MIT license and binary license
* **Contributing Guidelines** — Contributor workflow
* **Code of Conduct** — Community standards
* **Security Policy** — Vulnerability reporting
* **Makefile** — Build automation
* **Version** — Current suite version

### Document Responsibilities

| Document | Purpose |
|----------|---------|
| Installation | How to install and configure the suite |
| Suite Layout | Directory structure and packaging conventions |
| Logging | Logging architecture and rotation |
| Monitoring | Integration with monitoring systems |
| FLAGS | Shared bitmask engine used across all tools |
| Roadmap | Planned enhancements and future tools |
| README | Project overview and usage |
| Packaging | Build and distribution process |
| Release Notes | Version‑specific changes |
| Requirements | Dependency list |
| LICENSE / LICENSE_BINARY | Legal and binary licensing |
| CONTRIBUTING | Guidelines for contributors |
| CODE_OF_CONDUCT | Community standards |
| SECURITY | Vulnerability reporting |
| Makefile | Build automation |
| VERSION | Current suite version |

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
See [Roadmap.md](Roadmap.md) for planned enhancements and upcoming tools.
