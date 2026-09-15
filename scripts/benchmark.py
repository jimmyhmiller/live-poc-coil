#!/usr/bin/env python3
"""Measure client submission through Metal presentation; preserve every outcome."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import statistics
import subprocess
import time
from client import Client


def command(*args):
    result = subprocess.run(args, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def percentile(values, quantile):
    return sorted(values)[max(0, math.ceil(len(values) * quantile) - 1)] if values else None


parser = argparse.ArgumentParser()
parser.add_argument('--count', type=int, default=1000)
parser.add_argument('--warmup', type=int, default=20)
parser.add_argument('--limit-ms', type=float, default=100)
parser.add_argument('--delay-max-ms', type=float, default=17)
parser.add_argument('--timeout', type=float, default=5)
parser.add_argument('--output', type=Path, default=Path('build/benchmark.json'))
args = parser.parse_args()
assert args.count > 0 and args.warmup >= 0
client = Client()
rng = random.Random(0)
clock_samples = []
for _ in range(20):
    before = time.monotonic()
    reply = client.request('status')
    after = time.monotonic()
    clock_samples.append({'roundtrip': after-before,
                          'offset': float(reply['now'])-(before+after)/2})
clock = min(clock_samples, key=lambda x: x['roundtrip'])
clock['uncertainty'] = clock['roundtrip']/2
records = []
compiler = Path('build/toolchain/bin/coil')
report = {
    'workload': 'alternating-button-pigment',
    'configuration': vars(args) | {'output': str(args.output)},
    'clock': clock,
    'environment': {
        'os': platform.platform(),
        'hardware': command('sysctl', '-n', 'hw.model'),
        'cpu': command('sysctl', '-n', 'machdep.cpu.brand_string'),
        'project_commit': command('git', 'rev-parse', 'HEAD'),
        'project_status': command('git', 'status', '--porcelain'),
        'compiler_sha256': hashlib.sha256(compiler.read_bytes()).hexdigest(),
        'fixture_sha256': hashlib.sha256(Path('fixtures/paper.coil').read_bytes()).hexdigest(),
    },
    'records': records,
}
args.output.parent.mkdir(parents=True, exist_ok=True)
try:
    for i in range(args.count + args.warmup):
        source = f'(defn button-pigment [] (-> u32) {0x537bbc if i % 2 == 0 else 0xc77855})'
        started = time.monotonic()  # Before request construction and encoding.
        response = client.request('eval', ns='live-demo', code=source)
        record = {'index': i, 'warmup': i < args.warmup, 'source': source,
                  'client_submit': started, 'response': response}
        records.append(record)
        if 'error' in response['status']:
            record['outcome'] = 'rejected'
        else:
            deadline = started + args.timeout
            while True:
                telemetry = client.request('metrics', revision=response['revision'])
                record['telemetry'] = telemetry
                if float(telemetry['presented']) > 0:
                    record['outcome'] = 'presented'
                    record['latency_ms'] = 1000 * (float(telemetry['presented']) - started - clock['offset'])
                    record['compile_ms'] = 1000 * (float(telemetry['compile-end']) - float(telemetry['compile-start']))
                    break
                if time.monotonic() >= deadline:
                    record['outcome'] = 'unpresented-timeout'
                    break
                time.sleep(0.001)
        if i % 50 == 0:
            print(f"{i}: {record['outcome']}, {record.get('latency_ms', 0):.2f} ms", flush=True)
            args.output.write_text(json.dumps(report, indent=2))
        time.sleep(rng.random() * args.delay_max_ms / 1000)
finally:
    client.close()
    measured = [r for r in records if not r['warmup']]
    values = [r['latency_ms'] for r in measured if r['outcome'] == 'presented']
    misses = sum(v + clock['uncertainty'] * 1000 >= args.limit_ms for v in values)
    background = sum(r.get('telemetry', {}).get('app-active') != '1' or
                     r.get('telemetry', {}).get('window-visible') != '1' for r in measured)
    report['summary'] = {
        'measured': len(measured), 'presented': len(values),
        'p50_ms': statistics.median(values) if values else None,
        'p95_ms': percentile(values, .95), 'p99_ms': percentile(values, .99),
        'max_ms': max(values) if values else None,
        'misses_including_clock_uncertainty': misses,
        'other_outcomes': len(measured)-len(values),
        'timing_gate_passed': len(values) == args.count and misses == 0,
        'background_or_unknown_samples': background,
        'foreground_timing_gate_passed': len(values) == args.count and misses == 0 and background == 0,
        'pixel_gate': 'separate verification required',
    }
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report['summary'], indent=2), flush=True)
