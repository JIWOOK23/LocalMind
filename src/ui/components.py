"""
LocalMind UI 컴포넌트 모듈
재사용 가능한 UI 컴포넌트들을 정의합니다.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional

class UIComponents:
    """UI 컴포넌트 클래스"""
    
    @staticmethod
    def render_message_bubble(message: Dict, is_user: bool = False):
        """메시지 버블 렌더링"""
        role = "user" if is_user else "assistant"
        content = message.get('content', '')
        timestamp = message.get('timestamp', '')
        
        # 시간 포맷팅
        try:
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%H:%M')
            else:
                formatted_time = ""
        except:
            formatted_time = ""
        
        # HTML 이스케이프
        content = content.replace('<', '&lt;').replace('>', '&gt;')
        content = content.replace('\n', '<br>')
        
        message_class = f"message message-{role}"
        
        st.markdown(f"""
        <div class="{message_class}">
            <div class="message-content">
                {content}
            </div>
            {f'<div class="message-time">{formatted_time}</div>' if formatted_time else ''}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_loading_indicator(message: str = "생각하고 있습니다"):
        """로딩 인디케이터 렌더링"""
        st.markdown(f"""
        <div class="loading-message">
            <span>LocalMind가 {message}</span>
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_suggestion_button(text: str, icon: str = "💡"):
        """제안 버튼 렌더링"""
        return f"""
        <div class="suggestion-btn" onclick="fillInput('{text}')">
            {icon} {text}
        </div>
        """
    
    @staticmethod
    def render_session_item(session: Dict, is_active: bool = False):
        """세션 아이템 렌더링"""
        title = session['title'][:30] + "..." if len(session['title']) > 30 else session['title']
        created_date = session['created_at'][:5] if session.get('created_at') else ""
        
        active_class = "active" if is_active else ""
        
        return f"""
        <div class="chat-session {active_class}">
            <div class="session-title">{title}</div>
            <div class="session-date">{created_date}</div>
        </div>
        """
    
    @staticmethod
    def render_file_upload_area():
        """파일 업로드 영역 렌더링"""
        st.markdown("""
        <div class="file-upload-area">
            <div class="upload-icon">📄</div>
            <div class="upload-text">
                <strong>파일을 드래그하거나 클릭하여 업로드</strong><br>
                PDF, TXT, MD, DOCX 파일 지원
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_empty_state(title: str, subtitle: str, icon: str = "💬"):
        """빈 상태 렌더링"""
        st.markdown(f"""
        <div class="empty-state">
            <div class="empty-icon">{icon}</div>
            <h3 class="empty-title">{title}</h3>
            <p class="empty-subtitle">{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_status_badge(status: str, color: str = "#ff6b35"):
        """상태 배지 렌더링"""
        st.markdown(f"""
        <span class="status-badge" style="background-color: {color};">
            {status}
        </span>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_action_button(text: str, icon: str = "", onclick: str = "", disabled: bool = False):
        """액션 버튼 렌더링"""
        disabled_class = "disabled" if disabled else ""
        onclick_attr = f'onclick="{onclick}"' if onclick and not disabled else ""
        
        return f"""
        <button class="action-btn {disabled_class}" {onclick_attr}>
            {icon} {text}
        </button>
        """