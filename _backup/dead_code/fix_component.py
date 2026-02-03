#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# webcam_component.py 수정 스크립트

import os

path = os.path.join(os.path.dirname(__file__), "webcam_component.py")

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# critical 추가
if "critical" not in content:
    content = content.replace(
        '"high": "#ef4444"',
        '"critical": "#dc2626",\n        "high": "#ef4444"'
    )
    content = content.replace(
        '"high": "⚠️"',
        '"critical": "🚨",\n        "high": "⚠️"'
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Added critical priority")
else:
    print("Already has critical")
