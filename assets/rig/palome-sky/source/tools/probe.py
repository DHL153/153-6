# 엔진 값: probe.py '쿼리'  (probe.html 의 code=식 결과를 찍음)
import sys,threading,functools,http.server,socketserver,urllib.parse
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=socketserver.ThreadingTCPServer(('127.0.0.1',0),functools.partial(Q,directory='/home/claude/153-6'));port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page()
    for q in sys.argv[1:]:
        pg.goto(f'http://127.0.0.1:{port}/assets/rig/palome-sky/source/tools/probe.html?'+q)
        pg.wait_for_function("document.title.startsWith('OK')||document.title.startsWith('ERR')",timeout=20000); print(pg.title()[:3000])
    b.close()
srv.shutdown()
