# 10 브루노 — 공격 중 두 발 x(골반 기준)·A·다리 그림(서기/달리기) 표: python3 probe_feet10.py [idle|run]
import sys,threading,functools,http.server,socketserver,json
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=socketserver.ThreadingTCPServer(('127.0.0.1',0),functools.partial(Q,directory='/home/claude/153-6'));port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
mode=sys.argv[1] if len(sys.argv)>1 else 'run'; keepRun=len(sys.argv)>2
JS="""()=>{const an=window.__an,rig=window.__rig,VX=%s,KEEP=%s;const out=[];
for(let i=0;i<120;i++)an.update(1/60,{vx:VX,facing:1});
an.attack('smash');
for(let i=0;i<=66;i++){ if(i%%3==0){const f=an.ft; out.push([+(i/60).toFixed(3), +an.A.toFixed(3), +f.near.x.toFixed(1), +f.far.x.toFixed(1), +(f.near.lift||0).toFixed(1), +(f.far.lift||0).toFixed(1), +an._standW('near',true).toFixed(2)])}
  an.update(1/60,{vx:KEEP?VX:0,facing:1});}
return out}"""%( '620' if mode=='run' else '0', 'true' if keepRun else 'false')
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page();pg.goto(f'http://127.0.0.1:{port}/assets/rig/bruno-rust/source/tools/view.html?pre=0')
    pg.wait_for_function("document.title==='done'||document.title.startsWith('ERR')",timeout=20000)
    rows=pg.evaluate(JS); print('t A nearX farX nearLift farLift standW')
    for r in rows: print(*r)
    b.close()
srv.shutdown()
