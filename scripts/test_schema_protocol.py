#!/usr/bin/env python3
"""Exercise ordinary persistent state and transition-only repair over the socket."""
from client import Client

c = Client()
ns = 'schema-protocol'
initial = c.request('eval', ns=ns, id='schema-initial', code='''
(import "live-poc-coil.meta")
(defsum Visibility (Hidden) (Visible))
(defstruct State :live/state true [(visible bool true) (value i64 7)])
(letonce world (State :visible false :value 42))
(defn value [] (-> i64) (.value world))
''')
assert 'error' not in initial['status'], initial
assert c.request('eval', ns=ns, code='(value)')['value'] == '42'
missing_code = '(defstruct State :live/state true [(visible Visibility (Visible)) (value i64 7)])'
missing = c.request('eval', ns=ns, id='schema-missing', policy='deferred', code=missing_code)
assert 'error' in missing['status'], missing
assert int(c.request('status')['state-condition']) != 0
bad = c.request('eval', ns=ns, code='(migrate State visible old 17)')
assert 'error' in bad['status'], bad
repaired = c.request('eval', ns=ns, id='schema-repaired',
                     code='(migrate State visible old (if old (Visible) (Hidden)))')
assert 'error' not in repaired['status'], repaired
assert int(c.request('status')['state-condition']) == 0
assert c.request('eval', ns=ns, code='(value)')['value'] == '42'
assert c.request('eval', ns=ns,
                 code='(match (.visible world) (Hidden [] true) (Visible [] false))')['value'] == 'true'
assert c.request('eval', ns=ns, id='schema-missing', policy='deferred', code=missing_code) == missing
assert int(c.request('status')['state-condition']) == 0
c.close()
print('PASS: persistent roots, missing migration, strict rejection, transition-only repair and receipt retry')
