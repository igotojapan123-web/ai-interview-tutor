# animation_components.py
# 롤플레잉 및 토론면접용 애니메이션 컴포넌트

import streamlit.components.v1 as components


def render_animated_passenger(
    message: str,
    persona: str,
    escalation_level: int = 0,
    passenger_emoji: str = "👨",
    is_speaking: bool = True
):
    """
    애니메이션 승객 캐릭터 렌더링 (components.html 사용)
    """
    # 감정 레벨별 설정
    if escalation_level == 0:
        bg_color = "#e0f2fe"
        border_color = "#0ea5e9"
        mood_emoji = "🙂"
        mood_text = "차분함"
        bubble_color = "#f0f9ff"
    elif escalation_level == 1:
        bg_color = "#fef3c7"
        border_color = "#f59e0b"
        mood_emoji = "😤"
        mood_text = "짜증남"
        bubble_color = "#fffbeb"
    else:
        bg_color = "#fee2e2"
        border_color = "#ef4444"
        mood_emoji = "😠"
        mood_text = "화남"
        bubble_color = "#fef2f2"

    # 애니메이션 선택
    if is_speaking and escalation_level >= 2:
        animation = "angry-shake 0.2s infinite"
    elif is_speaking:
        animation = "passenger-speak 0.4s infinite"
    else:
        animation = "passenger-breathe 3s ease-in-out infinite"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: transparent; }}

    @keyframes passenger-breathe {{
        0%, 100% {{ transform: scale(1) translateY(0); }}
        50% {{ transform: scale(1.02) translateY(-2px); }}
    }}
    @keyframes passenger-speak {{
        0%, 100% {{ transform: scale(1) rotate(0deg); }}
        25% {{ transform: scale(1.05) rotate(-2deg); }}
        75% {{ transform: scale(1.05) rotate(2deg); }}
    }}
    @keyframes angry-shake {{
        0%, 100% {{ transform: translateX(0); }}
        25% {{ transform: translateX(-3px); }}
        75% {{ transform: translateX(3px); }}
    }}
    @keyframes bubble-appear {{
        0% {{ opacity: 0; transform: scale(0.9) translateY(10px); }}
        100% {{ opacity: 1; transform: scale(1) translateY(0); }}
    }}
    @keyframes mood-pulse {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.15); }}
    }}

    .container {{
        display: flex;
        align-items: flex-start;
        gap: 18px;
        padding: 22px;
        background: linear-gradient(145deg, {bg_color} 0%, white 100%);
        border-left: 5px solid {border_color};
        border-radius: 18px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    }}
    .avatar {{
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 80px;
    }}
    .avatar-icon {{
        font-size: 55px;
        animation: {animation};
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
    }}
    .mood {{
        display: flex;
        align-items: center;
        gap: 5px;
        margin-top: 8px;
        padding: 4px 10px;
        background: {border_color}20;
        border-radius: 15px;
        font-size: 11px;
        color: {border_color};
        font-weight: 600;
    }}
    .mood-emoji {{
        font-size: 16px;
        animation: mood-pulse 1s infinite;
    }}
    .speech {{
        flex: 1;
    }}
    .label {{
        font-size: 12px;
        color: {border_color};
        font-weight: 700;
        margin-bottom: 8px;
    }}
    .bubble {{
        background: {bubble_color};
        padding: 16px 20px;
        border-radius: 16px;
        border-top-left-radius: 4px;
        font-size: 15px;
        color: #1f2937;
        line-height: 1.7;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        animation: bubble-appear 0.4s ease-out;
    }}
    </style>
    </head>
    <body>
    <div class="container">
        <div class="avatar">
            <div class="avatar-icon">{passenger_emoji}</div>
            <div class="mood">
                <span class="mood-emoji">{mood_emoji}</span>
                <span>{mood_text}</span>
            </div>
        </div>
        <div class="speech">
            <div class="label">✈️ 승객</div>
            <div class="bubble">{message}</div>
        </div>
    </div>
    </body>
    </html>
    """
    components.html(html, height=180)


def render_animated_crew(message: str):
    """
    애니메이션 승무원(사용자) 캐릭터 렌더링
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: transparent; }

    @keyframes crew-float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-3px); }
    }
    @keyframes bubble-appear {
        0% { opacity: 0; transform: scale(0.9) translateX(-10px); }
        100% { opacity: 1; transform: scale(1) translateX(0); }
    }

    .container {
        display: flex;
        align-items: flex-start;
        gap: 18px;
        padding: 22px;
        background: linear-gradient(145deg, #dcfce7 0%, white 100%);
        border-right: 5px solid #10b981;
        border-radius: 18px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        flex-direction: row-reverse;
    }
    .avatar {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 80px;
    }
    .avatar-icon {
        font-size: 55px;
        animation: crew-float 3s ease-in-out infinite;
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
    }
    .badge {
        margin-top: 8px;
        padding: 4px 10px;
        background: #10b98120;
        border-radius: 15px;
        font-size: 11px;
        color: #10b981;
        font-weight: 600;
    }
    .speech {
        flex: 1;
        text-align: right;
    }
    .label {
        font-size: 12px;
        color: #10b981;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .bubble {
        display: inline-block;
        text-align: left;
        background: #f0fdf4;
        padding: 16px 20px;
        border-radius: 16px;
        border-top-right-radius: 4px;
        font-size: 15px;
        color: #1f2937;
        line-height: 1.7;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        animation: bubble-appear 0.4s ease-out;
    }
    </style>
    </head>
    <body>
    <div class="container">
        <div class="avatar">
            <div class="avatar-icon">👩‍✈️</div>
            <div class="badge">승무원</div>
        </div>
        <div class="speech">
            <div class="label">✈️ 나 (승무원)</div>
            <div class="bubble">""" + message + """</div>
        </div>
    </div>
    </body>
    </html>
    """
    components.html(html, height=160)


def render_roleplay_scene(scenario_type: str, situation: str):
    """
    롤플레잉 상황별 애니메이션 장면 렌더링

    scenario_type: 시나리오 유형 (seat_change, meal, delay, medical, drunk, etc.)
    """
    # 시나리오별 배경 설정
    scenes = {
        "seat": {
            "bg": "linear-gradient(180deg, #1e3a5f 0%, #2d4a6f 100%)",
            "icon": "💺",
            "title": "좌석 구역",
            "elements": ["🪟", "💺", "💺", "🪟"]
        },
        "meal": {
            "bg": "linear-gradient(180deg, #1e3a5f 0%, #2d4a6f 100%)",
            "icon": "🍽️",
            "title": "기내식 서비스",
            "elements": ["🥗", "🍝", "🥤", "🍞"]
        },
        "delay": {
            "bg": "linear-gradient(180deg, #374151 0%, #1f2937 100%)",
            "icon": "⏰",
            "title": "지연/결항 상황",
            "elements": ["🌧️", "⚡", "✈️", "⏱️"]
        },
        "medical": {
            "bg": "linear-gradient(180deg, #7f1d1d 0%, #991b1b 100%)",
            "icon": "🏥",
            "title": "응급 상황",
            "elements": ["💊", "🩺", "❤️", "🆘"]
        },
        "drunk": {
            "bg": "linear-gradient(180deg, #78350f 0%, #92400e 100%)",
            "icon": "🍺",
            "title": "음주 승객",
            "elements": ["🍷", "😵", "🚫", "⚠️"]
        },
        "vip": {
            "bg": "linear-gradient(180deg, #4c1d95 0%, #5b21b6 100%)",
            "icon": "👑",
            "title": "VIP 승객",
            "elements": ["💎", "✨", "🥂", "⭐"]
        },
        "default": {
            "bg": "linear-gradient(180deg, #1e3a5f 0%, #2d4a6f 100%)",
            "icon": "✈️",
            "title": "기내 상황",
            "elements": ["🪟", "💺", "💺", "🪟"]
        }
    }

    # 시나리오 타입 매칭
    scene = scenes.get("default")
    situation_lower = situation.lower()
    if "좌석" in situation_lower or "자리" in situation_lower:
        scene = scenes.get("seat")
    elif "기내식" in situation_lower or "음식" in situation_lower or "식사" in situation_lower:
        scene = scenes.get("meal")
    elif "지연" in situation_lower or "결항" in situation_lower or "취소" in situation_lower:
        scene = scenes.get("delay")
    elif "응급" in situation_lower or "환자" in situation_lower or "아프" in situation_lower or "쓰러" in situation_lower:
        scene = scenes.get("medical")
    elif "음주" in situation_lower or "술" in situation_lower or "취한" in situation_lower:
        scene = scenes.get("drunk")
    elif "vip" in situation_lower or "비즈니스" in situation_lower or "퍼스트" in situation_lower:
        scene = scenes.get("vip")

    elements_html = "".join([f'<div class="element">{e}</div>' for e in scene["elements"]])

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: transparent; }}

    @keyframes float {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-5px); }}
    }}
    @keyframes pulse {{
        0%, 100% {{ opacity: 0.6; }}
        50% {{ opacity: 1; }}
    }}
    @keyframes slide-in {{
        0% {{ opacity: 0; transform: translateY(-20px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}

    .scene {{
        background: {scene["bg"]};
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        animation: slide-in 0.5s ease-out;
        position: relative;
        overflow: hidden;
    }}
    .scene::before {{
        content: '';
        position: absolute;
        top: 15px;
        left: 50%;
        transform: translateX(-50%);
        width: 150px;
        height: 40px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        border-radius: 20px;
    }}
    .elements {{
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 15px;
    }}
    .element {{
        font-size: 28px;
        animation: float 2s ease-in-out infinite;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
    }}
    .element:nth-child(2) {{ animation-delay: 0.3s; }}
    .element:nth-child(3) {{ animation-delay: 0.6s; }}
    .element:nth-child(4) {{ animation-delay: 0.9s; }}
    .icon {{
        font-size: 45px;
        margin-bottom: 10px;
        animation: pulse 2s infinite;
    }}
    .title {{
        color: white;
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 8px;
    }}
    .subtitle {{
        color: rgba(255,255,255,0.8);
        font-size: 13px;
        line-height: 1.5;
    }}
    </style>
    </head>
    <body>
    <div class="scene">
        <div class="elements">{elements_html}</div>
        <div class="icon">{scene["icon"]}</div>
        <div class="title">{scene["title"]}</div>
        <div class="subtitle">승객이 다가오고 있습니다...</div>
    </div>
    </body>
    </html>
    """
    components.html(html, height=200)


def render_debate_table(current_speaker: str = "", user_position: str = "pro"):
    """
    토론 테이블 장면 렌더링
    """
    position_labels = {"pro": "찬성", "con": "반대", "neutral": "중립"}
    user_pos_kr = position_labels.get(user_position, "찬성")

    # 각 좌석별 활성화 상태
    speakers = [
        {"name": "김찬성", "pos": "찬성", "emoji": "👨‍💼", "color": "#3b82f6"},
        {"name": "나", "pos": user_pos_kr, "emoji": "✈️", "color": "#10b981", "is_user": True},
        {"name": "이반대", "pos": "반대", "emoji": "👩‍💼", "color": "#ef4444"},
        {"name": "박중립", "pos": "중립", "emoji": "🧑‍💼", "color": "#8b5cf6"},
    ]

    seats_html = ""
    for s in speakers:
        is_active = (s["name"] == current_speaker) or (current_speaker == "user" and s.get("is_user"))
        active_class = "active" if is_active else ""
        user_class = "user-seat" if s.get("is_user") else ""
        speaking_indicator = '<div class="speaking">💬</div>' if is_active else ""

        seats_html += f"""
        <div class="seat {active_class} {user_class}">
            <div class="seat-avatar" style="border-color: {s['color']}">
                <span class="emoji">{s['emoji']}</span>
            </div>
            <div class="seat-info">
                <span class="name" style="color: {s['color']}">{s['name']}</span>
                <span class="pos" style="background: {s['color']}20; color: {s['color']}">{s['pos']}</span>
            </div>
            {speaking_indicator}
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: transparent; }}

    @keyframes table-glow {{
        0%, 100% {{ box-shadow: 0 8px 30px rgba(0,0,0,0.15); }}
        50% {{ box-shadow: 0 12px 40px rgba(0,0,0,0.2); }}
    }}
    @keyframes speaker-pulse {{
        0%, 100% {{ transform: scale(1); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        50% {{ transform: scale(1.05); box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3); }}
    }}
    @keyframes speaking-bounce {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-4px); }}
    }}

    .room {{
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 25px;
        border-radius: 20px;
        position: relative;
    }}
    .room::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6, #10b981, #ef4444, #8b5cf6);
        border-radius: 20px 20px 0 0;
    }}
    .header {{
        text-align: center;
        margin-bottom: 20px;
    }}
    .header h3 {{
        color: #1e293b;
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 4px;
    }}
    .header p {{
        color: #64748b;
        font-size: 12px;
    }}
    .table {{
        background: linear-gradient(145deg, #475569 0%, #334155 100%);
        border-radius: 80px;
        height: 50px;
        margin: 0 auto 20px;
        width: 70%;
        max-width: 400px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 13px;
        font-weight: 600;
        animation: table-glow 3s ease-in-out infinite;
    }}
    .seats {{
        display: flex;
        justify-content: center;
        gap: 15px;
        flex-wrap: wrap;
    }}
    .seat {{
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 12px;
        background: white;
        border-radius: 14px;
        min-width: 85px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        position: relative;
        opacity: 0.65;
        transform: scale(0.95);
    }}
    .seat.active {{
        opacity: 1;
        transform: scale(1);
        animation: speaker-pulse 1.5s ease-in-out infinite;
    }}
    .seat.user-seat {{
        background: linear-gradient(145deg, #f0fdf4 0%, #dcfce7 100%);
        border: 2px solid #10b981;
    }}
    .seat-avatar {{
        width: 50px;
        height: 50px;
        background: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 3px solid #e2e8f0;
        margin-bottom: 8px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.1);
    }}
    .emoji {{
        font-size: 26px;
    }}
    .seat-info {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
    }}
    .name {{
        font-weight: 700;
        font-size: 12px;
    }}
    .pos {{
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 8px;
        font-weight: 600;
    }}
    .speaking {{
        position: absolute;
        top: -8px;
        right: -8px;
        font-size: 20px;
        animation: speaking-bounce 0.5s ease-in-out infinite;
    }}
    </style>
    </head>
    <body>
    <div class="room">
        <div class="header">
            <h3>📋 그룹 토론면접</h3>
            <p>면접복 차림의 지원자들이 토론 중입니다</p>
        </div>
        <div class="table">💬 토론 중</div>
        <div class="seats">{seats_html}</div>
    </div>
    </body>
    </html>
    """
    components.html(html, height=280)


def render_animated_debater(
    message: str,
    name: str,
    position: str,
    emoji: str = "👨‍💼",
    color: str = "#3b82f6",
    is_speaking: bool = True
):
    """
    애니메이션 토론자 발언 렌더링
    """
    position_labels = {"pro": "찬성", "con": "반대", "neutral": "중립"}
    position_kr = position_labels.get(position, "")

    animation = "debater-speak 0.8s ease-in-out infinite" if is_speaking else "none"
    glow_animation = "border-glow 2s ease-in-out infinite," if is_speaking else ""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: transparent; }}

    @keyframes debater-speak {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.03); }}
    }}
    @keyframes speech-fade-in {{
        0% {{ opacity: 0; transform: translateX(-15px); }}
        100% {{ opacity: 1; transform: translateX(0); }}
    }}
    @keyframes border-glow {{
        0%, 100% {{ box-shadow: 0 0 0 0 {color}40; }}
        50% {{ box-shadow: 0 0 12px 3px {color}30; }}
    }}

    .container {{
        display: flex;
        align-items: flex-start;
        gap: 15px;
        padding: 18px;
        background: linear-gradient(145deg, {color}08 0%, white 100%);
        border-left: 4px solid {color};
        border-radius: 14px;
        animation: {glow_animation} speech-fade-in 0.4s ease-out;
    }}
    .avatar {{
        min-width: 60px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }}
    .avatar-icon {{
        width: 52px;
        height: 52px;
        background: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        border: 3px solid {color}30;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        animation: {animation};
    }}
    .info {{
        flex: 1;
    }}
    .header {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }}
    .name {{
        font-weight: 700;
        color: {color};
        font-size: 14px;
    }}
    .badge {{
        background: {color}15;
        color: {color};
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: 600;
    }}
    .bubble {{
        background: white;
        padding: 14px 18px;
        border-radius: 12px;
        border-top-left-radius: 4px;
        font-size: 14px;
        color: #1f2937;
        line-height: 1.6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    </style>
    </head>
    <body>
    <div class="container">
        <div class="avatar">
            <div class="avatar-icon">{emoji}</div>
        </div>
        <div class="info">
            <div class="header">
                <span class="name">{name}</span>
                <span class="badge">{position_kr}</span>
            </div>
            <div class="bubble">{message}</div>
        </div>
    </div>
    </body>
    </html>
    """
    components.html(html, height=140)


def render_user_debate(message: str, position: str):
    """
    애니메이션 사용자 토론 발언 렌더링
    """
    position_labels = {"pro": "찬성", "con": "반대", "neutral": "중립"}
    position_kr = position_labels.get(position, "")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: transparent; }}

    @keyframes user-appear {{
        0% {{ opacity: 0; transform: translateX(15px); }}
        100% {{ opacity: 1; transform: translateX(0); }}
    }}

    .container {{
        display: flex;
        align-items: flex-start;
        gap: 15px;
        padding: 18px;
        background: linear-gradient(145deg, #dcfce7 0%, white 100%);
        border-right: 4px solid #10b981;
        border-radius: 14px;
        flex-direction: row-reverse;
        animation: user-appear 0.4s ease-out;
    }}
    .avatar {{
        min-width: 60px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }}
    .avatar-icon {{
        width: 52px;
        height: 52px;
        background: linear-gradient(145deg, #10b981 0%, #059669 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 26px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }}
    .info {{
        flex: 1;
        text-align: right;
    }}
    .header {{
        display: flex;
        align-items: center;
        gap: 8px;
        justify-content: flex-end;
        margin-bottom: 8px;
    }}
    .name {{
        font-weight: 700;
        color: #10b981;
        font-size: 14px;
    }}
    .badge {{
        background: #10b98115;
        color: #10b981;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: 600;
    }}
    .bubble {{
        display: inline-block;
        text-align: left;
        background: white;
        padding: 14px 18px;
        border-radius: 12px;
        border-top-right-radius: 4px;
        font-size: 14px;
        color: #1f2937;
        line-height: 1.6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    </style>
    </head>
    <body>
    <div class="container">
        <div class="avatar">
            <div class="avatar-icon">✈️</div>
        </div>
        <div class="info">
            <div class="header">
                <span class="name">나 (지원자)</span>
                <span class="badge">{position_kr}</span>
            </div>
            <div class="bubble">{message}</div>
        </div>
    </div>
    </body>
    </html>
    """
    components.html(html, height=130)


# 기존 함수들 (호환성 유지)
def get_animated_passenger_html(*args, **kwargs):
    """호환성을 위한 래퍼 - 직접 render 함수 사용 권장"""
    return ""

def get_animated_crew_html(*args, **kwargs):
    """호환성을 위한 래퍼 - 직접 render 함수 사용 권장"""
    return ""

def get_debate_table_html(*args, **kwargs):
    """호환성을 위한 래퍼 - 직접 render 함수 사용 권장"""
    return ""

def get_animated_debater_html(*args, **kwargs):
    """호환성을 위한 래퍼 - 직접 render 함수 사용 권장"""
    return ""

def get_user_debate_animated_html(*args, **kwargs):
    """호환성을 위한 래퍼 - 직접 render 함수 사용 권장"""
    return ""

def get_cabin_scene_html():
    """호환성을 위한 래퍼"""
    return ""
