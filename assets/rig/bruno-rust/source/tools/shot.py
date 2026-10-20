# 리그 그림 찍기: shot.py '쿼리' 출력.png  (저장소 루트를 띄워 tools/view.html 렌더)
import sys,threading,functools,http.server,socketserver
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
ROOT='/home/claude/153-6'
srv=socketserver.ThreadingTCPServer(('127.0.0.1',0),functools.partial(Q,directory=ROOT));port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1200,'height':900});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto(f'http://127.0.0.1:{port}/assets/rig/bruno-rust/source/tools/view.html?'+sys.argv[1])
    pg.wait_for_function("document.title==='done'||document.title.startsWith('ERR')",timeout=20000)
    if pg.title()!='done':print(pg.title())
    pg.locator('#c').screenshot(path=sys.argv[2]);print('ERR',errs);b.close()
srv.shutdown()
