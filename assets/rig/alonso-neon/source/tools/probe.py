import sys,json,threading,functools,http.server,socketserver
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=socketserver.ThreadingTCPServer(('127.0.0.1',0),functools.partial(Q,directory='/home/claude/153-6'));port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
def run(q=''):
    with sync_playwright() as p:
        b=p.chromium.launch();pg=b.new_page();pg.goto(f'http://127.0.0.1:{port}/assets/rig/alonso-neon/source/tools/probe.html?'+q)
        pg.wait_for_function("document.title==='done'||document.title.startsWith('ERR')",timeout=20000)
        if pg.title()!='done':print(pg.title());return None
        R=pg.evaluate('R');b.close();return R
def report(R):
    import math
    mx={'kneeJump':0,'footJump':0,'ankleJump':0}
    for s in ['near','far']:
        ks=[r[s]['k'] for r in R];fs=[r[s]['f'] for r in R]
        kj=max(abs(ks[i+1]-ks[i]) for i in range(len(ks)-1));fj=max(abs(fs[i+1]-fs[i]) for i in range(len(fs)-1))
        acc=max(abs(ks[i+1]-2*ks[i]+ks[i-1]) for i in range(1,len(ks)-1))
        print(s,'knee min/max',min(ks),max(ks),'max step',round(kj,1),'max accel',round(acc,1),'| foot ang min/max',min(fs),max(fs),'step',round(fj,1))
    hy=[r['hipY'] for r in R];print('hipY',min(hy),max(hy),'max accel',round(max(abs(hy[i+1]-2*hy[i]+hy[i-1]) for i in range(1,len(hy)-1)),2))
if __name__=='__main__':
    R=run(sys.argv[1] if len(sys.argv)>1 else '');report(R);json.dump(R,open('/tmp/claude-0/-home-claude/c76b6f25-7843-5cc6-b177-7797dcb3a853/scratchpad/probe.json','w'))
