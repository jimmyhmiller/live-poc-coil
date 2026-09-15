#!/usr/bin/env python3
"""Package the locally built host as a macOS development application."""
from pathlib import Path
import plistlib
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
app = root / 'build/Live Coil.app'
contents = app / 'Contents'
(contents / 'MacOS').mkdir(parents=True, exist_ok=True)
staged = contents / 'MacOS/live-poc.next'
shutil.copy2(root / 'build/live-poc', staged)
staged.replace(contents / 'MacOS/live-poc')
with (contents / 'Info.plist').open('wb') as file:
    plistlib.dump({
        'CFBundleIdentifier': 'com.jimmyhmiller.live-poc-coil',
        'CFBundleName': 'Live Coil',
        'CFBundleExecutable': 'live-poc',
        'CFBundlePackageType': 'APPL',
        'CFBundleVersion': '1',
        'NSHighResolutionCapable': True,
        'LSEnvironment': {
            'LPC_PROJECT': str(root),
            'LPC_TOOLCHAIN': str(root / 'build/toolchain/bin/coil'),
        },
    }, file)
subprocess.run(['codesign', '--force', '--sign', '-', str(app)], check=True)
subprocess.run(['codesign', '--verify', '--strict', str(app)], check=True)
print(app)
