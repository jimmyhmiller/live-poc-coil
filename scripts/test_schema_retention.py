#!/usr/bin/env python3
"""Build and measure the long-lived native schema workload on macOS."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--compiler', type=Path, default=ROOT / 'build/toolchain/bin/coil')
parser.add_argument('--count', type=int, default=1000)
parser.add_argument('--output', type=Path, default=ROOT / 'build/schema-retention.json.gz')
args = parser.parse_args()
if platform.system() != 'Darwin':
    parser.error('This gate uses macOS time(1) resident-memory accounting.')
if args.count < 80 or args.count > 100000:
    parser.error('--count must be between 80 and 100000')
compiler = args.compiler.resolve()
binary = ROOT / 'build/schema-retention-gate'
env = dict(os.environ, LPC_TOOLCHAIN=str(compiler),
           PATH=str(compiler.parent) + os.pathsep + os.environ['PATH'])
subprocess.run([str(compiler), 'build', 'tests/schema_retention_probe.coil',
                '-o', str(binary)], cwd=ROOT, env=env, check=True)
result = subprocess.run(['/usr/bin/time', '-l', str(binary), str(args.count)],
                        cwd=ROOT, env=env, text=True, capture_output=True)
pattern = (r'schema-retention: version=(\d+) generations=(\d+) runtime-images=(\d+) '
           r'owned-bytes=(\d+) owned-peak=(\d+)')
keys = ['version', 'generations', 'runtime_images', 'owned_bytes', 'owned_peak']
samples = [dict(zip(keys, map(int, row))) for row in re.findall(pattern, result.stdout)]
peak_match = re.search(r'(\d+)\s+maximum resident set size', result.stderr)
peak = int(peak_match[1]) if peak_match else None
steady = [row['owned_bytes'] for row in samples[1:]]
failures = []
if result.returncode:
    failures.append(f'native assertions failed: exit {result.returncode}')
if len(samples) != (args.count + 24) // 25:
    failures.append('missing progress samples')
if any(row['generations'] > 4 or row['runtime_images'] > 2 for row in samples):
    failures.append('native ownership exceeded its bound')
if not steady or max(steady) - min(steady) > 65536:
    failures.append('session allocations did not reach steady state')
# The compiler has a large fixed startup working set. This ceiling includes
# allocator caching, and is independent of the number of requested edits.
if peak is None or peak >= 768 * 1024 * 1024:
    failures.append('process peak exceeded 768 MiB')
report = dict(count=args.count, compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
              revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              worktree_status=subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True),
              platform=platform.platform(), samples=samples, peak_resident_bytes=peak,
              stdout=result.stdout, stderr=result.stderr, failures=failures)
args.output.parent.mkdir(parents=True, exist_ok=True)
opener = gzip.open if args.output.suffix == '.gz' else open
with opener(args.output, 'wt') as output:
    json.dump(report, output, indent=2)
print(f'{"FAIL" if failures else "PASS"}: {args.count} schema edits; peak {peak} bytes; {args.output}')
for failure in failures:
    print(failure)
raise SystemExit(bool(failures))
