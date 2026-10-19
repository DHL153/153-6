# 도감 상세에서 그림 칸 클릭 → 공격(올려베기) 되는지: python3 game_dexclick.py 가로 세로 이름
import os
exec(open(os.path.dirname(os.path.abspath(__file__)) + '/game_base.py').read())
W = int(sys.argv[1]); H = int(sys.argv[2]); tag = sys.argv[3]; IDX = int(os.environ.get('NUM', '13')) - 1   # 캐릭터 번호 → 전투 인덱스
with sync_playwright() as p:
    b, pg, errs = play(p, W, H)
    pg.evaluate(f"()=>MRWorld.openDetail({{meta:BATTLE_CHARACTER_META[{IDX}],tier:'L',owned:true,count:1,slot:0,team:[...battleTeam],slotRaw:i=>['주 캐릭터','동료 1','동료 2'][i],roomOwned:()=>true}})")
    time.sleep(2.5); pg.locator('.mrw-hero').click(); 
    for i, t in enumerate([.15, .3, .45]):
        time.sleep(t - [0, .15, .3][i]); pg.locator('.mrw-hero').screenshot(path=O + f'{tag}_dexc{i}.png')
    print('errs', [e for e in errs if 'handleAsset' not in e][:5]); b.close()
srv.shutdown()
