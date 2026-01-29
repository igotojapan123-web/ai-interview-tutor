# ui_components.py
# FlyReady Lab - 프로페셔널 UI 컴포넌트 라이브러리
# 대기업 수준의 깔끔한 UI를 위한 재사용 가능한 컴포넌트

import streamlit as st
import streamlit.components.v1 as components

# ============================================
# SVG 아이콘 라이브러리 (Lucide 스타일)
# ============================================
ICONS = {
    # 네비게이션
    "home": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "menu": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>',

    # 면접/연습
    "mic": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>',
    "video": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 8-6 4 6 4V8Z"/><rect width="14" height="12" x="2" y="6" rx="2" ry="2"/></svg>',
    "users": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "message-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"/></svg>',
    "globe": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" x2="22" y1="12" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',

    # 문서/학습
    "file-text": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/></svg>',
    "book-open": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
    "graduation-cap": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>',
    "lightbulb": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>',

    # 분석/차트
    "bar-chart": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/></svg>',
    "trending-up": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
    "pie-chart": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>',

    # 상태/알림
    "check-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    "alert-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>',
    "info": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
    "x-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>',

    # 액션
    "play": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
    "pause": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="4" height="16" x="6" y="4"/><rect width="4" height="16" x="14" y="4"/></svg>',
    "refresh": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>',
    "download": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>',
    "upload": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>',
    "settings": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',

    # 기타
    "calendar": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>',
    "clock": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "star": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    "star-filled": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    "user": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "plane": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/></svg>',
    "building": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg>',
    "award": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/></svg>',
    "target": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "smile": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" x2="9.01" y1="9" y2="9"/><line x1="15" x2="15.01" y1="9" y2="9"/></svg>',
    "volume-2": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>',
    "image": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>',
    "help-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>',
    "bell": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
    "database": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/></svg>',
    "dumbbell": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6.5 6.5 11 11"/><path d="m21 21-1-1"/><path d="m3 3 1 1"/><path d="m18 22 4-4"/><path d="m2 6 4-4"/><path d="m3 10 7-7"/><path d="m14 21 7-7"/></svg>',
    "briefcase": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="7" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    "clipboard-list": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/></svg>',
    "arrow-right": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>',
    "arrow-left": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>',
    "chevron-right": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>',
    "chevron-down": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>',
    "x": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
    "check": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "plus": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>',
    "minus": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/></svg>',
    "search": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    "filter": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>',
    "edit": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
    "trash": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>',
    "external-link": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" x2="21" y1="14" y2="3"/></svg>',

    # 추가 아이콘 (이모지 대체용)
    "trophy": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></svg>',
    "medal": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="17" r="5"/><path d="M12 12V2"/></svg>',
    "fire": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>',
    "sparkles": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3Z"/></svg>',
    "zap": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "thumbs-up": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/></svg>',
    "heart": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>',
    "gift": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="8" width="18" height="4" rx="1"/><path d="M12 8v13"/><path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/></svg>',
    "pencil": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>',
    "clipboard": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>',
    "list": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" x2="21" y1="6" y2="6"/><line x1="8" x2="21" y1="12" y2="12"/><line x1="8" x2="21" y1="18" y2="18"/><line x1="3" x2="3.01" y1="6" y2="6"/><line x1="3" x2="3.01" y1="12" y2="12"/><line x1="3" x2="3.01" y1="18" y2="18"/></svg>',
    "book": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>',
    "camera": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>',
    "eye": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>',
    "shirt": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23Z"/></svg>',
    "activity": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
    "timer": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="10" x2="14" y1="2" y2="2"/><line x1="12" x2="15" y1="14" y2="11"/><circle cx="12" cy="14" r="8"/></svg>',
    "megaphone": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 11 18-5v12L3 13v-2z"/></svg>',
    "map-pin": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>',
    "flag": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" x2="4" y1="22" y2="15"/></svg>',
    "lock": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
}


def get_icon(name: str, size: int = 20, color: str = "currentColor") -> str:
    """SVG 아이콘 반환"""
    icon = ICONS.get(name, ICONS["help-circle"])
    if size != 20:
        icon = icon.replace('width="20"', f'width="{size}"').replace('height="20"', f'height="{size}"')
    if color != "currentColor":
        icon = icon.replace('stroke="currentColor"', f'stroke="{color}"')
    return icon


def icon_with_text(icon_name: str, text: str, size: int = 20, color: str = "#1e3a5f", gap: int = 8) -> str:
    """아이콘 + 텍스트 조합 HTML"""
    icon = get_icon(icon_name, size, color)
    return f'<span style="display:inline-flex;align-items:center;gap:{gap}px;color:{color}">{icon}<span>{text}</span></span>'


# ============================================
# 로딩 컴포넌트
# ============================================
def get_loading_css():
    """로딩 애니메이션 CSS"""
    return """
<style>
/* 스피너 로딩 */
.fr-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #e2e8f0;
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: fr-spin 0.8s linear infinite;
}
@keyframes fr-spin {
    to { transform: rotate(360deg); }
}

/* 도트 로딩 */
.fr-dots {
    display: flex;
    gap: 6px;
    justify-content: center;
    align-items: center;
}
.fr-dot {
    width: 10px;
    height: 10px;
    background: #3b82f6;
    border-radius: 50%;
    animation: fr-bounce 0.6s infinite alternate;
}
.fr-dot:nth-child(2) { animation-delay: 0.2s; }
.fr-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes fr-bounce {
    to { transform: translateY(-10px); opacity: 0.3; }
}

/* 스켈레톤 로딩 */
.fr-skeleton {
    background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
    background-size: 200% 100%;
    animation: fr-shimmer 1.5s infinite;
    border-radius: 8px;
}
@keyframes fr-shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
.fr-skeleton-text { height: 16px; margin-bottom: 8px; }
.fr-skeleton-title { height: 24px; width: 60%; margin-bottom: 12px; }
.fr-skeleton-card { height: 120px; }
.fr-skeleton-avatar { width: 48px; height: 48px; border-radius: 50%; }

/* 프로그레스 바 */
.fr-progress-animate {
    height: 4px;
    background: #e2e8f0;
    border-radius: 2px;
    overflow: hidden;
}
.fr-progress-bar-animate {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #60a5fa, #3b82f6);
    background-size: 200% 100%;
    animation: fr-progress 1s infinite linear;
    border-radius: 2px;
}
@keyframes fr-progress {
    0% { background-position: 100% 0; }
    100% { background-position: -100% 0; }
}

/* 펄스 효과 */
.fr-pulse {
    animation: fr-pulse 2s infinite;
}
@keyframes fr-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
</style>
"""


def render_spinner(text: str = "로딩 중..."):
    """스피너 로딩 표시"""
    st.markdown(get_loading_css(), unsafe_allow_html=True)
    st.markdown(f'''
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px;gap:16px;">
        <div class="fr-spinner"></div>
        <div style="color:#64748b;font-size:0.9rem;">{text}</div>
    </div>
    ''', unsafe_allow_html=True)


def render_dots_loading(text: str = "처리 중..."):
    """도트 로딩 표시"""
    st.markdown(get_loading_css(), unsafe_allow_html=True)
    st.markdown(f'''
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:30px;gap:12px;">
        <div class="fr-dots">
            <div class="fr-dot"></div>
            <div class="fr-dot"></div>
            <div class="fr-dot"></div>
        </div>
        <div style="color:#64748b;font-size:0.85rem;">{text}</div>
    </div>
    ''', unsafe_allow_html=True)


def render_skeleton_cards(count: int = 3):
    """스켈레톤 카드 로딩"""
    st.markdown(get_loading_css(), unsafe_allow_html=True)
    cards_html = ""
    for _ in range(count):
        cards_html += '''
        <div style="background:white;border-radius:12px;padding:20px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
            <div class="fr-skeleton fr-skeleton-title"></div>
            <div class="fr-skeleton fr-skeleton-text" style="width:80%"></div>
            <div class="fr-skeleton fr-skeleton-text" style="width:60%"></div>
        </div>
        '''
    st.markdown(f'<div style="padding:16px;">{cards_html}</div>', unsafe_allow_html=True)


def render_progress_loading():
    """프로그레스 바 로딩"""
    st.markdown(get_loading_css(), unsafe_allow_html=True)
    st.markdown('''
    <div class="fr-progress-animate">
        <div class="fr-progress-bar-animate" style="width:100%"></div>
    </div>
    ''', unsafe_allow_html=True)


# ============================================
# 빈 상태 컴포넌트
# ============================================
def get_empty_state_illustration(type: str = "default") -> str:
    """빈 상태 일러스트레이션 SVG"""
    illustrations = {
        "default": '''<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="60" cy="60" r="50" fill="#f1f5f9"/>
            <rect x="35" y="40" width="50" height="40" rx="4" fill="#e2e8f0"/>
            <rect x="40" y="50" width="30" height="4" rx="2" fill="#cbd5e1"/>
            <rect x="40" y="58" width="40" height="4" rx="2" fill="#cbd5e1"/>
            <rect x="40" y="66" width="25" height="4" rx="2" fill="#cbd5e1"/>
        </svg>''',
        "search": '''<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="60" cy="60" r="50" fill="#f1f5f9"/>
            <circle cx="52" cy="52" r="20" stroke="#cbd5e1" stroke-width="4" fill="none"/>
            <line x1="66" y1="66" x2="80" y2="80" stroke="#cbd5e1" stroke-width="4" stroke-linecap="round"/>
        </svg>''',
        "calendar": '''<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="60" cy="60" r="50" fill="#f1f5f9"/>
            <rect x="30" y="35" width="60" height="50" rx="4" fill="#e2e8f0"/>
            <rect x="30" y="35" width="60" height="15" rx="4" fill="#cbd5e1"/>
            <circle cx="42" cy="42" r="3" fill="#94a3b8"/>
            <circle cx="60" cy="42" r="3" fill="#94a3b8"/>
            <circle cx="78" cy="42" r="3" fill="#94a3b8"/>
        </svg>''',
        "chart": '''<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="60" cy="60" r="50" fill="#f1f5f9"/>
            <rect x="35" y="70" width="12" height="20" rx="2" fill="#cbd5e1"/>
            <rect x="54" y="55" width="12" height="35" rx="2" fill="#94a3b8"/>
            <rect x="73" y="40" width="12" height="50" rx="2" fill="#64748b"/>
        </svg>''',
        "mic": '''<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="60" cy="60" r="50" fill="#f1f5f9"/>
            <rect x="50" y="35" width="20" height="35" rx="10" fill="#e2e8f0"/>
            <path d="M40 55v5a20 20 0 0040 0v-5" stroke="#cbd5e1" stroke-width="4" fill="none"/>
            <line x1="60" y1="80" x2="60" y2="90" stroke="#cbd5e1" stroke-width="4"/>
        </svg>''',
        "success": '''<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="60" cy="60" r="50" fill="#dcfce7"/>
            <circle cx="60" cy="60" r="30" fill="#86efac"/>
            <polyline points="45,60 55,70 75,50" stroke="white" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
    }
    return illustrations.get(type, illustrations["default"])


def render_empty_state(
    title: str = "데이터가 없습니다",
    description: str = "",
    illustration: str = "default",
    action_text: str = "",
    action_link: str = ""
):
    """빈 상태 화면 렌더링"""
    illust_svg = get_empty_state_illustration(illustration)

    action_html = ""
    if action_text and action_link:
        action_html = f'''
        <a href="{action_link}" style="display:inline-block;margin-top:16px;padding:10px 24px;background:#3b82f6;color:white;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.9rem;transition:all 0.2s;">
            {action_text}
        </a>
        '''

    desc_html = f'<p style="color:#94a3b8;font-size:0.9rem;margin:8px 0 0 0;line-height:1.5;">{description}</p>' if description else ''

    st.markdown(f'''
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:48px 24px;text-align:center;">
        <div style="margin-bottom:20px;">{illust_svg}</div>
        <h3 style="color:#334155;font-size:1.1rem;font-weight:600;margin:0;">{title}</h3>
        {desc_html}
        {action_html}
    </div>
    ''', unsafe_allow_html=True)


# ============================================
# 토스트 알림 시스템
# ============================================
def get_toast_css():
    """토스트 알림 CSS"""
    return """
<style>
.fr-toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.fr-toast {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 20px;
    border-radius: 10px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    animation: fr-toast-in 0.3s ease-out;
    max-width: 360px;
}
@keyframes fr-toast-in {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
.fr-toast-success {
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
}
.fr-toast-error {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: white;
}
.fr-toast-warning {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: white;
}
.fr-toast-info {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
}
.fr-toast-icon {
    flex-shrink: 0;
}
.fr-toast-content {
    flex: 1;
}
.fr-toast-title {
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 2px;
}
.fr-toast-message {
    font-size: 0.8rem;
    opacity: 0.9;
}
.fr-toast-close {
    cursor: pointer;
    opacity: 0.7;
    transition: opacity 0.2s;
}
.fr-toast-close:hover {
    opacity: 1;
}
</style>
"""


def show_toast(message: str, type: str = "info", title: str = "", duration: int = 4000):
    """토스트 알림 표시 (JavaScript 기반 자동 사라짐)"""
    icons = {
        "success": get_icon("check-circle", 24, "white"),
        "error": get_icon("x-circle", 24, "white"),
        "warning": get_icon("alert-circle", 24, "white"),
        "info": get_icon("info", 24, "white"),
    }
    icon = icons.get(type, icons["info"])

    title_html = f'<div class="fr-toast-title">{title}</div>' if title else ''

    toast_html = f'''
    {get_toast_css()}
    <div id="fr-toast-{hash(message)}" class="fr-toast fr-toast-{type}" style="position:fixed;top:20px;right:20px;z-index:9999;">
        <div class="fr-toast-icon">{icon}</div>
        <div class="fr-toast-content">
            {title_html}
            <div class="fr-toast-message">{message}</div>
        </div>
        <div class="fr-toast-close" onclick="this.parentElement.remove()">{get_icon("x", 18, "white")}</div>
    </div>
    <script>
        setTimeout(function() {{
            var toast = document.getElementById('fr-toast-{hash(message)}');
            if (toast) {{
                toast.style.animation = 'fr-toast-out 0.3s ease-in forwards';
                setTimeout(function() {{ toast.remove(); }}, 300);
            }}
        }}, {duration});
    </script>
    <style>
        @keyframes fr-toast-out {{
            to {{ transform: translateX(100%); opacity: 0; }}
        }}
    </style>
    '''
    components.html(toast_html, height=0)


# ============================================
# 마이크로 인터랙션 CSS
# ============================================
def get_interaction_css():
    """마이크로 인터랙션 CSS"""
    return """
<style>
/* 버튼 호버/클릭 효과 */
.stButton > button {
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* 카드 호버 효과 */
.fr-hover-lift {
    transition: all 0.2s ease;
}
.fr-hover-lift:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

/* 링크 밑줄 애니메이션 */
.fr-link-underline {
    position: relative;
    text-decoration: none;
}
.fr-link-underline::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    width: 0;
    height: 2px;
    background: #3b82f6;
    transition: width 0.3s ease;
}
.fr-link-underline:hover::after {
    width: 100%;
}

/* 페이드 인 애니메이션 */
.fr-fade-in {
    animation: fr-fade-in 0.5s ease-out;
}
@keyframes fr-fade-in {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* 슬라이드 인 애니메이션 */
.fr-slide-in-left {
    animation: fr-slide-in-left 0.4s ease-out;
}
@keyframes fr-slide-in-left {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

.fr-slide-in-right {
    animation: fr-slide-in-right 0.4s ease-out;
}
@keyframes fr-slide-in-right {
    from { opacity: 0; transform: translateX(20px); }
    to { opacity: 1; transform: translateX(0); }
}

/* 스케일 인 애니메이션 */
.fr-scale-in {
    animation: fr-scale-in 0.3s ease-out;
}
@keyframes fr-scale-in {
    from { opacity: 0; transform: scale(0.9); }
    to { opacity: 1; transform: scale(1); }
}

/* 포커스 링 */
.fr-focus-ring:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
}

/* 체크박스/라디오 애니메이션 */
.stCheckbox label span, .stRadio label span {
    transition: all 0.2s ease;
}

/* 입력 필드 포커스 */
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

/* 셀렉트박스 호버 */
.stSelectbox > div > div:hover {
    border-color: #3b82f6 !important;
}

/* 탭 전환 애니메이션 */
.stTabs [data-baseweb="tab-panel"] {
    animation: fr-fade-in 0.3s ease-out;
}

/* 익스팬더 애니메이션 */
.streamlit-expanderHeader:hover {
    background: #f8fafc !important;
}
.streamlit-expanderContent {
    animation: fr-fade-in 0.2s ease-out;
}

/* 메트릭 카드 호버 */
[data-testid="stMetricValue"] {
    transition: all 0.2s ease;
}
[data-testid="metric-container"]:hover [data-testid="stMetricValue"] {
    color: #3b82f6 !important;
}

/* 프로그레스 바 애니메이션 */
.stProgress > div > div > div {
    transition: width 0.5s ease !important;
}

/* 성공/에러/경고/정보 알림 애니메이션 */
.stAlert {
    animation: fr-slide-in-left 0.3s ease-out;
}
</style>
"""


def apply_interaction_css():
    """마이크로 인터랙션 CSS 적용"""
    st.markdown(get_interaction_css(), unsafe_allow_html=True)


# ============================================
# 유틸리티 함수
# ============================================
def render_page_header(title: str, subtitle: str = "", icon_name: str = ""):
    """페이지 헤더 렌더링"""
    icon_html = ""
    if icon_name:
        icon_html = f'<span style="margin-right:12px;display:inline-flex;vertical-align:middle;">{get_icon(icon_name, 28, "#1e3a5f")}</span>'

    subtitle_html = f'<p style="color:#64748b;font-size:0.95rem;margin:8px 0 0 0;">{subtitle}</p>' if subtitle else ''

    st.markdown(f'''
    <div style="margin-bottom:24px;" class="fr-fade-in">
        <h1 style="color:#1e3a5f;font-size:1.75rem;font-weight:800;margin:0;display:flex;align-items:center;">
            {icon_html}{title}
        </h1>
        {subtitle_html}
    </div>
    ''', unsafe_allow_html=True)


def render_section_header(title: str, icon_name: str = ""):
    """섹션 헤더 렌더링"""
    icon_html = ""
    if icon_name:
        icon_html = f'<span style="margin-right:8px;display:inline-flex;">{get_icon(icon_name, 20, "#3b82f6")}</span>'

    st.markdown(f'''
    <div style="display:flex;align-items:center;margin:24px 0 16px 0;padding-bottom:8px;border-bottom:2px solid #e2e8f0;">
        {icon_html}
        <span style="font-size:1.1rem;font-weight:700;color:#1e3a5f;">{title}</span>
    </div>
    ''', unsafe_allow_html=True)


def render_stat_card(value: str, label: str, icon_name: str = "", trend: str = "", trend_positive: bool = True):
    """통계 카드 렌더링"""
    icon_html = ""
    if icon_name:
        icon_html = f'<div style="margin-bottom:8px;">{get_icon(icon_name, 24, "#64748b")}</div>'

    trend_html = ""
    if trend:
        trend_color = "#10b981" if trend_positive else "#ef4444"
        trend_icon = get_icon("trending-up" if trend_positive else "trending-down", 16, trend_color)
        trend_html = f'<div style="display:flex;align-items:center;gap:4px;color:{trend_color};font-size:0.8rem;margin-top:4px;">{trend_icon}{trend}</div>'

    st.markdown(f'''
    <div class="fr-hover-lift" style="background:white;border-radius:12px;padding:20px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.04);border:1px solid #e2e8f0;">
        {icon_html}
        <div style="font-size:1.75rem;font-weight:800;color:#1e3a5f;">{value}</div>
        <div style="font-size:0.8rem;color:#64748b;font-weight:500;">{label}</div>
        {trend_html}
    </div>
    ''', unsafe_allow_html=True)


def render_info_banner(message: str, type: str = "info", icon_name: str = ""):
    """정보 배너 렌더링"""
    colors = {
        "info": {"bg": "#eff6ff", "border": "#3b82f6", "text": "#1e40af"},
        "success": {"bg": "#f0fdf4", "border": "#10b981", "text": "#166534"},
        "warning": {"bg": "#fffbeb", "border": "#f59e0b", "text": "#92400e"},
        "error": {"bg": "#fef2f2", "border": "#ef4444", "text": "#991b1b"},
    }
    c = colors.get(type, colors["info"])

    default_icons = {"info": "info", "success": "check-circle", "warning": "alert-circle", "error": "x-circle"}
    icon = icon_name or default_icons.get(type, "info")

    st.markdown(f'''
    <div class="fr-fade-in" style="display:flex;align-items:flex-start;gap:12px;padding:16px 20px;background:{c["bg"]};border-left:4px solid {c["border"]};border-radius:8px;margin:12px 0;">
        <div style="flex-shrink:0;color:{c["border"]};">{get_icon(icon, 20, c["border"])}</div>
        <div style="color:{c["text"]};font-size:0.9rem;line-height:1.5;">{message}</div>
    </div>
    ''', unsafe_allow_html=True)


def render_difficulty_stars(level: int, max_level: int = 4):
    """난이도 별 표시"""
    stars_html = ""
    for i in range(max_level):
        if i < level:
            stars_html += get_icon("star-filled", 16, "#f59e0b")
        else:
            stars_html += get_icon("star", 16, "#e2e8f0")
    return f'<span style="display:inline-flex;gap:2px;">{stars_html}</span>'
