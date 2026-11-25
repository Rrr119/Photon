#!/usr/bin/env python3
"""Acceptance test for SPA & hash-route discovery.

Runs Photon against 3 local SPA sites twice per site (legacy behavior via
--no-spa, then with SPA discovery enabled) and verifies:
  1. SPA discovery finds strictly more unique paths on every site.
  2. No resource is requested more than once (dedup check on the server
     request log of the SPA run).
"""
import os
import subprocess
import sys
import tempfile
import threading
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spa_server import make_server

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITES = ['hash', 'history', 'forms']
DATASETS = ('internal', 'routes', 'fuzzable', 'endpoints')


def run_photon(url, output_dir, spa):
    cmd = [sys.executable, os.path.join(ROOT, 'photon.py'),
           '-u', url, '-l', '2', '-t', '4', '-o', output_dir]
    if not spa:
        cmd.append('--no-spa')
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                            timeout=300)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError('photon run failed for %s' % url)


def discovered_paths(output_dir):
    """Collect unique discovered paths from Photon's output files."""
    paths = set()
    for name in DATASETS:
        filepath = os.path.join(output_dir, name + '.txt')
        if not os.path.isfile(filepath):
            continue
        with open(filepath) as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('http'):
                    parsed = urlparse(line)
                    path = parsed.path or '/'
                    if parsed.query:
                        path += '?' + parsed.query
                    paths.add(path)
                elif line.startswith('/'):
                    paths.add(line)
    return paths


def check_site(site, workdir):
    site_dir = os.path.join(ROOT, 'tests', 'spa_sites', site)
    results = {}
    for label, spa in (('baseline', False), ('spa', True)):
        log_path = os.path.join(workdir, '%s-%s-requests.log' % (site, label))
        server = make_server(site_dir, log_path)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            output_dir = os.path.join(workdir, '%s-%s-out' % (site, label))
            run_photon('http://127.0.0.1:%i' % server.port, output_dir, spa)
        finally:
            server.shutdown()
            server.server_close()
        with open(log_path) as handle:
            requests_made = handle.read().splitlines()
        results[label] = (discovered_paths(output_dir), requests_made)
    return results


def main():
    failures = []
    print('%-10s %10s %10s %8s' % ('site', 'baseline', 'spa', 'delta'))
    with tempfile.TemporaryDirectory() as workdir:
        for site in SITES:
            results = check_site(site, workdir)
            baseline_paths, _ = results['baseline']
            spa_paths, spa_requests = results['spa']
            delta = len(spa_paths) - len(baseline_paths)
            print('%-10s %10i %10i %+8i' % (
                site, len(baseline_paths), len(spa_paths), delta))
            if delta <= 0:
                failures.append('%s: no path discovery improvement' % site)
            duplicates = len(spa_requests) - len(set(spa_requests))
            if duplicates:
                failures.append('%s: %i duplicate requests' % (site,
                                                               duplicates))
    if failures:
        print('\nFAIL:')
        for failure in failures:
            print(' - ' + failure)
        return 1
    print('\nOK: SPA discovery finds more paths on all 3 sites and no '
          'resource is requested twice.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
