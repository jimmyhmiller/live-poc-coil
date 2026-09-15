#!/usr/bin/env python3
"""Exercise framing, authentication, shared revision and request idempotency."""
from client import Client, encode, decode

c = Client()
other = Client()
start = int(c.request('status')['revision'])
bad = c.request('eval', token='wrong', code='(defn f [] (-> i64) 1)')
assert 'error' in bad['status']
assert int(c.request('status')['revision']) == start
request = {'op': 'eval', 'id': 'fragmented', 'token': c.token,
           'code': '(defn f [] (-> i64) 99)', 'base-revision': str(start)}
wire = encode(request)
for byte in wire:
    c.socket.sendall(bytes([byte]))
reply = decode(c.stream)
assert int(reply['revision']) == start + 1, reply
assert other.request('status')['revision'] == str(start + 1)
assert c.request('eval', id='fragmented', code=request['code'], **{'base-revision': str(start)}) == reply
assert 'error' in c.request('eval', id='fragmented', code='(defn f [] (-> i64) 100)')['status']
assert 'error' in other.request('eval', code='(defn f [] (-> i64) 100)', **{'base-revision': str(start)})['status']
assert int(c.request('status')['revision']) == start + 1
assert 'error' in c.request('eval', code='(defn f [] (-> i64) true)')['status']
assert int(c.request('status')['revision']) == start + 1
loaded = c.request('load-file', id='loaded-file', ns='live-demo',
                   file='(defn f [] (-> i64) 101)')
assert int(loaded['revision']) == start + 2, loaded
assert c.request('load-file', id='loaded-file', ns='live-demo',
                 file='(defn f [] (-> i64) 101)') == loaded
assert 'error' in c.request('load-file', id='loaded-file', ns='live-demo',
                            file='(defn f [] (-> i64) 102)')['status']
assert int(c.request('status')['revision']) == start + 2
source = c.request('source', ns='live-demo', symbol='f')
assert source['accepted'] == '(defn f [] (-> i64) 101)', source
bad = c.request('eval', ns='live-demo', code='(defn f [] (-> i64) true)')
assert 'error' in bad['status']
source = c.request('source', ns='live-demo', symbol='f')
assert source['desired'] == '(defn f [] (-> i64) true)', source
assert source['accepted'] == '(defn f [] (-> i64) 101)', source
assert source['diagnostic'], source
assert c.request('eval', ns='live-demo', code='(+ (f) 1)')['value'] == '102'
setup = c.request('eval', ns='live-demo', code='(defn* counter [] (-> (ptr i64)) (coil.primitive/alloc-static i64))')
assert 'error' not in setup['status'], setup
code = '(do (set! (counter) (+ (load (counter)) 1)) (load (counter)))'
effect = c.request('eval', id='effect-once', ns='live-demo', code=code)
assert effect['value'] == '1', effect
assert c.request('eval', id='effect-once', ns='live-demo', code=code) == effect
assert other.request('eval', ns='live-demo', code='(load (counter))')['value'] == '1'
c.close()
other.close()
print('PASS: auth, bytewise framing, shared revision, idempotency, conflicts and rejection')
