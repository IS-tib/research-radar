"""Unit tests for cache.TTLCache."""

import time

from cache import TTLCache


def test_set_then_get_returns_value():
    c = TTLCache(ttl_seconds=60)
    c.set("k", {"papers": [1, 2, 3]})
    assert c.get("k") == {"papers": [1, 2, 3]}


def test_missing_key_returns_none():
    c = TTLCache(ttl_seconds=60)
    assert c.get("nope") is None


def test_expired_entry_returns_none():
    c = TTLCache(ttl_seconds=0.01)
    c.set("k", "value")
    time.sleep(0.03)
    assert c.get("k") is None


def test_expired_entry_is_evicted():
    c = TTLCache(ttl_seconds=0.01)
    c.set("k", "value")
    time.sleep(0.03)
    c.get("k")
    assert len(c) == 0


def test_clear_empties_the_cache():
    c = TTLCache(ttl_seconds=60)
    c.set("a", 1)
    c.set("b", 2)
    c.clear()
    assert len(c) == 0
    assert c.get("a") is None


def test_per_entry_ttl_overrides_default():
    c = TTLCache(ttl_seconds=60)
    c.set("short", "value", ttl=0.01)
    time.sleep(0.03)
    assert c.get("short") is None


def test_distinct_keys_are_independent():
    c = TTLCache(ttl_seconds=60)
    c.set(("a", "hash1"), "one")
    c.set(("a", "hash2"), "two")
    assert c.get(("a", "hash1")) == "one"
    assert c.get(("a", "hash2")) == "two"


def test_contains():
    c = TTLCache(ttl_seconds=60)
    assert "k" not in c
    c.set("k", "v")
    assert "k" in c
