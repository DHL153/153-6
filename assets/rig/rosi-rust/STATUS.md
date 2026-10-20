# 4 러스트 로시 (rosi-rust) — 상태

## 2026-10-21 00:26 시작 (DHL 00:26 '러스트 로시 인게임에 넣어줄 수 있나요?' · 00:27 '리깅 편집 툴 목록에도')
- 원화 = char_0004.png (스킬 사례 gatling-nun v7.8 원화와 같은 그림, 픽셀 차이 최대 3/255) → source/ref512.png
- 리그 = 스킬 사례 gatling-nun v7.8 rig.json 그대로(source/rig_v16_gatling-nun.json) + 게임 엔진 이름 맞춤: legs.near/far.stand(숫자) → idleStance, gait.headTilt → headRun. 조각 27장 그대로(참조 = 파일 목록 27/27)
- 팔 구조 = carry rigidFore: 팔뚝+장갑 = 손잡이 뼈 한 몸, 소매만 어깨에서 돌아 팔꿈치 점을 겨눔 · 총 = 가슴에 대한 무게 스프링 · 탄띠 = 원본 C 곡선 닮음 변환

## 엔진 (assets/rig/rig.js, 캐시 태그 20261021r4)
- 게임 엔진에 두 손 무거운 무기(carry) 모드가 없었음(게임 엔진 = 니콜 계열, 스킬 엔진 v16 = carry 있음 — 두 갈래로 갈라져 있었음). v16 의 carry 를 옮김: 탄띠 사슬, _arms/_armIK/_carry/_gunSoft/_fireTick, fire(true/false), holdAt, 베일 뒷면(capeFill)·두건 가장자리 고정, 옵션 gait.startPhase·accelLean·idleRise·breathScale·lockMax·swingFoot, boot.toeX·idleDorsi, actions.nearWin/farWin — 전부 rig.json 에 있을 때만 켜짐
- 이름 겹침 막음: 탄띠 "belt" 그리기는 carry.belt 가 있을 때만(2 러스트 둘시네 parts.belt 와 겹침 — M01 같은 종류)
- 새 옵션 attack(name, {hold}) — holdAt 자세에 닿은 뒤 그만큼 연사(게임 전투 '짧은 연사')
- 검사: 게임 리그 20종(로시 빼고) 옛 엔진 ↔ 새 엔진, 서기·달리기·공격·표정·전투 박자(stepHz 2.22, VX 380/500/650)·달리다 공격 37~40장면 픽셀 차이 0
- 검사: 로시 v16(승인본) ↔ 게임 엔진 — 다른 곳은 '서 있다가 다시 달릴 때 발 이어받기'(게임 엔진의 방향 바꿀 때 튐 고침, 모든 캐릭터 같은 규칙)뿐. 그걸 끄면 29장면 픽셀 차이 0. 켠 채로 발 튐 재 보니 v16 과 같음(최대 13.1/프레임)

## 게임 연결 (index.html MRRig)
- REGISTRY 4:'rosi-rust', rig.def.js 스크립트
- 전투 공격 = ui.attack 'fire' + ui.attackOpts {hold:.2}: 1.5배속, 첫 발 0.13초(hitDelayMs 133), 버티는 자세에서 0.2초 = 4발, 공격 약 0.64초. 도감 클릭·시작 선택 카드도 같은 옵션
- 스킬 컷인 = cutHold .30(버티며 쏘는 자세 + 외침, 그 자세로 계속 연사 반동)
- 마이룸·도감 터치 = ui.tap / ui.long ['heft'] (총 추스르기 + 윙크). carry 리그는 공통 반응(손 흔들기·폴짝 등)을 엔진이 받지 않음 — 손 그림이 바뀌는 동작은 손잡이를 쥔 캐릭터에서 깨짐(G28)
- 걸음: 전투 VX ≈ 633 리그/초 · 초당 2.22걸음 → 한 걸음 ≈ 다리 길이 2.4배라 걷기 불가(P6) → gait.strideFlex [.45,.68]: 보폭 ≤ 다리 0.73배, 디딤 .145, 짧고 묵직한 종종 달리기(펴짐 ≤ .95, 미끄러짐 0, 소매 회전 −5.6~4.8° — 승인 범위 −3.8~6.7 안, 손 이탈 0, 총 바닥 여유 ≥ 4) 📝
- 마이룸 좌우 왕복도 ≈ 430 리그/초 → 무거운 걷기 그대로면 초당 5.1걸음(종종걸음) → ui.roomStep 으로 전투와 같은 박자(2.22)
- 확인: PC 1280×800 · 폰 390×844 시작 선택·미리보기·전투·공격·스킬 컷인·도감 2장(클릭)·필살기 컷신·마이룸(터치·길게) 페이지 오류 0

## 남은 것 / 확인받을 것
- DHL 검수: 전투·마이룸 종종 달리기(처음 만든 값), 연사 4발 길이
- 이펙트(팀 몫): 공격 때 게임 공통 칼 궤적(파란 베기)이 총 캐릭터에도 나옴 — 총구 불꽃 등은 이벤트 fire(x,y,dx,dy)로 연결 가능
- 마이룸 반응이 지금은 1종(추스르기+윙크). 손을 안 떼는 몸 반응(끄덕·움찔·폴짝 + 총 반동)을 더 만들 수 있음

## 편집 툴 (10-21 01:31, 버전 162)
- 목록 맨 위 '4 러스트 로시 v1' + rigs/rosi-rust/rig.def.js(source/tools/pack_editor.py — 조각·원화 1024 를 data URI 로, 파일 수 한도 511) · 기준 그림 = 원화 · 진행 칸(그림은 페이지 안 data URI)
- 편집 툴 rig.js = 게임 새 엔진 그대로(캐시 태그 20261021r4) — 편집 툴 옛 rig.js 는 게임 옛 엔진과 같은 파일이었음(md5 같음)
- 편집 툴 '공격'도 ui.attackOpts 를 넘김(게임과 같은 짧은 연사 4발) — attackOpts 없는 캐릭터는 그대로
- 확인: 로컬 PC 1280×900 · 폰 390×844 목록·서기·달리기·공격(4발) 페이지 오류 0
- 실수 기록: review/rig-mistakes-and-todo.md 2026-10-21 (3)~(6)

## 10-21 06:20 v1.1 표정·깜빡임·반응 (DHL 05:59 '기본 표정도 없네요, 눈이 깜빡이는 것도 없어요, 반응도 같이')
- 시트: DHL 06:06 source/sheets_faces_0606.png — 원화 머리 다시 그리기 3×2(프롬프트 하나, 첨부 = source/refs/attach_E_face.png = 사례집 E1~E3 첨부). 사례집 9칸은 선이 깨졌지만 6칸·넓은 간격은 깨끗(칸 배율 1.9 → 4배 조각)
- source/tools/faces4.py: 칸마다 두건·이마 띠·머리카락(얼굴 빼고, head.png 알파 안)에 SIFT 닮음 → ECC affine(.98) → 얼굴만 오려 원화 머리 위 조각, 살빛 맞춤
  - 웃음·화남·슬픔·놀람 = 얼굴 전체(이마 띠 아래 가장자리까지) · 깜빡임 반·감음 = 눈 부분만(위 y169~174 = 다시 그린 눈썹 줄 뺌, 코 선·입 = 원화)
  - faces: happy·angry·sad·surprised(+grimace) 추가 · blinkFaces {half, closed} · 기본 = 원화 얼굴 · 윙크·외침·집중 = v7.8 그대로
- 반응(source/tools/react4.py): nod 끄덕 · hop 작은 폴짝 · surprise 움찔 · sway 살랑(길게, 끝 윙크) — 손은 손잡이에서 안 뗌(G28), 몸·어깨·총 오프셋만
  - ui.tap = heft → nod → hop → surprise · ui.long = sway
  - 검사(actprobe, 서서): 다리 펴짐 ≤ .98(폴짝) · 디딘 발 미끄러짐 0 · 총 바닥 여유 ≥ 4(몸이 낮아질 때 gunY 로 총을 듦) · 소매 회전 = 승인된 heft 범위 안(폴짝 12.6/−11.3 ≤ heft 16.2/−11.5) · 손 이탈 0
  - 걷다가 누르면 바닥 여유가 2.3까지 줄어듦(땅 위, 공통 반응과 같은 넘어감) 📝
- 게임 확인 PC·폰: 마이룸 터치 차례 heft → nod(웃음) → hop(웃음) → surprise · 길게 sway · 페이지 오류 0
- 편집 툴 v163: '4 러스트 로시 v1.1' · 새 '반응' 줄(rig.json ui.tap·ui.long 이 있는 캐릭터만 보임 — 지금은 로시) · 진행 칸 v1.1
- 📝 DHL 검수: 반응 4종 움직임 크기 · 깜빡임 때 눈 밑 그늘이 잠깐 옅어짐(다시 그린 눈엔 그늘이 없음)
