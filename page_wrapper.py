# page_wrapper.py
# FlyReady Lab - Page Wrapper for consistent layout across all pages
# Use this to ensure every page has the same header, navigation, and footer

import streamlit as st
from typing import Optional, List, Dict, Any
from layout import (
    get_global_css,
    render_navbar,
    render_page_header,
    render_footer,
    start_page_body,
    end_page_body,
    THEME,
)


def setup_page(
    title: str,
    page_title: str = None,
    description: str = "",
    breadcrumb: List[Dict[str, str]] = None,
    show_navbar: bool = True,
    show_footer: bool = True,
    current_page: str = "",
    wide_layout: bool = True
):
    """
    Setup a page with consistent layout.

    Args:
        title: Main page title displayed on the page
        page_title: Browser tab title (defaults to "FlyReady Lab - {title}")
        description: Page description/subtitle
        breadcrumb: List of breadcrumb items [{"label": "Home", "link": "/"}]
        show_navbar: Whether to show the top navigation bar
        show_footer: Whether to show the footer
        current_page: Current page identifier for nav highlighting
        wide_layout: Use wide layout (True) or centered (False)
    """
    # Page config
    st.set_page_config(
        page_title=page_title or f"FlyReady Lab - {title}",
        page_icon="✈️",
        layout="wide" if wide_layout else "centered",
        initial_sidebar_state="collapsed"
    )

    # Apply global CSS
    st.markdown(get_global_css(), unsafe_allow_html=True)

    # Navigation
    if show_navbar:
        render_navbar(current_page)

    # Page header
    render_page_header(title, description, breadcrumb)

    # Start page body
    start_page_body()


def end_page(show_footer: bool = True):
    """
    End page with proper closing elements.

    Args:
        show_footer: Whether to show the footer
    """
    end_page_body()

    if show_footer:
        render_footer()


class PageLayout:
    """
    Context manager for page layout.

    Usage:
        with PageLayout(title="My Page", description="Description"):
            st.write("Page content here")
    """

    def __init__(
        self,
        title: str,
        page_title: str = None,
        description: str = "",
        breadcrumb: List[Dict[str, str]] = None,
        show_navbar: bool = True,
        show_footer: bool = True,
        current_page: str = "",
        wide_layout: bool = True
    ):
        self.title = title
        self.page_title = page_title
        self.description = description
        self.breadcrumb = breadcrumb
        self.show_navbar = show_navbar
        self.show_footer = show_footer
        self.current_page = current_page
        self.wide_layout = wide_layout

    def __enter__(self):
        setup_page(
            title=self.title,
            page_title=self.page_title,
            description=self.description,
            breadcrumb=self.breadcrumb,
            show_navbar=self.show_navbar,
            show_footer=self.show_footer,
            current_page=self.current_page,
            wide_layout=self.wide_layout
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_page(self.show_footer)
        return False


# ============================================
# Common UI Components
# ============================================

def render_card(
    title: str,
    content: str = "",
    icon: str = "",
    link: str = "",
    badge: str = "",
    badge_type: str = "blue"
):
    """Render a styled card"""
    from layout import get_icon

    icon_html = ""
    if icon:
        icon_html = f'''
        <div style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; background: rgba(37, 99, 235, 0.1); border-radius: 8px; color: #2563EB; margin-bottom: 16px;">
            {get_icon(icon, 22)}
        </div>
        '''

    badge_html = ""
    if badge:
        badge_colors = {
            "blue": ("rgba(37, 99, 235, 0.1)", "#2563EB"),
            "green": ("rgba(5, 150, 105, 0.1)", "#059669"),
            "amber": ("rgba(217, 119, 6, 0.1)", "#D97706"),
            "red": ("rgba(220, 38, 38, 0.1)", "#DC2626"),
        }
        bg, color = badge_colors.get(badge_type, badge_colors["blue"])
        badge_html = f'<span style="display: inline-block; padding: 4px 10px; background: {bg}; color: {color}; font-size: 12px; font-weight: 500; border-radius: 9999px; margin-bottom: 12px;">{badge}</span>'

    content_html = f'<p style="color: #475569; font-size: 14px; line-height: 1.5; margin: 0;">{content}</p>' if content else ""

    card_style = """
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 24px;
        transition: all 0.2s ease;
        text-decoration: none;
        display: block;
        color: inherit;
    """

    if link:
        st.markdown(f'''
        <a href="{link}" style="{card_style}" onmouseover="this.style.borderColor='#2563EB'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 6px -1px rgb(0 0 0 / 0.1)';" onmouseout="this.style.borderColor='#E2E8F0'; this.style.transform='none'; this.style.boxShadow='none';">
            {badge_html}
            {icon_html}
            <h3 style="font-size: 16px; font-weight: 600; color: #0F172A; margin: 0 0 8px 0;">{title}</h3>
            {content_html}
        </a>
        ''', unsafe_allow_html=True)
    else:
        st.markdown(f'''
        <div style="{card_style}">
            {badge_html}
            {icon_html}
            <h3 style="font-size: 16px; font-weight: 600; color: #0F172A; margin: 0 0 8px 0;">{title}</h3>
            {content_html}
        </div>
        ''', unsafe_allow_html=True)


def render_stat(value: str, label: str, trend: str = "", trend_up: bool = True):
    """Render a stat display"""
    trend_html = ""
    if trend:
        trend_color = "#059669" if trend_up else "#DC2626"
        trend_bg = "rgba(5, 150, 105, 0.1)" if trend_up else "rgba(220, 38, 38, 0.1)"
        trend_html = f'''
        <div style="display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; background: {trend_bg}; color: {trend_color}; font-size: 12px; font-weight: 500; border-radius: 9999px; margin-top: 8px;">
            {trend}
        </div>
        '''

    st.markdown(f'''
    <div style="padding: 20px; background: #F8FAFC; border-radius: 12px;">
        <div style="font-size: 28px; font-weight: 700; color: #0F172A; line-height: 1.2;">{value}</div>
        <div style="font-size: 13px; color: #475569; margin-top: 4px;">{label}</div>
        {trend_html}
    </div>
    ''', unsafe_allow_html=True)


def render_alert(message: str, type: str = "info", title: str = ""):
    """Render an alert/notice box"""
    colors = {
        "info": ("#EFF6FF", "#2563EB", "#1E40AF"),
        "success": ("#F0FDF4", "#059669", "#166534"),
        "warning": ("#FFFBEB", "#D97706", "#92400E"),
        "error": ("#FEF2F2", "#DC2626", "#991B1B"),
    }
    bg, border, text = colors.get(type, colors["info"])

    title_html = f'<div style="font-weight: 600; margin-bottom: 4px;">{title}</div>' if title else ""

    st.markdown(f'''
    <div style="padding: 16px 20px; background: {bg}; border-left: 4px solid {border}; border-radius: 8px; color: {text}; margin: 12px 0;">
        {title_html}
        <div style="font-size: 14px; line-height: 1.5;">{message}</div>
    </div>
    ''', unsafe_allow_html=True)


def render_divider(margin: int = 24):
    """Render a divider line"""
    st.markdown(f'<div style="height: 1px; background: #E2E8F0; margin: {margin}px 0;"></div>', unsafe_allow_html=True)


def render_section_title(title: str, subtitle: str = "", label: str = ""):
    """Render a section title"""
    label_html = f'<div style="font-size: 13px; font-weight: 600; color: #2563EB; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;">{label}</div>' if label else ""
    subtitle_html = f'<p style="font-size: 14px; color: #475569; margin: 8px 0 0 0;">{subtitle}</p>' if subtitle else ""

    st.markdown(f'''
    <div style="margin-bottom: 24px;">
        {label_html}
        <h2 style="font-size: 24px; font-weight: 700; color: #0F172A; margin: 0;">{title}</h2>
        {subtitle_html}
    </div>
    ''', unsafe_allow_html=True)


def render_empty_state(
    title: str = "데이터가 없습니다",
    description: str = "",
    action_text: str = "",
    action_link: str = ""
):
    """Render empty state placeholder"""
    from layout import get_icon

    action_html = ""
    if action_text and action_link:
        action_html = f'''
        <a href="{action_link}" style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; background: #2563EB; color: white; font-size: 14px; font-weight: 500; border-radius: 8px; text-decoration: none; margin-top: 20px;">
            {action_text}
        </a>
        '''

    desc_html = f'<p style="color: #94A3B8; font-size: 14px; margin: 8px 0 0 0;">{description}</p>' if description else ""

    st.markdown(f'''
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 64px 24px; text-align: center;">
        <div style="width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; background: #F8FAFC; border-radius: 50%; color: #94A3B8; margin-bottom: 20px;">
            {get_icon("help-circle", 28)}
        </div>
        <h3 style="font-size: 18px; font-weight: 600; color: #0F172A; margin: 0;">{title}</h3>
        {desc_html}
        {action_html}
    </div>
    ''', unsafe_allow_html=True)


def render_loading(text: str = "로딩 중..."):
    """Render loading spinner"""
    st.markdown(f'''
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px; gap: 16px;">
        <div style="width: 40px; height: 40px; border: 3px solid #E2E8F0; border-top-color: #2563EB; border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
        <div style="color: #64748b; font-size: 14px;">{text}</div>
    </div>
    <style>
    @keyframes spin {{
        to {{ transform: rotate(360deg); }}
    }}
    </style>
    ''', unsafe_allow_html=True)
