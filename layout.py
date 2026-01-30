# layout.py
# FlyReady Lab - Enterprise-grade Layout System
# Modern, clean UI inspired by Linear, Notion, Vercel

import streamlit as st
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass

# ============================================
# Design Tokens - Premium Enterprise Design System
# ============================================
THEME = {
    # Colors - Refined palette inspired by Linear/Vercel
    "primary": "#0F172A",      # Slate 900 - primary text
    "secondary": "#475569",    # Slate 600 - secondary text
    "muted": "#94A3B8",        # Slate 400 - muted text
    "accent": "#2563EB",       # Blue 600 - accent/links
    "accent_light": "#3B82F6", # Blue 500 - hover
    "accent_dark": "#1D4ED8",  # Blue 700 - active
    "success": "#059669",      # Emerald 600
    "success_light": "#10B981",# Emerald 500
    "warning": "#D97706",      # Amber 600
    "error": "#DC2626",        # Red 600
    "background": "#FFFFFF",   # White
    "surface": "#F8FAFC",      # Slate 50
    "surface_hover": "#F1F5F9",# Slate 100
    "border": "#E2E8F0",       # Slate 200
    "border_dark": "#CBD5E1",  # Slate 300

    # Premium gradients
    "gradient_hero": "linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #334155 100%)",
    "gradient_accent": "linear-gradient(135deg, #2563EB 0%, #3B82F6 100%)",
    "gradient_card": "linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)",

    # Typography
    "font": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "font_display": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",

    # Spacing
    "radius_sm": "6px",
    "radius_md": "8px",
    "radius_lg": "12px",
    "radius_xl": "16px",
    "radius_2xl": "20px",

    # Shadows - Premium depth
    "shadow_sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    "shadow_md": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    "shadow_lg": "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    "shadow_xl": "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
    "shadow_glow": "0 0 40px -10px rgba(37, 99, 235, 0.3)",
    "shadow_card": "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
    "shadow_card_hover": "0 10px 40px -10px rgb(0 0 0 / 0.15)",
}


# ============================================
# Navigation Structure
# ============================================
@dataclass
class NavItem:
    label: str
    page: str
    icon: str = ""
    badge: str = ""


NAV_SECTIONS = {
    "practice": {
        "label": "면접 연습",
        "icon": "mic",
        "items": [
            NavItem("AI 모의면접", "모의면접", "video"),
            NavItem("기내 롤플레잉", "롤플레잉", "message-circle"),
            NavItem("영어 면접", "영어면접", "globe"),
            NavItem("토론 면접", "토론면접", "users"),
        ]
    },
    "tools": {
        "label": "준비 도구",
        "icon": "briefcase",
        "items": [
            NavItem("자소서 첨삭", "자소서첨삭", "file-text"),
            NavItem("실전 연습", "실전연습", "camera"),
            NavItem("이미지메이킹", "이미지메이킹", "shirt"),
            NavItem("기내방송", "기내방송연습", "volume-2"),
        ]
    },
    "learn": {
        "label": "학습",
        "icon": "book-open",
        "items": [
            NavItem("항공 상식 퀴즈", "항공사퀴즈", "help-circle"),
            NavItem("면접 꿀팁", "면접꿀팁", "lightbulb"),
            NavItem("항공사 가이드", "항공사가이드", "plane"),
            NavItem("국민체력/수영", "국민체력", "dumbbell"),
            NavItem("기업 분석", "기업분석", "building"),
        ]
    },
    "manage": {
        "label": "관리",
        "icon": "bar-chart",
        "items": [
            NavItem("진도 관리", "진도관리", "clipboard-list"),
            NavItem("성장 그래프", "성장그래프", "trending-up"),
            NavItem("채용 정보", "채용정보", "briefcase"),
            NavItem("합격자 DB", "합격자DB", "database"),
            NavItem("D-Day 캘린더", "D-Day캘린더", "calendar"),
        ]
    }
}


# ============================================
# Base CSS
# ============================================
def get_global_css() -> str:
    """Enterprise-grade global CSS"""
    return f"""
<style>
/* Font Import */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Reset & Base */
* {{
    font-family: {THEME['font']};
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}}

/* Hide Streamlit Elements */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}
[data-testid="stHeader"] {{display: none;}}
[data-testid="stToolbar"] {{display: none;}}
[data-testid="stDecoration"] {{display: none;}}
[data-testid="stSidebar"] {{display: none !important;}}
[data-testid="stSidebarNav"] {{display: none !important;}}
[data-testid="collapsedControl"] {{display: none !important;}}
section[data-testid="stSidebar"] {{display: none !important;}}

/* Main Container */
.main .block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}

.stApp {{
    background: {THEME['background']};
}}

/* Top Navigation Bar - Glassmorphism */
.nav-top {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 64px;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border-bottom: 1px solid rgba(226, 232, 240, 0.8);
    display: flex;
    align-items: center;
    padding: 0 32px;
    z-index: 1000;
    gap: 40px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}

.nav-top.scrolled {{
    height: 56px;
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.05);
}}

.nav-logo {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 700;
    font-size: 18px;
    color: {THEME['primary']};
    text-decoration: none;
}}

.nav-logo img {{
    height: 28px;
}}

.nav-links {{
    display: flex;
    align-items: center;
    gap: 4px;
    flex: 1;
}}

.nav-link {{
    position: relative;
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 500;
    color: {THEME['secondary']};
    text-decoration: none;
    border-radius: {THEME['radius_lg']};
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
}}

.nav-link:hover {{
    color: {THEME['primary']};
    background: {THEME['surface']};
}}

.nav-link.active {{
    color: {THEME['accent']};
    background: rgba(37, 99, 235, 0.1);
}}

.nav-link svg {{
    transition: transform 0.2s ease;
}}

.nav-link:hover svg {{
    transform: rotate(180deg);
}}

.nav-dropdown {{
    position: absolute;
    top: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%) translateY(10px);
    min-width: 240px;
    background: rgba(255, 255, 255, 0.98);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid {THEME['border']};
    border-radius: {THEME['radius_xl']};
    box-shadow: 0 20px 50px -12px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05);
    padding: 8px;
    opacity: 0;
    visibility: hidden;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 1001;
}}

.nav-dropdown::before {{
    content: '';
    position: absolute;
    top: -6px;
    left: 50%;
    transform: translateX(-50%) rotate(45deg);
    width: 12px;
    height: 12px;
    background: white;
    border-left: 1px solid {THEME['border']};
    border-top: 1px solid {THEME['border']};
}}

.nav-link:hover .nav-dropdown {{
    opacity: 1;
    visibility: visible;
    transform: translateX(-50%) translateY(0);
}}

.nav-dropdown-item {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    font-size: 14px;
    font-weight: 500;
    color: {THEME['secondary']};
    text-decoration: none;
    border-radius: {THEME['radius_md']};
    transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}}

.nav-dropdown-item:hover {{
    background: {THEME['surface']};
    color: {THEME['accent']};
    transform: translateX(4px);
}}

.nav-dropdown-item.active {{
    background: rgba(37, 99, 235, 0.1);
    color: {THEME['accent']};
}}

.nav-dropdown-item svg {{
    color: {THEME['muted']};
    transition: color 0.15s ease;
}}

.nav-dropdown-item:hover svg {{
    color: {THEME['accent']};
}}

.nav-dropdown-item:hover svg {{
    color: {THEME['accent']};
}}

.nav-right {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.nav-btn {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 600;
    border-radius: {THEME['radius_lg']};
    text-decoration: none;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
}}

.nav-btn-ghost {{
    color: {THEME['secondary']};
    background: transparent;
}}

.nav-btn-ghost:hover {{
    color: {THEME['primary']};
    background: {THEME['surface']};
}}

.nav-btn-primary {{
    background: {THEME['gradient_accent']};
    color: white;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
}}

.nav-btn-primary:hover {{
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.35);
}}

.nav-btn-primary:active {{
    transform: translateY(0);
}}

/* Page Content Area */
.page-content {{
    margin-top: 64px;
    min-height: calc(100vh - 64px);
}}

/* Page Header - Premium style */
.page-header {{
    padding: 40px 64px 32px;
    background: linear-gradient(180deg, {THEME['surface']} 0%, {THEME['background']} 100%);
    border-bottom: 1px solid {THEME['border']};
}}

.page-header-inner {{
    max-width: 1200px;
    margin: 0 auto;
}}

.page-breadcrumb {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: {THEME['muted']};
    margin-bottom: 12px;
}}

.page-breadcrumb a {{
    color: {THEME['muted']};
    text-decoration: none;
}}

.page-breadcrumb a:hover {{
    color: {THEME['accent']};
}}

.page-title {{
    font-size: 32px;
    font-weight: 700;
    color: {THEME['primary']};
    margin: 0 0 8px 0;
    letter-spacing: -0.02em;
}}

.page-description {{
    font-size: 16px;
    color: {THEME['secondary']};
    margin: 0;
    line-height: 1.5;
}}

/* Page Body */
.page-body {{
    padding: 32px 64px;
    max-width: 1200px;
    margin: 0 auto;
}}

/* Card Component - Premium */
.card {{
    position: relative;
    background: {THEME['background']};
    border: 1px solid {THEME['border']};
    border-radius: {THEME['radius_xl']};
    padding: 28px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}

.card:hover {{
    border-color: {THEME['border_dark']};
    box-shadow: 0 12px 40px -12px rgba(0, 0, 0, 0.12);
    transform: translateY(-2px);
}}

.card-clickable {{
    cursor: pointer;
}}

.card-clickable:hover {{
    border-color: {THEME['accent']};
}}

/* Grid Layout - Responsive */
.grid {{
    display: grid;
    gap: 24px;
}}

.grid-2 {{
    grid-template-columns: repeat(2, 1fr);
}}

.grid-3 {{
    grid-template-columns: repeat(3, 1fr);
}}

.grid-4 {{
    grid-template-columns: repeat(4, 1fr);
}}

@media (max-width: 1200px) {{
    .grid-4 {{ grid-template-columns: repeat(3, 1fr); }}
}}

@media (max-width: 1024px) {{
    .grid-4 {{ grid-template-columns: repeat(2, 1fr); }}
    .grid-3 {{ grid-template-columns: repeat(2, 1fr); }}
    .hero {{ padding: 80px 40px; }}
    .hero-title {{ font-size: 42px; }}
}}

@media (max-width: 768px) {{
    .grid-4, .grid-3, .grid-2 {{ grid-template-columns: 1fr; }}
    .page-header {{ padding: 32px 24px 24px; }}
    .page-body {{ padding: 24px; }}
    .nav-top {{ padding: 0 16px; }}
    .hero {{ padding: 60px 24px; }}
    .hero-title {{ font-size: 32px; }}
    .hero-subtitle {{ font-size: 16px; }}
    .hero-actions {{ flex-direction: column; }}
    .hero-btn {{ width: 100%; justify-content: center; }}
    .section {{ padding: 40px 24px; }}
}}

/* Stat Card - Premium */
.stat-card {{
    position: relative;
    padding: 24px;
    overflow: hidden;
    background: {THEME['surface']};
    border-radius: {THEME['radius_lg']};
}}

.stat-value {{
    font-size: 32px;
    font-weight: 800;
    color: {THEME['primary']};
    line-height: 1.1;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, {THEME['primary']} 0%, {THEME['secondary']} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.stat-label {{
    font-size: 13px;
    font-weight: 500;
    color: {THEME['secondary']};
    margin-top: 6px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}}

.stat-trend {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    font-weight: 600;
    margin-top: 10px;
    padding: 4px 10px;
    border-radius: 9999px;
}}

.stat-trend-up {{
    color: {THEME['success']};
    background: rgba(5, 150, 105, 0.12);
}}

.stat-trend-down {{
    color: {THEME['error']};
    background: rgba(220, 38, 38, 0.12);
}}

/* Feature Card - Premium */
.feature-card {{
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 28px;
    background: {THEME['background']};
    border: 1px solid {THEME['border']};
    border-radius: {THEME['radius_xl']};
    text-decoration: none;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
}}

.feature-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: {THEME['gradient_accent']};
    opacity: 0;
    transition: opacity 0.3s ease;
}}

.feature-card:hover {{
    border-color: transparent;
    transform: translateY(-4px);
    box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.12);
}}

.feature-card:hover::before {{
    opacity: 1;
}}

.feature-icon {{
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(59, 130, 246, 0.15) 100%);
    border-radius: {THEME['radius_lg']};
    color: {THEME['accent']};
    transition: all 0.3s ease;
}}

.feature-card:hover .feature-icon {{
    transform: scale(1.05);
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.15) 0%, rgba(59, 130, 246, 0.2) 100%);
}}

.feature-title {{
    font-size: 17px;
    font-weight: 600;
    color: {THEME['primary']};
    letter-spacing: -0.01em;
}}

.feature-desc {{
    font-size: 14px;
    color: {THEME['secondary']};
    line-height: 1.6;
}}

/* Button Styles - Premium */
.btn {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 600;
    border-radius: {THEME['radius_lg']};
    text-decoration: none;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    border: none;
    position: relative;
    overflow: hidden;
}}

.btn::after {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(255,255,255,0.1) 0%, transparent 100%);
    opacity: 0;
    transition: opacity 0.2s ease;
}}

.btn:hover::after {{
    opacity: 1;
}}

.btn-primary {{
    background: {THEME['gradient_accent']};
    color: white;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25);
}}

.btn-primary:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(37, 99, 235, 0.35);
}}

.btn-primary:active {{
    transform: translateY(0);
}}

.btn-primary:hover {{
    background: #1D4ED8;
}}

.btn-secondary {{
    background: {THEME['surface']};
    color: {THEME['primary']};
    border: 1px solid {THEME['border']};
}}

.btn-secondary:hover {{
    background: {THEME['border']};
}}

.btn-lg {{
    padding: 14px 28px;
    font-size: 16px;
}}

/* Badge */
.badge {{
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 500;
    border-radius: 9999px;
}}

.badge-blue {{
    background: rgba(37, 99, 235, 0.1);
    color: {THEME['accent']};
}}

.badge-green {{
    background: rgba(5, 150, 105, 0.1);
    color: {THEME['success']};
}}

.badge-amber {{
    background: rgba(217, 119, 6, 0.1);
    color: {THEME['warning']};
}}

.badge-red {{
    background: rgba(220, 38, 38, 0.1);
    color: {THEME['error']};
}}

/* Hero Section - Premium with animated gradient */
.hero {{
    position: relative;
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
    background-size: 200% 200%;
    animation: heroGradient 15s ease infinite;
    padding: 100px 64px;
    color: white;
    overflow: hidden;
}}

.hero::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(ellipse at 30% 20%, rgba(37, 99, 235, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 70% 80%, rgba(59, 130, 246, 0.1) 0%, transparent 50%);
    pointer-events: none;
}}

@keyframes heroGradient {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}

.hero-inner {{
    position: relative;
    max-width: 1200px;
    margin: 0 auto;
    z-index: 1;
}}

.hero-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 9999px;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 24px;
    animation: fadeInUp 0.6s ease;
}}

.hero-title {{
    font-size: 56px;
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -0.03em;
    margin: 0 0 20px 0;
    animation: fadeInUp 0.6s ease 0.1s both;
}}

.hero-subtitle {{
    font-size: 20px;
    color: rgba(255, 255, 255, 0.75);
    margin: 0 0 40px 0;
    max-width: 600px;
    line-height: 1.6;
    animation: fadeInUp 0.6s ease 0.2s both;
}}

.hero-actions {{
    display: flex;
    gap: 16px;
    animation: fadeInUp 0.6s ease 0.3s both;
}}

@keyframes fadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(20px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.hero-btn {{
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 16px 32px;
    font-size: 16px;
    font-weight: 600;
    border-radius: {THEME['radius_lg']};
    text-decoration: none;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}}

.hero-btn-primary {{
    background: white;
    color: {THEME['primary']};
}}

.hero-btn-primary:hover {{
    background: {THEME['surface']};
    transform: translateY(-1px);
}}

.hero-btn-secondary {{
    background: rgba(255, 255, 255, 0.1) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.2);
}}

.hero-btn-secondary:hover {{
    background: rgba(255, 255, 255, 0.15) !important;
    color: #FFFFFF !important;
}}

/* Page Header */
.page-header {{
    padding: 32px 64px;
    background: {THEME['background']};
    border-bottom: 1px solid {THEME['border']};
}}

.page-header-inner {{
    max-width: 1200px;
    margin: 0 auto;
}}

.page-breadcrumb {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: {THEME['muted']};
    margin-bottom: 12px;
}}

.page-breadcrumb a {{
    color: {THEME['secondary']};
    text-decoration: none;
}}

.page-breadcrumb a:hover {{
    color: {THEME['accent']};
}}

.page-breadcrumb span {{
    color: {THEME['muted']};
}}

.page-title {{
    font-size: 28px;
    font-weight: 700;
    color: {THEME['primary']};
    margin: 0;
    letter-spacing: -0.01em;
}}

.page-description {{
    font-size: 15px;
    color: {THEME['secondary']};
    margin: 8px 0 0 0;
    max-width: 600px;
}}

/* Page Body */
.page-body {{
    padding: 32px 64px;
    max-width: 1200px;
    margin: 0 auto;
}}

/* Section */
.section {{
    padding: 64px;
    max-width: 1200px;
    margin: 0 auto;
}}

.section-header {{
    margin-bottom: 32px;
}}

.section-label {{
    font-size: 13px;
    font-weight: 600;
    color: {THEME['accent']};
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
}}

.section-title {{
    font-size: 24px;
    font-weight: 700;
    color: {THEME['primary']};
    margin: 0;
}}

/* Empty State */
.empty-state {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 64px 24px;
    text-align: center;
}}

.empty-state-icon {{
    width: 64px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: {THEME['surface']};
    border-radius: 50%;
    color: {THEME['muted']};
    margin-bottom: 20px;
}}

.empty-state-title {{
    font-size: 18px;
    font-weight: 600;
    color: {THEME['primary']};
    margin: 0 0 8px 0;
}}

.empty-state-desc {{
    font-size: 14px;
    color: {THEME['secondary']};
    margin: 0 0 24px 0;
}}

/* Divider */
.divider {{
    height: 1px;
    background: {THEME['border']};
    margin: 24px 0;
}}

/* Quick Actions Bar */
.quick-actions {{
    display: flex;
    gap: 12px;
    padding: 16px 64px;
    background: {THEME['surface']};
    border-bottom: 1px solid {THEME['border']};
    overflow-x: auto;
}}

.quick-action {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: {THEME['background']};
    border: 1px solid {THEME['border']};
    border-radius: {THEME['radius_md']};
    font-size: 14px;
    font-weight: 500;
    color: {THEME['secondary']};
    text-decoration: none;
    white-space: nowrap;
    transition: all 0.15s ease;
}}

.quick-action:hover {{
    border-color: {THEME['accent']};
    color: {THEME['accent']};
}}

.quick-action svg {{
    color: {THEME['muted']};
}}

.quick-action:hover svg {{
    color: {THEME['accent']};
}}

/* Footer - Premium */
.footer {{
    padding: 64px;
    background: linear-gradient(180deg, {THEME['surface']} 0%, #F1F5F9 100%);
    border-top: 1px solid {THEME['border']};
}}

.footer-inner {{
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 24px;
}}

.footer-brand {{
    font-size: 18px;
    font-weight: 700;
    color: {THEME['primary']};
}}

.footer-tagline {{
    font-size: 13px;
    color: {THEME['muted']};
    margin-top: 4px;
}}

.footer-links {{
    display: flex;
    gap: 32px;
}}

.footer-link {{
    font-size: 14px;
    font-weight: 500;
    color: {THEME['secondary']};
    text-decoration: none;
    transition: color 0.2s ease;
}}

.footer-link:hover {{
    color: {THEME['accent']};
}}

.footer-copy {{
    font-size: 13px;
    color: {THEME['muted']};
}}

/* Streamlit Overrides */
.stButton > button {{
    font-family: {THEME['font']} !important;
    font-weight: 500 !important;
    border-radius: {THEME['radius_md']} !important;
    border: 1px solid {THEME['border']} !important;
    transition: all 0.15s ease !important;
}}

.stButton > button:hover {{
    border-color: {THEME['accent']} !important;
    color: {THEME['accent']} !important;
}}

.stButton > button[kind="primary"] {{
    background: {THEME['accent']} !important;
    border-color: {THEME['accent']} !important;
    color: white !important;
}}

.stButton > button[kind="primary"]:hover {{
    background: #1D4ED8 !important;
    border-color: #1D4ED8 !important;
}}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{
    font-family: {THEME['font']} !important;
    border-radius: {THEME['radius_md']} !important;
    border-color: {THEME['border']} !important;
}}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color: {THEME['accent']} !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
}}

.stSelectbox > div > div {{
    border-radius: {THEME['radius_md']} !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    border-bottom: 1px solid {THEME['border']};
}}

.stTabs [data-baseweb="tab"] {{
    font-family: {THEME['font']} !important;
    font-weight: 500;
    padding: 12px 20px;
    color: {THEME['secondary']};
}}

.stTabs [data-baseweb="tab"]:hover {{
    color: {THEME['primary']};
}}

.stTabs [aria-selected="true"] {{
    color: {THEME['accent']} !important;
    border-bottom: 2px solid {THEME['accent']} !important;
}}

.stExpander {{
    border: 1px solid {THEME['border']} !important;
    border-radius: {THEME['radius_lg']} !important;
}}

.stAlert {{
    border-radius: {THEME['radius_md']} !important;
}}

/* Progress Bar */
.stProgress > div > div > div {{
    background: {THEME['accent']} !important;
}}

/* Metric */
[data-testid="stMetricValue"] {{
    font-family: {THEME['font']} !important;
    font-weight: 700 !important;
    color: {THEME['primary']} !important;
}}

[data-testid="stMetricLabel"] {{
    font-family: {THEME['font']} !important;
    color: {THEME['secondary']} !important;
}}

/* Animation */
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.animate-fade-in {{
    animation: fadeIn 0.4s ease-out;
}}

/* Scrollbar */
::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}

::-webkit-scrollbar-track {{
    background: transparent;
}}

::-webkit-scrollbar-thumb {{
    background: {THEME['border']};
    border-radius: 4px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: {THEME['border_dark']};
}}
</style>
"""


# ============================================
# SVG Icons (Minimal Set)
# ============================================
ICONS = {
    "mic": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>',
    "video": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m22 8-6 4 6 4V8Z"/><rect width="14" height="12" x="2" y="6" rx="2" ry="2"/></svg>',
    "message-circle": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"/></svg>',
    "globe": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" x2="22" y1="12" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "users": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "file-text": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>',
    "camera": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>',
    "shirt": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23Z"/></svg>',
    "volume-2": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>',
    "book-open": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
    "help-circle": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>',
    "lightbulb": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>',
    "plane": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/></svg>',
    "dumbbell": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6.5 6.5 11 11"/><path d="m21 21-1-1"/><path d="m3 3 1 1"/><path d="m18 22 4-4"/><path d="m2 6 4-4"/><path d="m3 10 7-7"/><path d="m14 21 7-7"/></svg>',
    "building": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg>',
    "bar-chart": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/></svg>',
    "clipboard-list": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/></svg>',
    "trending-up": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
    "briefcase": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="20" height="14" x="2" y="7" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    "database": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/></svg>',
    "calendar": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>',
    "chevron-down": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>',
    "arrow-right": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>',
    "sparkles": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3Z"/></svg>',
    "home": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
}


def get_icon(name: str, size: int = 20, color: str = "currentColor") -> str:
    """Get SVG icon"""
    icon = ICONS.get(name, ICONS.get("help-circle", ""))
    if size != 20:
        icon = icon.replace('width="20"', f'width="{size}"').replace('height="20"', f'height="{size}"')
    if color != "currentColor":
        icon = icon.replace('stroke="currentColor"', f'stroke="{color}"')
    return icon


# ============================================
# Layout Components
# ============================================
def init_page(
    title: str = "FlyReady Lab",
    icon: str = "plane",
    layout: str = "wide"
):
    """Initialize page with proper configuration"""
    st.set_page_config(
        page_title=title,
        page_icon="✈️",
        layout=layout,
        initial_sidebar_state="collapsed"
    )
    st.markdown(get_global_css(), unsafe_allow_html=True)


def render_navbar(current_page: str = ""):
    """Render top navigation bar"""
    nav_items_html = ""

    for key, section in NAV_SECTIONS.items():
        dropdown_items = ""
        for item in section["items"]:
            is_active = current_page == item.page
            active_class = "active" if is_active else ""
            dropdown_items += f'''
            <a href="/{item.page}" class="nav-dropdown-item {active_class}">
                {get_icon(item.icon, 18)}
                <span>{item.label}</span>
            </a>
            '''

        nav_items_html += f'''
        <div class="nav-link">
            {section["label"]}
            {get_icon("chevron-down", 16)}
            <div class="nav-dropdown">
                {dropdown_items}
            </div>
        </div>
        '''

    st.markdown(f'''
    <nav class="nav-top">
        <a href="/" class="nav-logo">
            <span style="color: #2563EB;">Fly</span><span>Ready Lab</span>
        </a>
        <div class="nav-links">
            {nav_items_html}
        </div>
        <div class="nav-right">
            <a href="/로그인" class="nav-btn nav-btn-ghost">로그인</a>
            <a href="/회원가입" class="nav-btn nav-btn-primary">시작하기</a>
        </div>
    </nav>
    <div style="height: 56px;"></div>
    ''', unsafe_allow_html=True)


def render_page_header(
    title: str,
    description: str = "",
    breadcrumb: List[Dict[str, str]] = None
):
    """Render page header"""
    breadcrumb_html = ""
    if breadcrumb:
        items = []
        for item in breadcrumb:
            if item.get("link"):
                items.append(f'<a href="{item["link"]}">{item["label"]}</a>')
            else:
                items.append(f'<span>{item["label"]}</span>')
        breadcrumb_html = f'''
        <div class="page-breadcrumb">
            {' <span>/</span> '.join(items)}
        </div>
        '''

    desc_html = f'<p class="page-description">{description}</p>' if description else ""

    st.markdown(f'''
    <div class="page-header animate-fade-in">
        <div class="page-header-inner">
            {breadcrumb_html}
            <h1 class="page-title">{title}</h1>
            {desc_html}
        </div>
    </div>
    ''', unsafe_allow_html=True)


def render_hero(
    title: str,
    subtitle: str,
    primary_action: Dict[str, str] = None,
    secondary_action: Dict[str, str] = None,
    badge: str = ""
):
    """Render hero section"""
    badge_html = f'<div class="hero-badge">{get_icon("sparkles", 16)} {badge}</div>' if badge else ""

    actions_html = '<div class="hero-actions">'
    if primary_action:
        actions_html += f'''
        <a href="{primary_action.get("link", "#")}" class="hero-btn hero-btn-primary">
            {primary_action.get("label", "시작하기")}
            {get_icon("arrow-right", 16)}
        </a>
        '''
    if secondary_action:
        actions_html += f'''
        <a href="{secondary_action.get("link", "#")}" class="hero-btn hero-btn-secondary">
            {secondary_action.get("label", "더 알아보기")}
        </a>
        '''
    actions_html += '</div>'

    st.markdown(f'''
    <div class="hero">
        <div class="hero-inner animate-fade-in">
            {badge_html}
            <h1 class="hero-title">{title}</h1>
            <p class="hero-subtitle">{subtitle}</p>
            {actions_html}
        </div>
    </div>
    ''', unsafe_allow_html=True)


def render_section(
    title: str,
    label: str = "",
    content: str = ""
):
    """Render section wrapper"""
    label_html = f'<div class="section-label">{label}</div>' if label else ""

    st.markdown(f'''
    <section class="section animate-fade-in">
        <div class="section-header">
            {label_html}
            <h2 class="section-title">{title}</h2>
        </div>
        {content}
    </section>
    ''', unsafe_allow_html=True)


def render_stat_cards(stats: List[Dict[str, Any]]):
    """Render stat cards grid"""
    cards_html = ""
    for stat in stats:
        trend_html = ""
        if stat.get("trend"):
            trend_class = "stat-trend-up" if stat.get("trend_positive", True) else "stat-trend-down"
            trend_icon = "trending-up" if stat.get("trend_positive", True) else "trending-down"
            trend_html = f'''
            <div class="stat-trend {trend_class}">
                {get_icon(trend_icon, 14)} {stat["trend"]}
            </div>
            '''

        cards_html += f'''
        <div class="stat-card">
            <div class="stat-value">{stat.get("value", "-")}</div>
            <div class="stat-label">{stat.get("label", "")}</div>
            {trend_html}
        </div>
        '''

    st.markdown(f'''
    <div class="grid grid-4">
        {cards_html}
    </div>
    ''', unsafe_allow_html=True)


def render_feature_cards(features: List[Dict[str, str]], columns: int = 4):
    """Render feature cards grid"""
    cards_html = ""
    for feature in features:
        icon_html = get_icon(feature.get("icon", "sparkles"), 22)
        cards_html += f'''
        <a href="{feature.get("link", "#")}" class="feature-card">
            <div class="feature-icon">{icon_html}</div>
            <div>
                <div class="feature-title">{feature.get("title", "")}</div>
                <div class="feature-desc">{feature.get("description", "")}</div>
            </div>
        </a>
        '''

    st.markdown(f'''
    <div class="grid grid-{columns}">
        {cards_html}
    </div>
    ''', unsafe_allow_html=True)


def render_footer():
    """Render footer"""
    st.markdown('''
    <footer class="footer">
        <div class="footer-inner">
            <div>
                <div class="footer-brand">FlyReady Lab</div>
                <div class="footer-copy">AI와 함께하는 승무원 면접 준비</div>
            </div>
            <div class="footer-links">
                <a href="#" class="footer-link">이용약관</a>
                <a href="#" class="footer-link">개인정보처리방침</a>
                <a href="#" class="footer-link">문의하기</a>
            </div>
            <div class="footer-copy">2026 FlyReady Lab. All rights reserved.</div>
        </div>
    </footer>
    ''', unsafe_allow_html=True)


def start_page_body():
    """Start page body container"""
    st.markdown('<div class="page-body animate-fade-in">', unsafe_allow_html=True)


def end_page_body():
    """End page body container"""
    st.markdown('</div>', unsafe_allow_html=True)
