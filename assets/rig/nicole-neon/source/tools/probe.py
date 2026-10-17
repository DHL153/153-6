#!/usr/bin/env python3
"""리그 페이지에서 JS 식을 돌려 결과 출력. python3 probe.py PKG 'js expression using rig, RunAnimator'"""
import os, sys, time, socket, subprocess, json
from playwright.sync_api import sync_playwright
pkg = os.path.abspath(sys.argv[1]); code = sys.argv[2]
open(os.path.join(pkg, '_probe.html'), 'w').write('<!doctype html><meta charset=utf-8><script src="rig.js"></script><script>(async()=>{window.rig=await CharacterRig.load("rig.json");window.ready=1})()</script>')
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=pkg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.5)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, executable_path='/opt/pw-browsers/chromium'); pg = b.new_page()
        pg.goto(f'http://127.0.0.1:{port}/_probe.html'); pg.wait_for_function('window.ready', timeout=30000)
        print(json.dumps(pg.evaluate('()=>{' + code + '}'), ensure_ascii=False)); b.close()
finally: srv.terminate(); os.remove(os.path.join(pkg, '_probe.html'))
