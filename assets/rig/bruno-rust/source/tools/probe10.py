# 리그 뼈 각 보기: python3 probe10.py '쿼리' 'JS 식(rig, an 사용)'
import sys,threading,functools,http.server,socketserver,json
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=socketserver.ThreadingTCPServer(('127.0.0.1',0),functools.partial(Q,directory='/home/claude/153-6'));port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page();pg.goto(f'http://127.0.0.1:{port}/assets/rig/bruno-rust/source/tools/view.html?'+sys.argv[1])
    pg.wait_for_function("document.title==='done'||document.title.startsWith('ERR')",timeout=20000)
    print(json.dumps(pg.evaluate("()=>{const rig=window.__rig,an=window.__an;return ("+sys.argv[2]+")}"),ensure_ascii=False));b.close()
srv.shutdown()
