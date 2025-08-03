"""
UI 컴포넌트 시스템 - 재사용 가능한 UI 요소들
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Callable
import json

class UIComponents:
    """UI 컴포넌트 클래스"""
    
    @staticmethod
    def render_message_bubble(message: Dict, is_user: bool = False, show_actions: bool = True):
        """메시지 버블 렌더링"""
        role = message.get('role', 'user' if is_user else 'assistant')
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
        
        # 메시지 클래스 결정
        message_class = f"message message-{role}"
        
        # 메시지 렌더링
        st.markdown(f"""
        <div class="{message_class}">
            <div class="message-content">
                {UIComponents._format_message_content(content)}
            </div>
            {f'<div class="message-time">{formatted_time}</div>' if formatted_time else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # 액션 버튼들
        if show_actions:
            UIComponents._render_message_actions(message)
    
    @staticmethod
    def _format_message_content(content: str) -> str:
        """메시지 내용 포맷팅"""
        if not content:
            return ""
        
        # HTML 이스케이프
        content = content.replace('<', '&lt;').replace('>', '&gt;')
        
        # 줄바꿈 처리
        content = content.replace('\n', '<br>')
        
        # 코드 블록 처리
        if '```' in content:
            parts = content.split('```')
            for i in range(1, len(parts), 2):
                parts[i] = f'<pre class="code-block"><code>{parts[i]}</code></pre>'
            content = ''.join(parts)
        
        # 인라인 코드 처리
        if '`' in content:
            import re
            content = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', content)
        
        return content
    
    @staticmethod
    def _render_message_actions(message: Dict):
        """메시지 액션 버튼들"""
        col1, col2, col3, col4 = st.columns([1, 1, 1, 9])
        
        with col1:
            if st.button("📋", key=f"copy_{message.get('id', 'unknown')}", help="복사"):
                st.session_state.clipboard = message.get('content', '')
                st.success("복사됨!", icon="✅")
        
        with col2:
            if st.button("👍", key=f"like_{message.get('id', 'unknown')}", help="좋아요"):
                UIComponents._handle_message_rating(message.get('id'), True)
        
        with col3:
            if st.button("👎", key=f"dislike_{message.get('id', 'unknown')}", help="싫어요"):
                UIComponents._handle_message_rating(message.get('id'), False)
    
    @staticmethod
    def _handle_message_rating(message_id: str, is_positive: bool):
        """메시지 평가 처리"""
        # 평가 데이터 저장 (향후 학습에 활용)
        rating_data = {
            'message_id': message_id,
            'rating': 'positive' if is_positive else 'negative',
            'timestamp': datetime.now().isoformat()
        }
        
        # 세션 상태에 평가 저장
        if 'message_ratings' not in st.session_state:
            st.session_state.message_ratings = {}
        
        st.session_state.message_ratings[message_id] = rating_data
        
        st.success("피드백이 저장되었습니다!" if is_positive else "피드백이 저장되었습니다.")
    
    @staticmethod
    def render_chat_input(on_submit: Callable[[str], None], disabled: bool = False):
        """채팅 입력 컴포넌트"""
        st.markdown('<div class="chat-input">', unsafe_allow_html=True)
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([10, 1])
            
            with col1:
                user_input = st.text_area(
                    "",
                    placeholder="메시지를 입력하세요...",
                    height=50,
                    disabled=disabled,
                    key="chat_input",
                    label_visibility="collapsed"
                )
            
            with col2:
                submit = st.form_submit_button(
                    "↑",
                    disabled=disabled or not user_input.strip()
                )
            
            # 빠른 액션 버튼들
            UIComponents._render_quick_actions(on_submit, disabled)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 메시지 처리
        if submit and user_input and user_input.strip():
            on_submit(user_input.strip())
    
    @staticmethod
    def _render_quick_actions(on_submit: Callable[[str], None], disabled: bool):
        """빠른 액션 버튼들"""
        st.markdown("**💫 빠른 액션**")
        col1, col2, col3, col4 = st.columns(4)
        
        quick_actions = [
            ("📋 요약", "지금까지의 대화를 요약해주세요."),
            ("🔍 검색", "업로드된 문서에서 중요한 내용을 찾아주세요."),
            ("💡 아이디어", "문서 내용을 바탕으로 새로운 아이디어를 제안해주세요."),
            ("❓ 도움말", "LocalMind 사용법을 알려주세요.")
        ]
        
        for i, (label, prompt) in enumerate(quick_actions):
            with [col1, col2, col3, col4][i]:
                if st.form_submit_button(label, disabled=disabled):
                    on_submit(prompt)
    
    @staticmethod
    def render_sidebar_session_list(sessions: List[Dict], current_session_id: str, 
                                  on_select: Callable[[str], None], 
                                  on_delete: Callable[[str], None]):
        """사이드바 세션 목록"""
        if not sessions:
            st.info("아직 채팅 세션이 없습니다.")
            return
        
        st.markdown("**최근 채팅**")
        
        for session in sessions:
            title = session['title'][:30] + "..." if len(session['title']) > 30 else session['title']
            is_current = current_session_id == session['id']
            
            # 세션 컨테이너
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    if st.button(
                        title,
                        key=f"session_{session['id']}",
                        help=f"생성: {session.get('created_at', '')[:10]}",
                        use_container_width=True,
                        type="primary" if is_current else "secondary"
                    ):
                        on_select(session['id'])
                
                with col2:
                    if st.button("🗑️", key=f"delete_{session['id']}", help="삭제"):
                        UIComponents._handle_session_delete(session, on_delete)
    
    @staticmethod
    def _handle_session_delete(session: Dict, on_delete: Callable[[str], None]):
        """세션 삭제 처리"""
        session_id = session['id']
        confirm_key = f"confirm_delete_{session_id}"
        
        if st.session_state.get(confirm_key, False):
            on_delete(session_id)
            if confirm_key in st.session_state:
                del st.session_state[confirm_key]
        else:
            st.session_state[confirm_key] = True
            st.warning(f"'{session['title'][:20]}...' 세션을 삭제하시겠습니까?")
            st.rerun()
    
    @staticmethod
    def render_document_card(document: Dict, on_process: Callable[[str], None] = None,
                           on_delete: Callable[[str], None] = None):
        """문서 카드 렌더링"""
        with st.expander(f"📄 {document['filename']}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**크기:** {UIComponents._format_file_size(document['file_size'])}")
                st.write(f"**타입:** {document['file_type']}")
                st.write(f"**업로드:** {document['upload_date'][:10]}")
            
            with col2:
                status = "✅ 처리됨" if document['processed'] else "⏳ 대기중"
                st.write(f"**상태:** {status}")
                
                if document.get('chunk_count'):
                    st.write(f"**청크 수:** {document['chunk_count']}")
                
                if document.get('processing_time'):
                    st.write(f"**처리 시간:** {document['processing_time']:.2f}초")
            
            # 액션 버튼들
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if not document['processed'] and on_process:
                    if st.button("🔄 처리", key=f"process_{document['id']}"):
                        on_process(document['id'])
            
            with col2:
                if st.button("📊 분석", key=f"analyze_{document['id']}"):
                    UIComponents._show_document_analysis(document)
            
            with col3:
                if on_delete:
                    if st.button("🗑️ 삭제", key=f"delete_doc_{document['id']}"):
                        on_delete(document['id'])
    
    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """파일 크기 포맷팅"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    @staticmethod
    def _show_document_analysis(document: Dict):
        """문서 분석 정보 표시"""
        st.info("문서 분석 기능은 개발 중입니다.")
    
    @staticmethod
    def render_loading_spinner(message: str = "처리 중..."):
        """로딩 스피너"""
        st.markdown(f"""
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <span style="margin-left: 1rem;">{message}</span>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_status_indicator(status: str, message: str = ""):
        """상태 표시기"""
        status_class = {
            'online': 'status-online',
            'thinking': 'status-thinking',
            'offline': 'status-offline',
            'error': 'status-offline'
        }.get(status, 'status-online')
        
        status_text = {
            'online': '준비됨',
            'thinking': '생각 중...',
            'offline': '오프라인',
            'error': '오류'
        }.get(status, '알 수 없음')
        
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin: 0.5rem 0;">
            <span class="status-indicator {status_class}"></span>
            <span>{status_text}</span>
            {f"<span style='margin-left: 0.5rem; color: #666;'>| {message}</span>" if message else ""}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_statistics_card(title: str, stats: Dict):
        """통계 카드"""
        st.markdown(f"""
        <div class="stats-card">
            <h3>{title}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 통계 메트릭들
        cols = st.columns(len(stats))
        for i, (key, value) in enumerate(stats.items()):
            with cols[i]:
                st.metric(key, value)
    
    @staticmethod
    def render_welcome_screen():
        """환영 화면"""
        st.markdown("""
        <div class="welcome-screen">
            <div class="welcome-icon">🧠</div>
            <h1 class="welcome-title">오늘 밤 어떤 생각이 드시나요?</h1>
            <p class="welcome-subtitle">LocalMind와 함께 문서를 분석하고 대화해보세요</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_error_message(error: str, details: str = None):
        """에러 메시지"""
        st.error(f"❌ {error}")
        if details:
            with st.expander("자세한 정보"):
                st.code(details)
    
    @staticmethod
    def render_success_message(message: str):
        """성공 메시지"""
        st.success(f"✅ {message}")
    
    @staticmethod
    def render_info_message(message: str):
        """정보 메시지"""
        st.info(f"💡 {message}")
    
    @staticmethod
    def render_warning_message(message: str):
        """경고 메시지"""
        st.warning(f"⚠️ {message}")

# CSS 스타일 추가
ADDITIONAL_CSS = """
<style>
    /* 코드 블록 스타일 */
    .code-block {
        background: rgba(0, 0, 0, 0.05);
        padding: 1rem;
        border-radius: 8px;
        overflow-x: auto;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        margin: 0.5rem 0;
    }
    
    .inline-code {
        background: rgba(0, 0, 0, 0.1);
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
    }
    
    /* 통계 카드 */
    .stats-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    .stats-card h3 {
        margin: 0 0 1rem 0;
        color: #2d2d2d;
        font-size: 1.1rem;
    }
    
    /* 로딩 컨테이너 */
    .loading-container {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        color: #666;
    }
    
    .loading-spinner {
        width: 20px;
        height: 20px;
        border: 2px solid rgba(255, 107, 53, 0.3);
        border-top: 2px solid #ff6b35;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
"""