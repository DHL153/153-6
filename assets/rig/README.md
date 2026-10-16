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
- 설정 > 🖥️ 화면 > 화면 흔들림 아래 **리깅 캐릭터 테스트**를 켜면 전투 슬롯 0이 `rust-fork-girl`로 바뀐다(화면만, 경제·판정 그대로).
- 정식 적용은 `MRRig.registry[전투 캐릭터 번호] = '<id>'` 로 등록한다 (지금은 비어 있음).
- `rig.json`을 바꾸면 `rig.def.js`도 다시 만든다:
  `python3 -c "import json;d=json.load(open('assets/rig/<id>/rig.json'));open('assets/rig/<id>/rig.def.js','w').write('window.MR_RIG_DEFS=window.MR_RIG_DEFS||{};window.MR_RIG_DEFS[\\'<id>\\']='+json.dumps(d,ensure_ascii=False,separators=(\\',\\',\\':\\'))+';')"`
