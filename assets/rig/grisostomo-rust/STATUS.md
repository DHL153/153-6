# 5 러스트 그리소스토모 (grisostomo-rust) — 진행 기록 (계획·프롬프트: 프로젝트 문서 `claude/grisostomo5-rig-sheets.md`)

## 20:37 (10-21) 착수 — DHL 20:34 '같이 만들어 볼까요?' (첨부 = char_0005, md5 같음 → `source/refs/ref_dhl_2034.png` · `source/ref512.png`)
- 공격 = 두 주먹 내려찍기(DHL 20:35 고름 — 원투 펀치 · 두 주먹 내려찍기 · 어퍼컷 중)
- 러스트 세계라 원화 그대로가 기준 자세(새 원화 안 받음). 불투명 x 13–505 · y 37–480 · 발바닥 480(샌들 평평) · 몸 키 443 · 게임 칸 위 끝 추정 −322
- 두 팔 = 팔뚝까지 감싼 큰 쇠 건틀릿 — 보이는 팔은 가까운 어깨 살·먼 윗팔 살뿐(가까운 팔꿈치·손목은 추정, 지운 원화로 다시 잼)
- `source/tools/measure5.py` → `source/measure5.json` · `review/measure5.png` · `source/tools/guides5.py` → `refs/ref_W5_near_arm_gauntlet_remove.png` · `refs/ref_X5_far_arm_gauntlet_remove.png` · `refs/ref_B5_limb_guide.png`
- 프롬프트 1(조각 시트 21칸 — 머리·표정 6·깜빡임 2·상투·건틀릿 둘·윗팔 둘·다리 4·달리는 샌들 2) · 2(가까운 팔·건틀릿 지운 원화) · 3(먼 팔·건틀릿 지운 원화) — 한꺼번에 보냄

## 2026-10-21 20:53 — 프롬프트 2(가까운 팔·건틀릿 지운 원화) 통과
- sheets/nonear_2052.png · tools/check_remove5.py near → SIFT 배율 1.0000, 이동 (−0.01, 0.00)
- 지운 곳 밖 평균 차 0.047, 밖 바뀐 덩어리 = 건틀릿 왼아래 그림자 자리(28,355 44×33)·작은 점뿐 → 문제 없음, 떨어진 섬 없음
- 조끼 소매 구멍(어깨 자리 ≈ 143,220) 드러남 → 가까운 어깨 SH [152,218] 그대로 씀
- 남은 것: 프롬프트 1(21칸 부품 시트) · 프롬프트 3(먼 팔·건틀릿 지운 원화)
