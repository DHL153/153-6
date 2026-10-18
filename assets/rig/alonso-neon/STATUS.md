# 11 네온 알론소 (alonso-neon) — 상태

## 2026-10-18 09:50 시작 (DHL 09:46 "추천대로 · 원안 뽑을 때 손가락 신경")
- 결정: 대기·달리기 = 원화처럼 **두 손으로 칼을 몸 앞에 쥠** · 공격 = 내려찍기(끝 자세 = 전투 그림 런지) · 마이룸 반응 = 몸 동작(폴짝·끄덕 등)
- 두 손이 처음부터 끝까지 손잡이를 놓지 않음 → 21의 손 잡기·놓기(reachIK) 필요 없음
- 요청한 그림: 0 원화 손 수정(두 주먹 손가락 4개 + 엄지) → 1 조각 시트(7×6, 쥔 주먹 8·두 손 겹쳐 쥔 손 1) → 2 동작 시트(달리기 8 + 내려찍기 6)
- 원화 관절점 1차: `source/measure.json` (손·손잡이는 손 고친 원화로 다시 잼). 칼 축 −52.7°(칼끝 오른쪽 위)
- 엔진 opt-in `swordGrip.guard` (rig.js `_swordGuard`): 동작이 없을 때(대기·달리기·몸 반응)도 `_swordRigid`로 두 손이 손잡이를 쥠. 값 gx·gy(골반 기준)·sa·sN·sF·shN·shF·조각 이름·order, 달리기 흔들림 run.{gx,gy,sa}=[진폭,위상], 숨쉬기 breath.{gy,sa}. 다른 리그 6종(대기·달리기·공격·반응) 픽셀 차이 0
- 시험: `assets/rig/alonso-sky/source/tools/guardtest.html` + `guardtest.py` (21 조각으로 엔진만 확인)

## 10:40 원화 손 수정본 받음 (0번) — 합격
- 바뀐 곳은 손 둘레(225~281, 353~417)뿐, 두 주먹 모두 손가락 4개. 게임 마이룸 그림 char_0011.png 교체(21과 같은 방식), 원본 받은 그림 = source/ref512_received.png, 정리본 = source/ref512.png
- 직접 정리 2곳: 지운 은색 고리가 남긴 검은 가시 지움 · 손목과 주먹 사이 작은 구멍 메움
- 손·손잡이 관절점 다시 잼 (measure.json)

## 10:51~ v1 대기·달리기 조립 (DHL 10:51 동작 시트·조각 시트 받음)
- 조립 `source/build_neon.py` (실행: `cd source && python3 -I build_neon.py`): 머리·몸통·골반·어깨갑·두 팔·주먹·다리는 **원화를 오려** 씀(`polys.json` 다각형), 칼 = 원화 칼날·날밑을 세워서 + 시트 손잡이(폼멜은 원화 것 하나)
  - 몸통 = 시트 몸통(3점 아핀, 원화 몸통 자리 안) 위에 원화 몸통. 떨어진 섬·가는 띠는 지움(`islands`·`slivers` — 대기엔 안 보이다 달리기에서 떠 보였음)
  - 아래 주먹 = 원화 외곽선 밖 바지·폼멜 고리는 `outline_cut`으로 뺌(달리기에서 주먹 밑 회색 띠·톱니)
- 대기 = 원화 (jprobe: 골반·머리·어깨·손잡이·무릎 원화 자리). 두 손은 `swordGrip.guard`로 늘 칼을 쥠
- 달리기 다리 = **시트의 곧은 다리 조각**(허벅지·정강이·무릎 덮개·부츠, 1.15배) — 원화 벌린 다리 조각은 옆으로 누워 달리기에 못 씀
  - 엔진 opt-in `legs.near/far.stand = {fade:[lo,hi], boot:{part,sole}, thighImg, shinImg, kneeImg}`: 서 있을 때(A<lo)는 원화 다리, A가 lo→hi 동안 달리기 다리 위에서 옅어짐, 발목 높이(두 부츠 밑창)도 같이 섞임
  - 엔진 opt-in `legs.near/far.thigh·shin`(쪽별 서 있는 길이, A 따라 공통 길이로) — 원화 다리 길이 그대로 대기
  - 엔진 opt-in `swordGrip.guard.runAt.{gx,gy,sa}`: 달릴 때 손잡이 자리를 옮김(손을 가슴 쪽으로)
  - gait: 골반 hipBase −44(다리가 몸 밑으로 모이면 골반이 올라감), strideBase 80·strideK .2, kneeLift .35, heelKick .5, lean .1 — probe: 무릎 뒤집힘 0, 무릎이 엉덩이 위로 0
- 표정 `source/faces11.py`: 시트 face_*(머리 통째) → 머리카락으로 ECC 맞춤 → 눈·입 3점 아핀으로 원화 얼굴 자리 → 얼굴 피부 안만(코 표시 남김). 깜빡임(half·closed)은 **두 눈 자리만**(눈썹 원화 그대로)
- 회귀: 다른 리그 6종 대기·달리기·멈춤·모든 동작·뒤돌기 픽셀 해시 차이 0 (Math.random·시간 고정한 `_reg.html`)

## 다음
DHL v1(대기·달리기) 확인 → 내려찍기(동작 시트 2줄: 머리 위로 들기 → 내려찍기 → 런지 → 돌아오기) → 게임 연결(REGISTRY 11, gameRef 가운데, cutHold, game_check.py)
