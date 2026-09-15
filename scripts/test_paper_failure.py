#!/usr/bin/env python3
"""Run against the visible moving fixture started with LPC_TESTING=1."""
import json
import hashlib
import subprocess
from pathlib import Path
from client import Client

c = Client()
records = []
ns = 'moving-demo'


def request(op, **fields):
    reply = c.request(op, **fields)
    records.append({'op': op, **fields, 'reply': reply})
    return reply


def evaluate(code):
    reply = request('eval', ns=ns, code=code)
    assert 'error' not in reply['status'], reply
    return reply.get('value')


velocity = None
armed = False
succeeded = False
try:
    evaluate('''(extern test-fail :as "lpc_test_payload_failure" :cc c [i64] (-> i64))
(extern test-hits :as "lpc_test_payload_failures" :cc c [] (-> i64))
(extern test-validation-fail :as "lpc_test_validation_failure" :cc c [i64] (-> i64))
(extern test-validation-hits :as "lpc_test_validation_failures" :cc c [] (-> i64))''')
    hits = int(evaluate('(test-hits)'))
    assert hits >= 0, 'Start this test host with LPC_TESTING=1'
    velocity = float(evaluate('(.velocity world)'))
    # Hold position deterministic while the real event loop continues ticking.
    evaluate('(do (set! (.velocity world) 0.0) (set! (.clicks world) 7) (set! (.clicks controls) 13))')
    before = {key: evaluate(code) for key, code in {
        'position': '(.x world)', 'payload': '(p/cast i64 world)',
        'size': '(p/sizeof State)', 'scene_count': '(.clicks world)',
        'control_count': '(.clicks controls)',
    }.items()}
    assert evaluate('(test-fail 1)') == '0'
    armed = True
    accepted = request('status')
    schema = '''(defstruct State
[(x f64 150.0) (velocity f64 70.0) (last f64 0.0)
 (visible bool true) (clicks i64 0) (weight f64 2.0)])'''
    failed = request('eval', ns=ns, code=schema)
    assert 'error' in failed['status'], failed
    after = request('status')
    assert after['revision'] == accepted['revision'], (accepted, after)
    assert after['schema-epoch'] == accepted['schema-epoch'], (accepted, after)
    assert after['state-condition'] == '0', after
    assert int(evaluate('(test-hits)')) == hits + 1
    for key, code in {'position': '(.x world)', 'payload': '(p/cast i64 world)',
                      'size': '(p/sizeof State)', 'scene_count': '(.clicks world)',
                      'control_count': '(.clicks controls)'}.items():
        assert evaluate(code) == before[key], (key, before, records[-1])
    # Reject a fully initialized and rewritten graph at its second validation.
    validation_hits = int(evaluate('(test-validation-hits)'))
    assert evaluate('(test-validation-fail 1)') == '0'
    accepted = request('status')
    invalid = request('eval', ns=ns, code=schema)
    assert 'error' in invalid['status'], invalid
    after = request('status')
    assert after['revision'] == accepted['revision'], (accepted, after)
    assert after['schema-epoch'] == accepted['schema-epoch'], (accepted, after)
    assert after['state-condition'] == '0', after
    assert int(evaluate('(test-validation-hits)')) == validation_hits + 1
    for key, code in {'position': '(.x world)', 'payload': '(p/cast i64 world)',
                      'size': '(p/sizeof State)', 'scene_count': '(.clicks world)',
                      'control_count': '(.clicks controls)'}.items():
        assert evaluate(code) == before[key], (key, before, records[-1])
    # Both faults disarmed. A new submission can use the same schema.
    evaluate(schema)
    assert evaluate('(.weight world)') == '2.0'
    assert evaluate('(.x world)') == before['position']
    assert evaluate('(.clicks world)') == '7'
    assert evaluate('(.clicks controls)') == '13'
    succeeded = True
    print('PASS: shadow allocation and validation failures preserved accepted storage, layout, position and counters; retry succeeded')
finally:
    cleanup_errors = []
    for code in (['(test-fail -1)', '(test-validation-fail -1)'] if armed else []) + (
            [f'(set! (.velocity world) {velocity!r})'] if velocity is not None else []):
        try:
            evaluate(code)
        except Exception as error:
            cleanup_errors.append(str(error))
    report = {
        'passed': succeeded and not cleanup_errors,
        'cleanup_errors': cleanup_errors,
        'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'worktree_status': subprocess.check_output(['git', 'status', '--porcelain'], text=True),
        'fixture_sha256': hashlib.sha256(Path('fixtures/moving.coil').read_bytes()).hexdigest(),
        'host_sha256': hashlib.sha256(Path('build/Live Coil.app/Contents/MacOS/live-poc').read_bytes()).hexdigest(),
        'compiler_sha256': hashlib.sha256(Path('build/toolchain/bin/coil').read_bytes()).hexdigest(),
        'records': records,
    }
    Path('build/paper-migration-failure.json').write_text(json.dumps(report, indent=2))
    c.close()
    if cleanup_errors:
        raise RuntimeError('test cleanup failed: ' + '; '.join(cleanup_errors))
