# assets/rig — 리깅 캐릭터 (2026-10-16)

팀원이 만든 2D 컷아웃 리그를 게임에 붙이는 자리. 규칙은 `character-rig-assistant` 스킬의 `references/07_runtime.md`를 따른다.

```
assets/rig/
  rig.js                 재생 엔진(공통, CharacterRig + RunAnimator). 캐릭터마다 복사하지 않는다
  <id>/rig.json          리그 데이터(그림 위치·뼈대·그리는 순서·표정). 팀원 도구가 쓰는 원본
  <id>/rig.def.js        rig.json을 window.MR_RIG_DEFS[id]에 넣는 JS 포장 (file:// 에서도 fetch 없이 읽히게)
  <id>/parts/*.png       부위 그림(리그 단위, 원본의 2배)
```

- 게임 연결 코드는 `index.html` 맨 아래 `<script id="mr-rig-js">` (MRRig). `layoutBattleTeam`이 발 위치·몸 높이를 넘기고, `setBattleHeroState`가 공격·스킬·승리를 알린다.
- **적용된 캐릭터: 8번 니콜** (`MRRig` 안의 `REGISTRY={8:'rust-fork-girl'}`). 리그 원본이 `characters/char_0008.png`라 도감·카드·상점 썸네일 같은 정지 그림은 기존 PNG를 그대로 쓴다.
- 니콜이 나오면 전투(1~3인 어느 자리든)·마이룸·친구 방문·미니룸에서 그림 대신 리그로 그린다. 전투 크기는 다른 캐릭터와 같은 규칙(512 그림에서 머리~발 290px).
- 설정 > 🖥️ 화면 > **리깅 캐릭터**(기본 ON)를 끄면 모든 리그 캐릭터가 기존 그림 프레임으로 돌아간다.
- 새 캐릭터 추가 = `assets/rig/<id>/`에 넣고 `<script src=…rig.def.js>` 한 줄 + `REGISTRY[번호]='<id>'`.
- `rig.json`을 바꾸면 `rig.def.js`도 다시 만든다:
  `python3 -c "import json;d=json.load(open('assets/rig/<id>/rig.json'));open('assets/rig/<id>/rig.def.js','w').write('window.MR_RIG_DEFS=window.MR_RIG_DEFS||{};window.MR_RIG_DEFS[\\'<id>\\']='+json.dumps(d,ensure_ascii=False,separators=(\\',\\',\\':\\'))+';')"`
