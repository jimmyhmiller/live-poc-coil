#!/usr/bin/env python3
"""Deferred publication and immutable retry receipts against a running host."""
from client import Client

c = Client()
try:
    ready = c.request('eval', ns='live-demo', code='(defn f [] (-> i64) 17)')
    assert ready['status'] == ['done'], ready
    request = dict(ns='live-demo', id='repair-protocol-block', policy='deferred',
                   code='(defn f [] (-> i64) true)')
    blocked = c.request('eval', **request)
    assert blocked['status'] == ['blocked', 'done'], blocked
    assert int(blocked['revision']) == int(ready['revision']) + 1
    assert blocked['diagnostic']
    assert c.request('eval', **request) == blocked
    conflict = c.request('eval', **{**request, 'policy': 'strict'})
    assert 'error' in conflict['status'], conflict
    source = c.request('source', ns='live-demo', symbol='f')
    assert source['accepted'] == '(defn f [] (-> i64) 17)', source
    assert int(source['condition']) > 0, source
    denied = c.request('eval', ns='live-demo', code='(f)')
    assert 'error' in denied['status'], denied
    repaired = c.request('eval', ns='live-demo', code='(defn f [] (-> i64) 42)')
    assert repaired['status'] == ['done'], repaired
    assert c.request('eval', ns='live-demo', code='(f)')['value'] == '42'
    assert c.request('source', ns='live-demo', symbol='f')['condition'] == '0'
    assert c.request('eval', **request) == blocked  # Immutable original receipt after repair.
    assert 'error' in c.request('cancel-input', ticket='-1')['status']
    print('PASS: blocked publication, desired/accepted source, policy conflicts, repair and original retry receipt')
finally:
    c.close()
