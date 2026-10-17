import threading,functools,http.server,socketserver,json
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=socketserver.ThreadingTCPServer(('127.0.0.1',0),functools.partial(Q,directory='/home/claude/153-6'));port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page();pg.goto(f'http://127.0.0.1:{port}/assets/rig/alonso-sky/source/tools/atkprobe.html')
    pg.wait_for_function("document.title==='done'||document.title.startsWith('ERR')",timeout=20000)
    if pg.title()!='done':print(pg.title())
    else:
        R=pg.evaluate("R");json.dump(R,open("/tmp/claude-0/-home-claude/c76b6f25-7843-5cc6-b177-7797dcb3a853/scratchpad/atkp.json","w"));[print(r) for r in R[::3]]
    b.close()
