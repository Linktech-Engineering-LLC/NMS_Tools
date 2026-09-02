#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Leon McClatchey, Linktech Engineering LLC
"""
File: test_check_ticker.py
Author: Leon McClatchey
Company: Linktech Engineering LLC
Created: 2026-09-02
Modified: 2026-09-02
Required: Python 3.8+
Part of: NMS_Tools Monitoring Suite
License: MIT (see LICENSE for details)

Description: Deterministic test group for NMS_Tools/check_ticker
            Tests the public behavioral surface exposed by run()
            using controlled fake backend responses.
"""

import builtins
import types
import pytest

import src.check_ticker.check_ticker as ct
from PythonTools.finance import ApiKeyError


# ---------------------------------------------------------------------------
# Fake provider registry
# ---------------------------------------------------------------------------

class FakeProvider:
    def __init__(self, name, accepts_key=True, requires_key=True):
        self.name = name
        self.accepts_key = accepts_key
        self.requires_key = requires_key


class FakeRegistry:
    provider_names = staticmethod(lambda: ["alpha", "beta"])
    providers = [
        FakeProvider("alpha"),
        FakeProvider("beta"),
    ]


# ---------------------------------------------------------------------------
# Fake vault + fake file
# ---------------------------------------------------------------------------

class FakeVault:
    """
    Global vault simulator.
    - If error is provided, decrypt_yaml() raises it.
    - Otherwise, decrypt_yaml() returns data.
    """

    def __init__(self, data=None, error=None, *a, **kw):
        self.data = data
        self.error = error

    def decrypt_yaml(self):
        if self.error:
            raise self.error
        return self.data


class FakeFile:
    """
    Simple fake file object that supports read(), __enter__, __exit__.
    """
    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass


# ---------------------------------------------------------------------------
# Patch helpers
# ---------------------------------------------------------------------------

def patch_registry(monkeypatch):
    monkeypatch.setattr(ct, "ProviderRegistry", FakeRegistry)


def patch_resolve_api_key(monkeypatch, mapping):
    def fake_resolve(name, cli_keys, vault_data, config_data):
        return mapping.get(name)
    monkeypatch.setattr(ct, "resolve_api_key", fake_resolve)


def patch_vault(monkeypatch, data):
    monkeypatch.setattr(
        ct,
        "VaultLoader",
        lambda *a, **kw: FakeVault(data=data)
    )


def patch_vault_failure(monkeypatch):
    monkeypatch.setattr(
        ct,
        "VaultLoader",
        lambda *a, **kw: FakeVault(error=ApiKeyError("vault failure"))
    )


def patch_yaml(monkeypatch, data):
    monkeypatch.setattr(ct.yaml, "safe_load", lambda f: data)


def patch_open(monkeypatch, data):
    def fake_open(path, mode="r", encoding=None, _data=data):
        return FakeFile(_data)
    monkeypatch.setattr(builtins, "open", fake_open)

def make_args(**kwargs):
    args = types.SimpleNamespace()
    for k, v in kwargs.items():
        setattr(args, k, v)
    return args


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_cli_overrides(monkeypatch):
    patch_registry(monkeypatch)
    patch_resolve_api_key(monkeypatch, {"alpha": "A1", "beta": "B1"})
    patch_vault(monkeypatch, None)
    patch_yaml(monkeypatch, None)
    patch_open(monkeypatch, None)

    args = make_args(
        alpha_key="A1",
        beta_key="B1",
        vault_path=None,
        vault_password_file=None,
        apikey_file=None,
    )

    result = ct.get_apikeys(args)
    assert result == {"alpha": "A1", "beta": "B1"}


def test_vault_precedence(monkeypatch):
    patch_registry(monkeypatch)
    patch_vault(monkeypatch, {"alpha": "VAULT_A", "beta": "VAULT_B"})
    patch_resolve_api_key(monkeypatch, {"alpha": "VAULT_A", "beta": "VAULT_B"})
    patch_yaml(monkeypatch, None)
    patch_open(monkeypatch, None)

    args = make_args(
        alpha_key=None,
        beta_key=None,
        vault_path="/fake/vault",
        vault_password_file="/fake/pass",
        apikey_file=None,
    )

    result = ct.get_apikeys(args)
    assert result == {"alpha": "VAULT_A", "beta": "VAULT_B"}


def test_yaml_precedence(monkeypatch):
    patch_registry(monkeypatch)
    patch_resolve_api_key(monkeypatch, {"alpha": "CFG_A", "beta": "CFG_B"})
    patch_vault(monkeypatch, None)
    patch_yaml(monkeypatch, {"alpha": "CFG_A", "beta": "CFG_B"})
    patch_open(monkeypatch, {"alpha": "CFG_A", "beta": "CFG_B"})

    args = make_args(
        alpha_key=None,
        beta_key=None,
        vault_path=None,
        vault_password_file=None,
        apikey_file="/fake/apikeys.yaml",
    )

    result = ct.get_apikeys(args)
    assert result == {"alpha": "CFG_A", "beta": "CFG_B"}


def test_missing_keys(monkeypatch):
    patch_registry(monkeypatch)
    patch_resolve_api_key(monkeypatch, {"alpha": None, "beta": None})
    patch_vault(monkeypatch, None)
    patch_yaml(monkeypatch, None)
    patch_open(monkeypatch, None)

    args = make_args(
        alpha_key=None,
        beta_key=None,
        vault_path=None,
        vault_password_file=None,
        apikey_file=None,
    )

    result = ct.get_apikeys(args)
    assert result == {}  # no providers resolved


def test_invalid_vault(monkeypatch):
    patch_registry(monkeypatch)
    patch_vault_failure(monkeypatch)
    patch_resolve_api_key(monkeypatch, {})
    patch_yaml(monkeypatch, None)
    patch_open(monkeypatch, None)

    args = make_args(
        alpha_key=None,
        beta_key=None,
        vault_path="/fake/vault",
        vault_password_file="/fake/pass",
        apikey_file=None,
    )

    with pytest.raises(ApiKeyError):
        ct.get_apikeys(args)


def test_env_fallback(monkeypatch):
    patch_registry(monkeypatch)
    patch_resolve_api_key(monkeypatch, {"alpha": "ENV_A", "beta": "ENV_B"})
    patch_vault(monkeypatch, None)
    patch_yaml(monkeypatch, None)
    patch_open(monkeypatch, {"alpha": "ENV_A", "beta": "ENV_B"})

    monkeypatch.setenv("CT_APIKEY_FILE", "/fake/env.yaml")

    args = make_args(
        alpha_key=None,
        beta_key=None,
        vault_path=None,
        vault_password_file=None,
        apikey_file=None,
    )

    result = ct.get_apikeys(args)
    assert result == {"alpha": "ENV_A", "beta": "ENV_B"}
