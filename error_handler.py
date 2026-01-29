# error_handler.py
import streamlit as st
from datetime import datetime
from functools import wraps

class ErrorType:
    NOT_FOUND = 'not_found'
    SERVER = 'server'
    PERMISSION = 'permission'
    NETWORK = 'network'

ERROR_CSS = '<style>.fr-error-container{min-height:80vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#f8fafc,#e2e8f0);padding:40px 20px}.fr-error-card{background:white;border-radius:20px;padding:48px;max-width:500px;width:100%;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,0.1);animation:fadeIn .5s}@keyframes fadeIn{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}.fr-error-code{font-size:4rem;font-weight:800;background:linear-gradient(135deg,#1e3a5f,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px;line-height:1}.fr-error-title{font-size:1.5rem;font-weight:700;color:#1e3a5f;margin-bottom:12px}.fr-error-message{font-size:1rem;color:#64748b;line-height:1.6;margin-bottom:32px}.fr-error-actions{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}.fr-error-btn{display:inline-flex;align-items:center;gap:8px;padding:14px 28px;border-radius:10px;font-weight:600;font-size:.95rem;text-decoration:none;transition:all .2s;cursor:pointer;border:none}.fr-error-btn-primary{background:linear-gradient(135deg,#3b82f6,#6366f1);color:white;box-shadow:0 4px 12px rgba(59,130,246,0.3)}.fr-error-btn-primary:hover{transform:translateY(-2px)}.fr-error-btn-secondary{background:#f1f5f9;color:#475569}.fr-toast-container{position:fixed;top:20px;right:20px;z-index:10000}.fr-toast{padding:16px 24px;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.15);animation:slideIn .3s;display:flex;align-items:center;gap:12px;max-width:400px}@keyframes slideIn{from{opacity:0;transform:translateX(100px)}to{opacity:1;transform:translateX(0)}}.fr-toast-success{background:linear-gradient(135deg,#10b981,#059669);color:white}.fr-toast-error{background:linear-gradient(135deg,#ef4444,#dc2626);color:white}.fr-toast-info{background:linear-gradient(135deg,#3b82f6,#2563eb);color:white}@media(max-width:600px){.fr-error-card{padding:32px 24px}.fr-error-code{font-size:3rem}.fr-error-actions{flex-direction:column}.fr-error-btn{width:100%;justify-content:center}}</style>'

ERRORS = {
    'not_found': ('404', '페이지를 찾을 수 없습니다', '요청하신 페이지가 존재하지 않습니다.'),
    'server': ('500', '서버 오류', '일시적인 서버 문제입니다. 잠시 후 다시 시도해주세요.'),
    'permission': ('403', '접근 권한이 없습니다', '이 페이지에 접근할 권한이 없습니다.'),
    'network': ('503', '네트워크 오류', '인터넷 연결을 확인해주세요.')
}

def show_error_page(error_type='server', custom_title=None, custom_message=None, show_home=True, show_back=True):
    code, title, message = ERRORS.get(error_type, ERRORS['server'])
    title = custom_title or title
    message = custom_message or message
    st.markdown(ERROR_CSS, unsafe_allow_html=True)
    btns = ''
    if show_home:
        btns += '<a href="/" target="_self" class="fr-error-btn fr-error-btn-primary">홈으로</a>'
    if show_back:
        btns += '<a href="javascript:history.back()" class="fr-error-btn fr-error-btn-secondary">이전</a>'
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html = f'<div class="fr-error-container"><div class="fr-error-card"><div class="fr-error-code">{code}</div><div class="fr-error-title">{title}</div><div class="fr-error-message">{message}</div><div class="fr-error-actions">{btns}</div><div style="margin-top:24px;font-size:0.75rem;color:#94a3b8">오류 발생: {ts}</div></div></div>'
    st.markdown(html, unsafe_allow_html=True)

def show_toast(message, toast_type='info'):
    icons = {'success': '✓', 'error': '✗', 'warning': '!', 'info': 'ℹ'}
    icon = icons.get(toast_type, 'ℹ')
    html = f'<div class="fr-toast-container"><div class="fr-toast fr-toast-{toast_type}"><span>{icon}</span><span>{message}</span></div></div>'
    st.markdown(html, unsafe_allow_html=True)

def handle_errors(error_type='server', show_toast_on_error=True, reraise=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if show_toast_on_error:
                    show_toast(f'오류: {str(e)}', 'error')
                if reraise:
                    raise
                return None
        return wrapper
    return decorator

class ErrorBoundary:
    def __init__(self, name='작업', show_page=False, error_type='server'):
        self.name = name
        self.show_page = show_page
        self.error_type = error_type
        self.error = None
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.error = exc_val
            if self.show_page:
                show_error_page(self.error_type, custom_message=f'{self.name} 중 오류')
            else:
                show_toast(f'{self.name} 중 오류 발생', 'error')
            return True
        return False

def safe_execute(func, *args, default=None, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception:
        return default
