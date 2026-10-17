#!/bin/bash
# 빌드 → 임시 패키지 → 관절 검사 + 추가 검사.  bash tools/check.sh
set -e
cd "$(dirname "$0")/.."; python3 -I build_neon.py >/dev/null
SP=/tmp/claude-0/-home-claude/68d7ec04-d283-5e5f-8529-136e76cd93e3/scratchpad/pkg18; rm -rf $SP; mkdir -p $SP; cp -r ../rig.json ../parts ../../rig.js $SP/
cd ../../tools; timeout 300 python3 audit_joints.py $SP 2>&1 | grep -v -i proxy | grep -v "^- \|^Allowed\|^For details" || true
timeout 300 python3 audit_extra.py $SP 2>&1 | grep -v -i proxy | grep -v "^- \|^Allowed\|^For details" || true
