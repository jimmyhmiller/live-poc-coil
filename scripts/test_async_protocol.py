#!/usr/bin/env python3
"""Real sockets: responsive controls, cooperative interrupt and owned retries."""
import time
from client import Client, encode, decode

c = Client()
other = Client()
try:
    setup = c.request('eval', code='''
      (import "live-poc-coil.cancellation" :as cancellation)
      (extern usleep :cc c [u32] (-> i32))
      (defn* async-counter [] (-> (ptr i64)) (coil.primitive/alloc-static i64))''')
    assert setup['status'] == ['done'], setup
    base = int(setup['revision'])
    running = dict(op='eval', id='async-running', token=c.token,
                   code='(do (loop (when (cancellation/cancelled?) (break)) (usleep 1000)) 73)')
    queued = dict(op='eval', id='async-queued', token=c.token,
                  code='(do (set! (async-counter) 123) (load (async-counter)))')
    c.socket.sendall(encode(running))
    deadline = time.monotonic() + 10
    while True:
        status = other.request('status')
        if int(status['revision']) == base + 1:
            break
        assert time.monotonic() < deadline, status
        time.sleep(.002)
    # The same connection can submit and interrupt while its eval is executing.
    messages = [queued,
                dict(op='status', id='async-status', token=c.token),
                dict(op='interrupt', id='cancel-queued', token=c.token, **{'interrupt-id': queued['id']}),
                dict(op='interrupt', id='cancel-running', token=c.token, **{'interrupt-id': running['id']})]
    start = time.monotonic()
    c.socket.sendall(b''.join(map(encode, messages)))
    replies = {}
    for _ in range(5):
        reply = decode(c.stream)
        replies[reply['id']] = reply
    elapsed = time.monotonic() - start
    assert replies['async-status']['compiler-active-request'] == running['id'], replies
    assert replies['async-status']['compiler-queued'] == '1', replies
    assert replies['cancel-queued']['matched-requests'] == '1', replies
    assert replies['cancel-running']['matched-requests'] == '1', replies
    assert replies['async-queued']['status'] == ['interrupted', 'done'], replies
    assert replies['async-running']['value'] == '73', replies
    assert replies['async-running']['interrupt'] == 'requested-after-publication', replies
    assert int(other.request('status')['revision']) == base + 1
    assert c.request('eval', id=queued['id'], code=queued['code']) == replies['async-queued']
    assert c.request('eval', code='(load (async-counter))')['value'] == '0'
    # A metaprogram delay puts the interrupt inside native preparation. The
    # control reply must arrive before the compiler finishes that delay.
    setup = c.request('eval', code='(defn* delayed-header [] (-> Code) (usleep 300000) `(defn* prepared-sentinel [] (-> i64) 19))')
    assert setup['status'] == ['done'], setup
    before = c.request('source', symbol='f')
    revision = c.request('status')['revision']
    slow = dict(op='eval', id='async-preparing', token=c.token,
                code='(meta (delayed-header)) (defn f [] (-> i64) 1234)')
    c.socket.sendall(encode(slow))
    deadline = time.monotonic() + 10
    while other.request('source', symbol='f')['desired'] != '(defn f [] (-> i64) 1234)':
        assert time.monotonic() < deadline
        time.sleep(.001)
    control_start = time.monotonic()
    control = other.request('interrupt', **{'interrupt-id': slow['id']})
    control_elapsed = time.monotonic() - control_start
    assert control['matched-requests'] == '1', control
    assert control_elapsed < .15, control_elapsed
    interrupted = decode(c.stream)
    assert interrupted['status'] == ['interrupted', 'done'], interrupted
    assert other.request('status')['revision'] == revision
    after = other.request('source', symbol='f')
    assert after['accepted'] == before['accepted'], (before, after)
    assert after['desired'] == '(defn f [] (-> i64) 1234)', after
    assert c.request('eval', code='(prepared-sentinel)')['status'] == ['error', 'done']
    assert c.request('eval', code='(defn f [] (-> i64) 42)')['status'] == ['done']
    # Receipt data survives the network reference disappearing during execution.
    detached = Client()
    detached_request = dict(op='eval', id='async-detached', token=c.token,
                            code='(do (usleep 50000) (set! (async-counter) (+ (load (async-counter)) 1)) (load (async-counter)))')
    detached.socket.sendall(encode(detached_request))
    detached.close()
    answer = c.request('eval', id=detached_request['id'], code=detached_request['code'])
    assert answer['value'] == '1', answer
    assert c.request('eval', id=detached_request['id'], code=detached_request['code']) == answer
    assert c.request('eval', code='(load (async-counter))')['value'] == '1'
    print(f'PASS: preparation interrupt reply {control_elapsed * 1000:.2f} ms; same-connection controls and interrupts ({elapsed * 1000:.2f} ms), no cancelled effects, disconnect retry once')
finally:
    c.close()
    other.close()
