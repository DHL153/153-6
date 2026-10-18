#!/bin/bash
# 빌드 → 임시 패키지 → 관절 검사 + 추가 검사.  bash tools/check.sh   (build_carden.py 는 조각 시트 받은 뒤 작성)
set -e
cd "$(dirname "$0")/.."; python3 -I build_carden.py >/dev/null
SP=/tmp/claude-0/-home-claude/68d7ec04-d283-5e5f-8529-136e76cd93e3/scratchpad/pkg16; rm -rf $SP; mkdir -p $SP; cp -r ../rig.json ../parts ../../rig.js $SP/
cd ../../tools; timeout 300 python3 audit_joints.py $SP 2>&1 | grep -v -i "agent-proxy" | grep -v "^- \|^Allowed\|^For details" || true
timeout 300 python3 audit_extra.py $SP 2>&1 | grep -v -i "agent-proxy" | grep -v "^- \|^Allowed\|^For details" || true
