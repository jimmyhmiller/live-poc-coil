#!/usr/bin/env python3
"""Explicit reset publishes once; ordinary initializer edits do not reset state."""
from client import Client

c = Client()
try:
    ns = 'reset-protocol'
    initial = c.request('eval', ns=ns, code='''
(import "live-poc-coil.meta")
(defstruct State [(value i64 7)])
(letonce world (State :value 42))
(defn value [] (-> i64) (.value world))
''')
    assert 'error' not in initial['status'], initial
    epoch = int(c.request('status')['schema-epoch'])
    code = '(reset-state! world (State :value 99))'
    reset = c.request('eval', ns=ns, id='reset-once', code=code)
    assert 'error' not in reset['status'], reset
    assert int(c.request('status')['schema-epoch']) == epoch + 1
    assert c.request('eval', ns=ns, code='(value)')['value'] == '99'
    changed = c.request('eval', ns=ns, code='(set! (.value world) 77)')
    assert 'error' not in changed['status'], changed
    assert c.request('eval', ns=ns, id='reset-once', code=code) == reset
    assert int(c.request('status')['schema-epoch']) == epoch + 1
    assert c.request('eval', ns=ns, code='(value)')['value'] == '77'
    bad = c.request('eval', ns=ns, code='(reset-state! world (State :value false))')
    assert 'error' in bad['status'], bad
    assert int(c.request('status')['schema-epoch']) == epoch + 1
    assert c.request('eval', ns=ns, code='(value)')['value'] == '77'
    again = c.request('eval', ns=ns, code='(letonce world (State :value 13))')
    assert 'error' not in again['status'], again
    assert c.request('eval', ns=ns, code='(value)')['value'] == '77'
    print('PASS: explicit reset, stable schema version, receipt retry once, rejection and initializer preservation')
finally:
    c.close()
