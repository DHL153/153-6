"""편집 툴에 27 스카이 루시아 넣기 — 받은 페이지 HTML → 새 HTML (파일 수 511 그대로: rigs/lucia-neon/rig.def.js 에 lucia-sky 정의를 덧붙임)
python3 editor_add27.py 받은.html 새.html 리그버전 진행그림.jpg 시각(2026-10-21T19:55)"""
import sys, base64
src, dst, ver, prog, when = sys.argv[1:6]
s = open(src, encoding='utf-8').read()
def once(old, new):
    global s
    assert s.count(old) == 1, (old[:80], s.count(old)); s = s.replace(old, new)
T = when[11:]
note = (f"v1({'10-21 ' + T}, DHL 19:02 ‘스카이 루시아 작업 진행해 보시죵’) 새 원화 없음 — 27 원화가 7·17 루시아 자세의 원본 · "
        "17 네온 루시아 v1.2 리그 구조 그대로(방패 = 가까운 어깨에 붙음·출렁임, 한 손 도끼 내려찍기, 공격 중 다리 안 바뀜, 드워프 종종걸음) + 가까운 주먹 = 방패 자식(7 러스트처럼 방패 오른쪽 끝에 보임) · "
        "가려진 곳 = 방패+가까운 주먹 지운 원화 19:21 + 먼 팔·도끼 지운 원화 19:21 · 조각 시트 19:30(표정 6 + 깜빡임 2 — 투구 가리개라 눈·눈썹만 · 도끼 · 어깨갑 · 먼 윗팔·팔뚝 · 달리는 다리·부츠·무릎 보호대) · 게임 REGISTRY 27 · 컷인 .36")
once("const CHARS=[\n", "const CHARS=[\n  {id:'lucia-sky',no:27,name:'27 스카이 루시아 v1',note:'" + note + "',updated:'" + when + "'},\n")
once("  'lucia-neon':[{k:'art'", "  'lucia-sky':[{k:'art',label:'원화 · 서 있는 자세 (char_0027 그대로)',src:(window.MR_REF_ART||{})['lucia-sky'],art:1}],   // 원화 1024 = rigs/lucia-neon/rig.def.js 안 data URI(파일 수 한도 511 — 17 파일에 같이 담음)\n  'lucia-neon':[{k:'art'")
b64 = base64.b64encode(open(prog, 'rb').read()).decode()
sec = f'''  <section class="panel prog" aria-labelledby="l27T">
    <div><h2 id="l27T">27 스카이 루시아 v1 <small>2026-10-21 {T} · 17 네온 루시아 v1.2 구조 · 게임 반영(REGISTRY 27)</small></h2>
    <p class="lead">27 원화가 7·17 루시아 자세의 원본이라 새 원화 없이 시작했어요. 17 네온 루시아 v1.2 와 같은 리그 구조·동작에 조각만 스카이로 바꾸고, 방패 오른쪽 끝에 보이는 가까운 주먹은 7 러스트처럼 방패에 붙였어요. 위에서 ‘27 스카이 루시아 v1’을 고르고 ‘공격’, ‘달리기’, ‘표정’으로 보세요.</p></div>
    <ol class="steps">
      <li class="done"><b>원화</b><span>char_0027 그대로</span></li>
      <li class="done"><b>조각</b><span>지운 원화 19:21 · 시트 19:30</span></li>
      <li class="done"><b>v1</b><span>대기·달리기·내려찍기·표정</span></li>
      <li class="done"><b>게임</b><span>전투·컷인·도감·마이룸</span></li>
      <li class="now"><b>확인</b><span>DHL 검수</span></li>
    </ol>
    <figure><img src="data:image/jpeg;base64,{b64}" alt="27 스카이 루시아 v1 — 원화·리그 대기·표정, 내려찍기 8장면, 달리기 8장면" loading="lazy"><figcaption>위: 원화 · 리그 서 있기 · 표정 6 + 깜빡임 2 / 가운데: 내려찍기 8장면 / 아래: 달리기 8장면</figcaption></figure>
    <p class="note"><b>{T} v1:</b> ①<b>대기 = 원화</b> — 엔진 대기 실루엣 겹침 .970~.981 ②<b>방패</b> = 가까운 어깨 뼈(숙임 60% 되세움 + 출렁임), <b>가까운 주먹</b> = 방패 자식(같이 움직임) ③<b>먼 팔</b> = 대기·달리기 원화, 공격 중(0.05~0.88)만 시트 윗팔·팔뚝·어깨갑 ④<b>표정</b> = 가리개 위 눈·눈썹만(웃음 칸은 시트 그림이 눈웃음이 약해요 — 다시 받을 수 있어요) ⑤공격 중 도끼 꼭대기 = 전투 칸 위 끝에서 PC 15 · 폰 13px 아래</p>
  </section>
'''
once('  <section class="panel prog" aria-labelledby="l17T">', sec + '  <section class="panel prog" aria-labelledby="l17T">')
open(dst, 'w', encoding='utf-8').write(s); print('ok', len(s) // 1024, 'KB')
