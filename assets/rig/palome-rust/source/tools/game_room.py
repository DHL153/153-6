# 마이룸(머리 'My Room' 버튼) 여러 장: 시작 선택에서 마이룸 캐릭터 = 번호 NN — python3 game_room.py 가로 세로 이름 NN
import os
exec(open(os.path.dirname(os.path.abspath(__file__)) + '/game_base.py').read())
W = int(sys.argv[1]); H = int(sys.argv[2]); tag = sys.argv[3]; NN = sys.argv[4]
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': W, 'height': H}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/index.html'); time.sleep(3)
    pg.get_by_role('button', name='Skip', exact=True).click(); time.sleep(1.5)
    pg.get_by_role('button', name='Next', exact=True).click(); time.sleep(2)
    for step in range(4):
        if step == 2:
            c = pg.locator(f'.mr-starter-card:has(img[src*="characters/char_{NN}"])'); c.first.scroll_into_view_if_needed(); c.first.click(); time.sleep(.8)
        else: pg.locator('.mr-starter-card').first.click(); time.sleep(.6)
        nx = pg.get_by_role('button', name='Next', exact=True)
        if nx.count() and nx.first.is_enabled(): nx.first.click()
        else: pg.get_by_role('button', name='Preview').first.click()
        time.sleep(1.2)
    time.sleep(1); pg.get_by_role('button', name='Confirm & play').first.click(); time.sleep(4)
    pg.get_by_role('button', name='Collection').first.click(); time.sleep(2.5)
    pg.screenshot(path=O + f'{tag}_coll.png')
    for i in range(4):
        time.sleep(1.5); pg.screenshot(path=O + f'{tag}_room{i}.png')
    print('roomLive', pg.evaluate("()=>{const r=MRRig.roomLive;return r?[...(r.values?r.values():[])].map(e=>e.id):null}"))
    print('errs', [e for e in errs if 'handleAsset' not in e][:5]); b.close()
srv.shutdown()
