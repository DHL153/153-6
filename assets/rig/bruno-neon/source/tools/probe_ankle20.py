"""20 네온 브루노 — 발목 꺾임 표: 정강이 방향 − 부츠 각(r, 도) · 쪽별 · 대기 / 달리기 한 주기 / 달리다 공격 / 서서 공격
엔진 legPose(무릎·발목·foot) 로 r = atan2(발목−무릎) − 90° − foot. 서 있는 원화 다리 그림(standW)도 같이
실행: python3 tools/probe_ankle20.py
"""
import threading, functools, http.server, socketserver
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(Q, directory='/home/claude/153-6')); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
JS = """(mode)=>{const an=window.__an,rig=window.__rig,out=[];
const R=()=>{const lp=rig.legPose,o={};for(const s of ['near','far']){const q=lp[s];o[s]=+(((Math.atan2(q.ankle[1]-q.knee[1],q.ankle[0]-q.knee[0])-Math.PI/2-q.foot)*180/Math.PI+540)%360-180).toFixed(1)}return o};
const VX=mode==='idle'||mode==='satk'?0:620;
for(let i=0;i<120;i++)an.update(1/60,{vx:VX,facing:1});
if(mode==='ratk'||mode==='satk')an.attack('smash');
for(let i=0;i<=(mode==='run'?40:70);i++){const r=R();out.push([+(i/60).toFixed(3),+an.A.toFixed(2),r.near,r.far,+an._standW('near',true).toFixed(2)]);an.update(1/60,{vx:mode==='run'?620:0,facing:1})}
return out}"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); pg.goto(f'http://127.0.0.1:{port}/assets/rig/bruno-neon/source/tools/view.html?pre=0')
    pg.wait_for_function("document.title==='done'||document.title.startsWith('ERR')", timeout=20000)
    for mode in ('idle', 'run', 'ratk', 'satk'):
        rows = pg.evaluate(JS, mode); nr = [r[2] for r in rows]; fr = [r[3] for r in rows]
        print(f'{mode:5s} near r {min(nr):7.1f} ~ {max(nr):6.1f} · far r {min(fr):7.1f} ~ {max(fr):6.1f}')
        if mode in ('idle', 'ratk'): print('   ', [(r[0], r[2], r[3], r[4]) for r in rows[::6]])
    b.close()
srv.shutdown()
