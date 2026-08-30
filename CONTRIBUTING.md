# Contributing to NMS_Tools

Thank you for your interest in NMS_Tools.

**Suite:** NMS_Tools Monitoring Suite
**Maintainer:** Leon McClatchey, Linktech Engineering LLC
**Document Type:** Contribution Guidelines
**Last Updated:** 2026‑08‑30

## 📘 Table of Contents
1. [Contribution Policy](#1-contribution-policy)
2. [Reporting Issues](#2-reporting-issues)
3. [Code Style](#3-code-style)
4. [Roadmap](#4-roadmap)

## 1. Contribution Policy
NMS_Tools is developed and maintained internally by Linktech Engineering.
External contributions are not currently accepted.

This policy ensures deterministic engineering standards, consistent suite behavior, and controlled release cycles.

## 2. Reporting Issues

If you encounter a bug or unexpected behavior:
1. Include the command you ran
2. Include the output (JSON or verbose preferred)
3. Include Python version and OS
4. Include any relevant network conditions (firewalls, proxies, etc.)

Providing deterministic reproduction steps ensures issues can be validated and resolved efficiently.

## 3. Code Style

All tools in this suite follow these principles:
* deterministic behavior
* audit‑transparent output
* no hidden state
* minimal dependencies
* **Python‑3.10+ compatibility (current development uses Python 3.12)**
* clear separation between human and machine output modes

These standards apply to all tools, demos, and internal scripts.

## 4. Roadmap

See [docs/roadmap](docs/roadmap.md) for planned enhancements and future tools.

Roadmap updates follow the same deterministic documentation rules as the suite README.