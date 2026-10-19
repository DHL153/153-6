# 도감 2/2(전투) 칸 클릭 → 공격(내려찍기) 되는지: python3 game_dexclick2.py 가로 세로 이름
import os
exec(open(os.path.dirname(os.path.abspath(__file__)) + '/game_base.py').read())
W = int(sys.argv[1]); H = int(sys.argv[2]); tag = sys.argv[3]; IDX = int(os.environ.get('NUM', '12')) - 1   # 캐릭터 번호 → 전투 인덱스
with sync_playwright() as p:
    b, pg, errs = play(p, W, H)
    pg.evaluate(f"()=>MRWorld.openDetail({{meta:BATTLE_CHARACTER_META[{IDX}],tier:'L',owned:true,count:1,slot:0,team:[...battleTeam],slotRaw:i=>['주 캐릭터','동료 1','동료 2'][i],roomOwned:()=>true}})")
    time.sleep(2.5); pg.locator('.mrw-nav.next').click(); time.sleep(2.0); pg.locator('.mrw-hero').click(); 
    for i, t in enumerate([.1, .2, .3, .4, .5]):
        time.sleep(t - [0, .1, .2, .3, .4][i]); pg.locator('.mrw-hero').screenshot(path=O + f'{tag}_dexb{i}.png')
    print('errs', [e for e in errs if 'handleAsset' not in e][:5]); b.close()
srv.shutdown()
