import sys,threading,functools,http.server,socketserver
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=socketserver.ThreadingTCPServer(('127.0.0.1',0),functools.partial(Q,directory='/home/claude/153-6'));port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page()
    pg.goto(f'http://127.0.0.1:{port}/assets/rig/basil-neon/source/tools/view.html?'+sys.argv[1])
    pg.wait_for_function("document.title==='done'||document.title.startsWith('ERR')",timeout=20000)
    print(pg.evaluate(sys.argv[2]));b.close()
srv.shutdown()
