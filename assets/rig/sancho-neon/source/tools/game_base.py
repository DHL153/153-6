import threading,functools,http.server,socketserver,time,sys,json
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=socketserver.ThreadingTCPServer(('127.0.0.1',0),functools.partial(Q,directory='/home/claude/153-6'));port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
O='/tmp/claude-0/-home-claude/c76b6f25-7843-5cc6-b177-7797dcb3a853/scratchpad/game/'
def boot(p,w=1280,h=800):
    b=p.chromium.launch();pg=b.new_page(viewport={'width':w,'height':h});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/index.html');time.sleep(3)
    pg.get_by_role('button',name='Skip',exact=True).click();time.sleep(1.5)
    pg.get_by_role('button',name='Next',exact=True).click();time.sleep(2)
    for i in range(6):
        cards=pg.locator('.mr-starter-card')
        if cards.count()==0: break
        cards.first.click();time.sleep(.6)
        nx=pg.get_by_role('button',name='Next',exact=True)
        if nx.count() and nx.first.is_enabled(): nx.first.click()
        else:
            st=pg.get_by_role('button',name='Start')
            if st.count(): st.first.click()
        time.sleep(1.2)
    return b,pg,errs
def play(p,w=1280,h=800):
    b,pg,errs=boot(p,w,h)
    pg.get_by_role('button',name='Preview').first.click();time.sleep(1.5)
    pg.get_by_role('button',name='Confirm & play').first.click();time.sleep(4)
    return b,pg,errs
