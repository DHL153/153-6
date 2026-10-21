"""편집 툴(리깅 편집 툴 artifact)에 17 네온 루시아 넣기 — 받은 페이지 HTML → 새 HTML (파일 수 511 그대로: palome9_v17.jpg 를 페이지 안 data URI 로 옮기고 rigs/lucia-neon/rig.def.js 하나 더함)
python3 -I editor_add17.py 받은.html 새.html 리그버전 진행그림.jpg 시각(예 2026-10-21T12:40) [palome9_v17.jpg]
"""
import sys, base64, re
src, dst, ver, prog, when = sys.argv[1:6]; p9 = sys.argv[6] if len(sys.argv) > 6 else None
s = open(src, encoding='utf-8').read()
def once(old, new):
    global s
    assert s.count(old) == 1, (old[:80], s.count(old)); s = s.replace(old, new)
# 1) 스크립트
m = re.search(r'<script src="rigs/lucia-rust/rig\.def\.js\?v=[0-9a-f]+"></script>\n', s); assert m
s = s[:m.end()] + f'<script src="rigs/lucia-neon/rig.def.js?v={ver}"></script>   <!-- 17 네온 루시아(조각·원화 data URI 한 파일 — 파일 수 한도 511) -->\n' + s[m.end():]
# 2) 캐릭터 목록(맨 위 = 최근)
note = ("v1(10-21 " + when[11:] + ", DHL 06:46 ‘네온 루시아 작업 진행해요~’) 새 원화(0번 09:54, 7 러스트 루시아 자세 — 방패 = 가까운 손(손은 방패 뒤, 안 보임) · 도끼 = 먼 손) · "
        "7 러스트 루시아 v1.5 리그 구조 그대로(방패 = 가까운 어깨에 붙음·출렁임, 한 손 도끼 내려찍기, 드워프 종종걸음, 공격 표정 눈 뜸, 타격 먼 발 10) · "
        "가려진 곳 = 방패만 지운 원화 11:32 + 먼 팔·도끼만 지운 원화 11:36 · 조각 시트 11:03(표정 6 + 깜빡임 2 · 도끼 · 어깨갑 · 먼 윗팔·팔뚝 · 달리는 다리·부츠·무릎 보호대) · "
        "목 가리개 = 머리 앞 상체 조각(머리가 돌아도 가리개 아래 끝이 가슴 판에 붙음) · 공격 중(0.05~0.88)만 먼 윗팔·팔뚝·어깨갑 = 시트 조각(원화 팔뚝 갑은 앞을 향해 줄어 보인 덩어리라 들면 조각나 보였음), 대기 = 원화 · "
        "게임 REGISTRY 17 · 컷인 .34")
once("const CHARS=[\n", "const CHARS=[\n  {id:'lucia-neon',no:17,name:'17 네온 루시아 v1',note:'" + note + "',updated:'" + when + "'},\n")
# 3) 기준 그림
once("  'lucia-rust':[{k:'art'", "  'lucia-neon':[{k:'art',label:'원화 · 서 있는 자세 (새 원화 0번 09:54, 7 러스트 루시아와 같은 자세)',src:(window.MR_REF_ART||{})['lucia-neon'],art:1}],   // 원화 1024 = rig.def.js 안 data URI(파일 수 한도)\n  'lucia-rust':[{k:'art'")
# 4) 진행 칸(맨 위)
b64 = base64.b64encode(open(prog, 'rb').read()).decode()
sec = f'''  <section class="panel prog" aria-labelledby="l17T">
    <div><h2 id="l17T">17 네온 루시아 v1 <small>2026-10-21 {when[11:]} · 7 러스트 루시아 v1.5 구조 · 게임 반영(REGISTRY 17)</small></h2>
    <p class="lead">네온 원화는 도끼를 가까운 손으로 머리 위에 든 자세라, 7 러스트 루시아 자세(방패 = 가까운 손, 도끼 = 먼 손)로 새 원화를 받아(0번 09:54) 같은 리그 구조·동작을 쓰고 조각만 네온으로 바꿨어요. 위에서 ‘17 네온 루시아 v1’을 고르고 ‘공격’, ‘달리기’, ‘표정’으로 보세요. ‘기준 그림 → 원화’로 서 있는 자세를 겹쳐 볼 수 있어요.</p></div>
    <ol class="steps">
      <li class="done"><b>새 원화</b><span>0번 09:54 · 러스트 자세</span></li>
      <li class="done"><b>조각</b><span>시트 11:03 · 지운 원화 11:32·11:36</span></li>
      <li class="done"><b>v1</b><span>대기·달리기·내려찍기·표정</span></li>
      <li class="done"><b>게임</b><span>전투·컷인·도감·마이룸</span></li>
      <li class="now"><b>확인</b><span>DHL 검수</span></li>
    </ol>
    <figure><img src="data:image/jpeg;base64,{b64}" alt="17 네온 루시아 v1 — 원화·리그 대기·표정, 내려찍기 8장면, 달리기 8장면" loading="lazy"><figcaption>위: 원화 · 리그 서 있기 · 표정 6 + 깜빡임 2 / 가운데: 내려찍기(들어 올림 0.18 · 예비 0.27 · 휘두름 0.32·0.36 · 타격 0.40 · 버팀 0.58 · 들어 돌림 0.68 · 돌아옴 0.82) — 노란 줄 = PC 전투 칸 위 끝, 빨간 줄 = 폰 / 아래: 달리기 1/60초씩</figcaption></figure>
    <p class="note"><b>{when[11:]} v1:</b> ①<b>대기 = 원화</b> — 원화 조각과 원화 겹침 차이 189px(7 러스트 762), 엔진 대기 실루엣 겹침 .972~.984 ②<b>방패</b> = 가까운 어깨 뼈(상체 숙임 60% 되세움 + 출렁임), 가까운 손은 방패 뒤라 그리지 않음 ③<b>목 가리개</b> = 상체에 붙은 따로 조각(머리 앞) — 머리 밑 턱은 시트 머리로 채움 ④<b>먼 팔</b>: 대기·달리기 = 원화 어깨갑·회색 윗팔 판·크림 팔뚝 갑, 공격 중(0.05~0.88) = 시트 어깨갑(아래 테 온전)·윗팔·옆에서 본 팔뚝(원화 팔뚝 갑은 앞을 향해 줄어든 덩어리라 팔을 들면 팔꿈치가 조각나 보였음) ⑤<b>내려찍기 키</b> = 7 러스트 키를 네온 어깨·팔 길이로 옮겨 다시 잼 — 펴짐 ≤ .89 · 손목 ≤ 29° · 타격 날 앞 끝 = 땅 · 공격 중 도끼 꼭대기 PC 칸 위 끝 13px · 폰 12px 아래 ⑥<b>달리기</b> = 시트 허벅지 아래쪽·정강이+부츠·무릎 보호대(부츠 = 원화 크기), 7 러스트 드워프 종종걸음 그대로.</p>
  </section>
'''
once('  <section class="panel prog" aria-labelledby="r24T">', sec + '  <section class="panel prog" aria-labelledby="r24T">')
# 5) 파일 수: 9 팔로메 진행 그림 한 장을 페이지 안으로
if p9:
    once('src="progress/palome9_v17.jpg"', 'src="data:image/jpeg;base64,' + base64.b64encode(open(p9, 'rb').read()).decode() + '"')
open(dst, 'w', encoding='utf-8').write(s); print('ok', len(s) // 1024, 'KB')
