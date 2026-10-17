#!/usr/bin/env python3
"""관절 검사 표. python3 audit_joints.py PKG_DIR  (PKG_DIR 에 rig.js · rig.json · parts/)"""
import os, sys, time, socket, subprocess, shutil, json
from playwright.sync_api import sync_playwright
pkg = os.path.abspath(sys.argv[1]); here = os.path.dirname(os.path.abspath(__file__))
shutil.copy(os.path.join(here, 'audit_joints.html'), os.path.join(pkg, 'audit_joints.html'))
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=pkg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{port}/audit_joints.html'); pg.wait_for_function('window.ready', timeout=60000)
        R = pg.evaluate('audit()'); b.close()
        if errs: print('JS ERR', errs[:3])
finally: srv.terminate()
fail = 0
print(f"{'장면':10s} {'손목(±35)':>14s} {'팔꿈치N(-150..6)':>17s} {'무릎(0..150)':>14s} {'엉덩이(-125..35)':>17s} {'무기땅(≤12)':>9s} {'튐(≤14)':>16s} {'미끄(≤1.5)':>8s}")
for n, r in R.items():
    fail |= bool(r['bad'])
    print(f"{n:10s} {str(r['wrist']):>14s} {str(r['elbowN']):>17s} {str(r['knee']):>14s} {str(r['hip']):>17s} {r['tipBelow']:9.1f} {r['jump']:6.1f} {r['jumpWhere']:>9s} {r['slide']:8.2f}  {'✗ '+','.join(r['bad']) if r['bad'] else '✓'}")
sys.exit(1 if fail else 0)
