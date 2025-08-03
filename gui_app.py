# gui_app.py
"""
LocalMind GUI - Claude Desktop 스타일 + 모든 기존 기능 포함
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import time
from typing import List, Dict, Optional
import warnings

# 경고 숨기기
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*encoder_attention_mask.*")

# LocalMind 모듈들
from main import LocalMindSystem
from database import db
from keyword_analyzer import keyword_analyzer
from function_tools import function_manager

# Streamlit 설정
st.set_page_config(
    page_title="LocalMind",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Claude 스타일 CSS (기능 포함)
st.markdown("""
<style>
    /* 전체 앱 스타일 */
    .stApp {
        background-color: #f7f7f5;
    }
    
    /* 메인 컨테이너 */
    .main .block-container {
        padding: 0;
        max-width: 100%;
    }
    
    /* 사이드바 스타일 */
    .css-1d391kg {
        background-color: #f0f0ee;
        border-right: 1px solid #e5e5e0;
        width: 320px !important;
    }
    
    /* 헤더 숨기기 */
    header[data-testid="stHeader"] {
        display: none;
    }
    
    /* 사이드바 헤더 */
    .sidebar-header {
        padding: 1rem;
        border-bottom: 1px solid #e5e5e0;
        background: white;
        margin: -1rem -1rem 0 -1rem;
    }
    
    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2d2d2d;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* 새 채팅 버튼 */
    .new-chat-btn {
        background: #ff6b35 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 500 !important;
        width: 100% !important;
        margin: 1rem 0 !important;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .new-chat-btn:hover {
        background: #e55a2b !important;
        transform: translateY(-1px);
    }
    
    /* 채팅 세션 목록 */
    .chat-session {
        padding: 0.75rem 1rem !important;
        margin: 0.25rem 0 !important;
        border-radius: 8px !important;
        cursor: pointer;
        transition: all 0.2s ease;
        color: #5d5d5d !important;
        font-size: 0.9rem !important;
        border: none !important;
        background: transparent !important;
        width: 100% !important;
        text-align: left !important;
    }
    
    .chat-session:hover {
        background: #e8e8e5 !important;
    }
    
    .chat-session.active {
        background: #ff6b35 !important;
        color: white !important;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #f0f0ee;
        border-radius: 8px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        border: none;
        color: #5d5d5d;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: white;
        color: #2d2d2d;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* 메인 채팅 영역 */
    .chat-main {
        height: 100vh;
        display: flex;
        flex-direction: column;
        background: white;
    }
    
    .chat-header {
        padding: 1rem 2rem;
        border-bottom: 1px solid #e5e5e0;
        background: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .chat-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2d2d2d;
        margin: 0;
    }
    
    .chat-actions {
        display: flex;
        gap: 0.5rem;
    }
    
    /* 채팅 메시지 영역 */
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 2rem;
        max-width: 800px;
        margin: 0 auto;
        width: 100%;
    }
    
    /* 메시지 스타일 */
    .message {
        margin-bottom: 2rem;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .message-user {
        text-align: right;
    }
    
    .message-assistant {
        text-align: left;
    }
    
    .message-content {
        display: inline-block;
        max-width: 80%;
        padding: 1rem 1.5rem;
        border-radius: 18px;
        line-height: 1.5;
        word-wrap: break-word;
        position: relative;
    }
    
    .message-user .message-content {
        background: #ff6b35;
        color: white;
        border-bottom-right-radius: 4px;
    }
    
    .message-assistant .message-content {
        background: #f0f0ee;
        color: #2d2d2d;
        border-bottom-left-radius: 4px;
    }
    
    .message-time {
        font-size: 0.75rem;
        color: #999;
        margin-top: 0.5rem;
    }
    
    .message-actions {
        display: flex;
        gap: 0.25rem;
        margin-top: 0.5rem;
        opacity: 0;
        transition: opacity 0.2s ease;
    }
    
    .message:hover .message-actions {
        opacity: 1;
    }
    
    .message-action-btn {
        background: rgba(0,0,0,0.1) !important;
        color: #666 !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.25rem 0.5rem !important;
        font-size: 0.75rem !important;
        cursor: pointer;
    }
    
    .message-action-btn:hover {
        background: rgba(0,0,0,0.2) !important;
    }
    
    /* 입력 영역 */
    .chat-input {
        padding: 1.5rem 2rem;
        border-top: 1px solid #e5e5e0;
        background: white;
        max-width: 800px;
        margin: 0 auto;
        width: 100%;
    }
    
    .input-container {
        position: relative;
        background: #f7f7f5;
        border-radius: 24px;
        border: 1px solid #e5e5e0;
        overflow: hidden;
    }
    
    .input-container:focus-within {
        border-color: #ff6b35;
        box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.1);
    }
    
    /* Streamlit 요소 스타일링 */
    .stTextArea > div > div > textarea {
        border: none !important;
        background: transparent !important;
        resize: none !important;
        padding: 1rem 3rem 1rem 1.5rem !important;
        font-size: 1rem !important;
        line-height: 1.5 !important;
        min-height: 24px !important;
        max-height: 200px !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    
    .send-button {
        position: absolute;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        background: #ff6b35 !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        width: 32px !important;
        height: 32px !important;
        padding: 0 !important;
        font-size: 1rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .send-button:hover {
        background: #e55a2b !important;
        transform: translateY(-50%) scale(1.05) !important;
    }
    
    /* 환영 화면 */
    .welcome-screen {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 60vh;
        text-align: center;
        color: #5d5d5d;
    }
    
    .welcome-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    
    .welcome-title {
        font-size: 2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #2d2d2d;
    }
    
    .welcome-subtitle {
        font-size: 1.1rem;
        margin-bottom: 2rem;
        opacity: 0.8;
    }
    
    /* 로딩 상태 */
    .loading-message {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #999;
        font-style: italic;
        padding: 1rem;
        text-align: center;
    }
    
    .loading-dots {
        animation: loading 1.5s infinite;
    }
    
    @keyframes loading {
        0%, 20% { opacity: 0; }
        50% { opacity: 1; }
        100% { opacity: 0; }
    }
    
    /* 문서 카드 */
    .document-card {
        background: white;
        border: 1px solid #e5e5e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        transition: all 0.2s ease;
    }
    
    .document-card:hover {
        border-color: #ff6b35;
        box-shadow: 0 2px 8px rgba(255, 107, 53, 0.1);
    }
    
    .document-title {
        font-weight: 600;
        color: #2d2d2d;
        margin-bottom: 0.5rem;
    }
    
    .document-meta {
        font-size: 0.8rem;
        color: #999;
        display: flex;
        justify-content: space-between;
    }
    
    /* 통계 카드 */
    .stat-card {
        background: white;
        border: 1px solid #e5e5e0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .stat-number {
        font-size: 1.5rem;
        font-weight: 600;
        color: #ff6b35;
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.25rem;
    }
    
    /* 스크롤바 */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #d0d0ce;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #b0b0ae;
    }
    
    /* Function Call 스타일 */
    .function-call {
        background: rgba(255, 107, 53, 0.1);
        border: 1px solid rgba(255, 107, 53, 0.2);
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        font-family: monospace;
        font-size: 0.85rem;
        color: #2d2d2d;
    }
</style>
""", unsafe_allow_html=True)

class LocalMindGUI:
    """LocalMind GUI - Claude 스타일 + 모든 기능"""
    
    def __init__(self):
        self.init_session_state()
        self.localmind = self.get_localmind_system()
    
    def init_session_state(self):
        """세션 상태 초기화"""
        defaults = {
            'current_session_id': None,
            'chat_sessions': [],
            'is_generating': False,
            'last_user_input': '',
            'message_counter': 0,
            'show_session_settings': False,
            'settings': {
                'auto_categorize': True,
                'enable_functions': True,
                'max_keywords': 10,
                'response_length': '보통',
                'language': '한국어',
                'theme': '라이트'
            }
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @st.cache_resource
    def get_localmind_system(_self):
        """LocalMind 시스템 초기화"""
        try:
            return LocalMindSystem()
        except Exception as e:
            st.error(f"시스템 초기화 실패: {str(e)}")
            return None
    
    def render_sidebar(self):
        """사이드바 렌더링"""
        with st.sidebar:
            # 헤더
            st.markdown("""
            <div class="sidebar-header">
                <div class="sidebar-title">
                    🧠 LocalMind
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 탭으로 구분
            tab1, tab2, tab3 = st.tabs(["💬 채팅", "📁 문서", "⚙️ 설정"])
            
            with tab1:
                self.render_chat_tab()
            
            with tab2:
                self.render_document_tab()
            
            with tab3:
                self.render_settings_tab()
    
    def render_chat_tab(self):
        """채팅 탭"""
        # 새 채팅 버튼
        if st.button("+ 새 채팅", key="new_chat", help="새로운 채팅 시작", use_container_width=True):
            self.create_new_session()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 채팅 세션 목록
        sessions = db.get_chat_sessions(limit=20)
        st.session_state.chat_sessions = sessions
        
        if sessions:
            st.markdown("**최근 채팅**")
            for session in sessions:
                title = session['title'][:25] + "..." if len(session['title']) > 25 else session['title']
                created_date = session['created_at'][:10] if session['created_at'] else ""
                
                # 현재 세션 확인
                is_active = st.session_state.current_session_id == session['id']
                
                col1, col2, col3 = st.columns([6, 1, 1])
                
                with col1:
                    if st.button(
                        f"💬 {title}",
                        key=f"session_{session['id']}",
                        help=f"생성: {created_date}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary"
                    ):
                        self.load_session(session['id'])
                
                with col2:
                    if st.button("ℹ️", key=f"info_{session['id']}", help="정보"):
                        self.show_session_info(session)
                
                with col3:
                    if st.button("🗑️", key=f"delete_{session['id']}", help="삭제"):
                        self.delete_session_with_confirm(session['id'])
        
        # 통계
        st.markdown("---")
        st.markdown("**📊 통계**")
        stats = db.get_chat_statistics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats['total_sessions']}</div>
                <div class="stat-label">총 세션</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats['total_messages']}</div>
                <div class="stat-label">총 메시지</div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_document_tab(self):
        """문서 탭"""
        st.markdown("**📁 문서 관리**")
        
        # 파일 업로드
        uploaded_file = st.file_uploader(
            "문서 업로드",
            type=['pdf', 'txt', 'md', 'docx'],
            help="PDF, TXT, MD, DOCX 파일을 업로드할 수 있습니다.",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            self.handle_file_upload(uploaded_file)
        
        # 업로드된 문서 목록
        documents = db.get_documents()
        
        if documents:
            st.markdown(f"**업로드된 문서 ({len(documents)}개)**")
            
            # 문서 검색
            search_query = st.text_input(
                "문서 검색", 
                placeholder="파일명으로 검색...",
                label_visibility="collapsed"
            )
            
            # 필터링
            filtered_docs = documents
            if search_query:
                filtered_docs = [
                    doc for doc in documents 
                    if search_query.lower() in doc['filename'].lower()
                ]
            
            # 문서 목록 표시
            for doc in filtered_docs[:10]:  # 최대 10개만 표시
                st.markdown(f"""
                <div class="document-card">
                    <div class="document-title">📄 {doc['filename']}</div>
                    <div class="document-meta">
                        <span>{self.format_file_size(doc['file_size'])}</span>
                        <span>{doc['upload_date'][:10]}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 문서 액션
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("💬", key=f"chat_{doc['id']}", help="채팅"):
                        self.create_document_chat(doc['filename'])
                with col2:
                    if st.button("🔍", key=f"analyze_{doc['id']}", help="분석"):
                        st.info("문서 분석 기능은 개발 중입니다.")
                with col3:
                    if st.button("🗑️", key=f"del_doc_{doc['id']}", help="삭제"):
                        self.delete_document(doc['id'])
        else:
            st.info("아직 업로드된 문서가 없습니다.")
    
    def render_settings_tab(self):
        """설정 탭"""
        st.markdown("**⚙️ 설정**")
        
        # 자동 카테고리 분류
        auto_categorize = st.checkbox(
            "자동 카테고리 분류", 
            value=st.session_state.settings['auto_categorize']
        )
        
        # Function Calling 활성화
        enable_functions = st.checkbox(
            "Function Calling 활성화", 
            value=st.session_state.settings['enable_functions']
        )
        
        # 키워드 추출 개수
        max_keywords = st.slider(
            "키워드 추출 개수", 
            5, 20, 
            st.session_state.settings['max_keywords']
        )
        
        # 응답 길이 설정
        response_length = st.selectbox(
            "기본 응답 길이",
            ["짧게", "보통", "길게"],
            index=["짧게", "보통", "길게"].index(st.session_state.settings['response_length'])
        )
        
        # 언어 설정
        language = st.selectbox(
            "언어 설정",
            ["한국어", "English"],
            index=["한국어", "English"].index(st.session_state.settings['language'])
        )
        
        # 설정 저장
        st.session_state.settings.update({
            'auto_categorize': auto_categorize,
            'enable_functions': enable_functions,
            'max_keywords': max_keywords,
            'response_length': response_length,
            'language': language
        })
        
        # 설정 초기화 버튼
        if st.button("🔄 설정 초기화", use_container_width=True):
            st.session_state.settings = {
                'auto_categorize': True,
                'enable_functions': True,
                'max_keywords': 10,
                'response_length': '보통',
                'language': '한국어',
                'theme': '라이트'
            }
            st.success("설정이 초기화되었습니다!")
            st.rerun()
    
    def render_main_chat(self):
        """메인 채팅 영역"""
        # 채팅 헤더
        current_title = "LocalMind"
        if st.session_state.current_session_id:
            sessions = [s for s in st.session_state.chat_sessions 
                       if s['id'] == st.session_state.current_session_id]
            if sessions:
                current_title = sessions[0]['title']
        
        # 헤더와 액션 버튼
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"""
            <div class="chat-header">
                <h1 class="chat-title">{current_title}</h1>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.session_state.current_session_id:
                if st.button("📤", help="내보내기"):
                    self.export_session()
        
        # 메시지 영역
        st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
        
        if st.session_state.current_session_id:
            self.render_messages()
        else:
            self.render_welcome()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 입력 영역
        self.render_input()
    
    def render_welcome(self):
        """환영 화면"""
        st.markdown("""
        <div class="welcome-screen">
            <div class="welcome-icon">🧠</div>
            <h1 class="welcome-title">오늘 밤 어떤 생각이 드시나요?</h1>
            <p class="welcome-subtitle">LocalMind와 함께 문서를 분석하고 대화해보세요</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_messages(self):
        """메시지 렌더링"""
        try:
            messages = db.get_chat_messages(st.session_state.current_session_id)
            
            for i, message in enumerate(messages):
                if not message or 'role' not in message:
                    continue
                
                role = message['role']
                content = message['content']
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
                
                # 메시지 렌더링
                message_class = f"message message-{role}"
                
                st.markdown(f"""
                <div class="{message_class}">
                    <div class="message-content">
                        {self.format_content(content)}
                    </div>
                    {f'<div class="message-time">{formatted_time}</div>' if formatted_time else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Function Call 표시
                if message.get('function_call'):
                    function_call = message['function_call']
                    st.markdown(f"""
                    <div class="function-call">
                        <strong>🔧 Function Call:</strong> {function_call.get('name', 'Unknown')}<br>
                        <strong>Parameters:</strong> {json.dumps(function_call.get('parameters', {}), ensure_ascii=False, indent=2)}
                    </div>
                    """, unsafe_allow_html=True)
                
                # 메시지 액션 버튼
                if role == 'assistant':
                    col1, col2, col3, col4 = st.columns([1, 1, 1, 7])
                    with col1:
                        if st.button("📋", key=f"copy_{i}", help="복사"):
                            st.session_state.clipboard = content
                            st.success("복사됨!")
                    with col2:
                        if st.button("🔄", key=f"regen_{i}", help="재생성"):
                            self.regenerate_response(i)
                    with col3:
                        if st.button("👍", key=f"like_{i}", help="좋아요"):
                            st.success("피드백 감사합니다!")
                
        except Exception as e:
            st.error(f"메시지 로딩 오류: {str(e)}")
    
    def format_content(self, content: str) -> str:
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
                parts[i] = f'<pre style="background: rgba(0,0,0,0.05); padding: 0.5rem; border-radius: 5px; overflow-x: auto;"><code>{parts[i]}</code></pre>'
            content = ''.join(parts)
        
        return content
    
    def render_input(self):
        """입력 영역"""
        st.markdown('<div class="chat-input">', unsafe_allow_html=True)
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        
        # 입력 폼
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([10, 1])
            
            with col1:
                user_input = st.text_area(
                    "메시지 입력",
                    placeholder="메시지를 입력하세요...",
                    height=50,
                    disabled=st.session_state.is_generating,
                    key="chat_input",
                    label_visibility="collapsed"
                )
            
            with col2:
                submit = st.form_submit_button(
                    "↑",
                    disabled=st.session_state.is_generating
                )
            
            # 고급 옵션
            with st.expander("🔧 고급 옵션", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    use_document_context = st.checkbox("📄 문서 컨텍스트 사용", value=True)
                
                with col2:
                    response_style = st.selectbox(
                        "✍️ 응답 스타일",
                        ["일반", "상세", "간결", "문체모방"],
                        index=0
                    )
                
                with col3:
                    temperature = st.slider("🌡️ 창의성", 0.0, 1.0, 0.1, 0.1)
        
        # 로딩 상태 표시
        if st.session_state.is_generating:
            st.markdown("""
            <div class="loading-message">
                <span>LocalMind가 생각하고 있습니다</span>
                <span class="loading-dots">...</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 메시지 처리
        if submit and user_input and user_input.strip():
            self.handle_message(user_input.strip(), use_document_context, response_style)
    
    def handle_message(self, user_input: str, use_document_context: bool = True, response_style: str = "일반"):
        """메시지 처리"""
        if st.session_state.is_generating:
            return
        
        if user_input == st.session_state.last_user_input:
            return
        
        try:
            st.session_state.is_generating = True
            st.session_state.last_user_input = user_input
            
            # 세션 생성
            if not st.session_state.current_session_id:
                self.create_new_session(user_input[:50])
            
            session_id = st.session_state.current_session_id
            
            # 사용자 메시지 저장
            db.add_message(session_id, 'user', user_input)
            
            # Function Call 확인
            function_call = None
            if st.session_state.settings.get('enable_functions', True):
                try:
                    function_call = function_manager.parse_function_call(user_input)
                except:
                    pass
            
            # AI 응답 생성
            if self.localmind:
                if function_call:
                    # Function Call 실행
                    try:
                        result = function_manager.execute_function(
                            function_call['function_name'],
                            **function_call['parameters']
                        )
                        
                        context = f"Function Call 결과: {json.dumps(result, ensure_ascii=False)}"
                        prompt = f"사용자 요청: {user_input}\n\n{context}\n\n위 정보를 바탕으로 사용자에게 도움이 되는 응답을 생성해주세요."
                        
                        if response_style == "문체모방":
                            response = self.localmind.mimic_style(prompt)
                        else:
                            response = self.localmind.ask_content(prompt)
                        
                        db.add_message(
                            session_id, 
                            'assistant', 
                            response,
                            function_call=function_call,
                            metadata={'function_result': result}
                        )
                    except Exception as e:
                        response = f"Function Call 실행 중 오류가 발생했습니다: {str(e)}"
                        db.add_message(session_id, 'assistant', response)
                else:
                    # 일반 응답 생성
                    if response_style == "문체모방":
                        response = self.localmind.mimic_style(user_input)
                    else:
                        response = self.localmind.ask_content(user_input)
                    
                    db.add_message(session_id, 'assistant', response)
                
                # 자동 카테고리 분류
                if st.session_state.settings.get('auto_categorize', True):
                    try:
                        self.update_session_analysis(session_id)
                    except:
                        pass
            else:
                db.add_message(session_id, 'assistant', "죄송합니다. 시스템 오류가 발생했습니다.")
            
        except Exception as e:
            st.error(f"오류: {str(e)}")
        finally:
            st.session_state.is_generating = False
            st.rerun()
    
    # 유틸리티 메서드들
    def create_new_session(self, title: str = None):
        """새 세션 생성"""
        if not title:
            title = f"새 채팅 {datetime.now().strftime('%m/%d %H:%M')}"
        
        try:
            session_id = db.create_chat_session(title)
            st.session_state.current_session_id = session_id
            st.rerun()
        except Exception as e:
            st.error(f"세션 생성 오류: {str(e)}")
    
    def load_session(self, session_id: str):
        """세션 로드"""
        st.session_state.current_session_id = session_id
        st.session_state.is_generating = False
        st.rerun()
    
    def delete_session_with_confirm(self, session_id: str):
        """세션 삭제 (확인 포함)"""
        if st.session_state.get(f"confirm_delete_{session_id}", False):
            try:
                db.delete_chat_session(session_id)
                if st.session_state.current_session_id == session_id:
                    st.session_state.current_session_id = None
                st.session_state[f"confirm_delete_{session_id}"] = False
                st.success("세션이 삭제되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"삭제 오류: {str(e)}")
        else:
            st.session_state[f"confirm_delete_{session_id}"] = True
            st.warning("다시 클릭하여 삭제를 확인하세요.")
    
    def show_session_info(self, session):
        """세션 정보 표시"""
        st.info(f"""
        **세션 정보**
        - 제목: {session['title']}
        - 생성일: {session['created_at'][:19] if session.get('created_at') else ''}
        - 카테고리: {session.get('category', '없음')}
        """)
    
    def handle_file_upload(self, uploaded_file):
        """파일 업로드 처리"""
        try:
            upload_dir = "data"
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            doc_id = db.add_document(
                filename=uploaded_file.name,
                filepath=file_path,
                file_type=uploaded_file.type,
                file_size=uploaded_file.size
            )
            
            st.success(f"✅ {uploaded_file.name} 파일이 업로드되었습니다!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 파일 업로드 중 오류: {str(e)}")
    
    def create_document_chat(self, filename: str):
        """문서 기반 채팅 생성"""
        title = f"{filename} 관련 채팅"
        self.create_new_session(title)
    
    def delete_document(self, doc_id: str):
        """문서 삭제"""
        try:
            db.delete_document(doc_id)
            st.success("문서가 삭제되었습니다!")
            st.rerun()
        except Exception as e:
            st.error(f"문서 삭제 오류: {str(e)}")
    
    def format_file_size(self, size_bytes: int) -> str:
        """파일 크기 포맷팅"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    def regenerate_response(self, message_index: int):
        """응답 재생성"""
        if st.session_state.is_generating:
            st.warning("이미 응답을 생성 중입니다.")
            return
        
        try:
            messages = db.get_chat_messages(st.session_state.current_session_id)
            if message_index > 0:
                user_message = None
                for i in range(message_index, -1, -1):
                    if messages[i]['role'] == 'user':
                        user_message = messages[i]['content']
                        break
                
                if user_message:
                    self.handle_message(user_message)
                else:
                    st.warning("재생성할 사용자 메시지를 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"재생성 오류: {str(e)}")
    
    def export_session(self):
        """세션 내보내기"""
        if not st.session_state.current_session_id:
            st.warning("내보낼 세션이 없습니다.")
            return
        
        try:
            messages = db.get_chat_messages(st.session_state.current_session_id)
            session_info = next((s for s in st.session_state.chat_sessions 
                               if s['id'] == st.session_state.current_session_id), None)
            
            if messages and session_info:
                export_dir = "exports"
                os.makedirs(export_dir, exist_ok=True)
                
                filename = f"{session_info['title']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                filepath = os.path.join(export_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"채팅 세션: {session_info['title']}\n")
                    f.write(f"생성일: {session_info['created_at']}\n")
                    f.write("="*50 + "\n\n")
                    
                    for msg in messages:
                        role_name = "사용자" if msg['role'] == 'user' else "LocalMind"
                        f.write(f"[{msg['timestamp']}] {role_name}:\n")
                        f.write(f"{msg['content']}\n\n")
                
                st.success(f"✅ 채팅이 {filepath}로 내보내졌습니다!")
            else:
                st.warning("내보낼 데이터가 없습니다.")
                
        except Exception as e:
            st.error(f"내보내기 오류: {str(e)}")
    
    def update_session_analysis(self, session_id: str):
        """세션 분석 업데이트"""
        try:
            messages = db.get_chat_messages(session_id)
            if messages:
                analysis = keyword_analyzer.analyze_conversation(messages)
                if analysis.get('keywords'):
                    db.update_session_keywords(session_id, analysis['keywords'])
        except:
            pass
    
    def run(self):
        """앱 실행"""
        # 레이아웃
        self.render_sidebar()
        self.render_main_chat()

def main():
    """메인 함수"""
    try:
        gui = LocalMindGUI()
        gui.run()
    except Exception as e:
        st.error(f"앱 초기화 오류: {str(e)}")

if __name__ == "__main__":
    main()