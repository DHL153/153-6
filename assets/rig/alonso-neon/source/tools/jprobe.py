import sys,json,threading,functools,http.server,socketserver
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=socketserver.ThreadingTCPServer(('127.0.0.1',0),functools.partial(Q,directory='/home/claude/153-6'));port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page();pg.goto(f'http://127.0.0.1:{port}/assets/rig/alonso-neon/source/tools/jprobe.html?'+(sys.argv[1] if len(sys.argv)>1 else ''))
    pg.wait_for_function("document.title==='done'||document.title.startsWith('ERR')",timeout=20000)
    if pg.title()!='done':print(pg.title())
    else:
        R=pg.evaluate('R');O=(208,486)
        to=lambda p:[round(p[0]/2+O[0],1),round(p[1]/2+O[1],1)]
        for k in ['hip','torso','head','armU','armF','armL','foreF','weapon','G']: print(k,to(R[k]) if R[k] else None)
        for s in ['near','far']:
            L=R['legs'][s];print(s,{k:to(L[k]) for k in ['hip','knee','ankle']},'foot',round(L['foot'],3),L.get('boot'))
        print('a',R['a'],'st',R['st'],'A',R['A'])
        for k in ['pommel','wGrip','armLgrip','armLpiv']: print(k,to(R[k]))
        print('armLrot',R['armLrot'],'wRot',R['wRot'],'swapL',R['swapL'])
    b.close()
srv.shutdown()
