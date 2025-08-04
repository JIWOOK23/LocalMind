"""
LocalMind 메인 GUI 애플리케이션 - Claude Desktop 스타일 완성 버전
"""

import streamlit as st
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import warnings
import uuid

# 경고 숨기기
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*encoder_attention_mask.*")

# LocalMind 모듈들 (상대 경로로 수정)
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from main import LocalMindSystem
from database import db
from keyword_analyzer import keyword_analyzer
from function_tools import function_manager

class LocalMindApp:
    """LocalMind 메인 애플리케이션 - Claude Desktop 스타일"""
    
    def __init__(self):
        self.setup_page_config()
        self.load_css()
        self.init_session_state()
        self.ai_engine = self.get_ai_engine()
    
    def setup_page_config(self):
        """페이지 설정"""
        st.set_page_config(
            page_title="LocalMind",
            page_icon="🧠",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
    
    def load_css(self):
        """Claude Desktop 스타일 CSS 로드"""
        st.markdown("""
        <style>
            /* 전체 앱 스타일 */
            .stApp {
                background-color: #f7f7f5;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
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
                width: 280px !important;
            }
            
            /* 헤더 숨기기 */
            header[data-testid="stHeader"] {
                display: none;
            }
            
            /* 사이드바 헤더 */
            .sidebar-header {
                padding: 1.5rem 1rem;
                border-bottom: 1px solid #e5e5e0;
                background: white;
                margin: -1rem -1rem 0 -1rem;
            }
            
            .sidebar-title {
                font-size: 1.2rem;
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
                cursor: pointer !important;
                transition: all 0.2s ease !important;
                font-size: 0.95rem !important;
            }
            
            .new-chat-btn:hover {
                background: #e55a2b !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3) !important;
            }
            
            /* 채팅 세션 목록 */
            .chat-session {
                padding: 0.75rem 1rem;
                margin: 0.25rem 0;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
                color: #5d5d5d;
                font-size: 0.9rem;
                border: none;
                background: transparent;
                width: 100%;
                text-align: left;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .chat-session:hover {
                background: #e8e8e5;
            }
            
            .chat-session.active {
                background: #ff6b35;
                color: white;
            }
            
            .session-title {
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            
            .session-date {
                font-size: 0.75rem;
                opacity: 0.7;
                margin-left: 0.5rem;
            }
            
            /* 메인 채팅 영역 */
            .chat-main {
                height: 100vh;
                display: flex;
                flex-direction: column;
                background: white;
            }
            
            .chat-header {
                padding: 1.5rem 2rem;
                border-bottom: 1px solid #e5e5e0;
                background: white;
                display: flex;
                align-items: center;
                justify-content: center;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            .chat-title {
                font-size: 1.3rem;
                font-weight: 600;
                color: #2d2d2d;
                margin: 0;
            }
            
            /* 채팅 메시지 영역 */
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 2rem;
                max-width: 800px;
                margin: 0 auto;
                width: 100%;
                min-height: 0;
            }
            
            /* 메시지 스타일 */
            .message {
                margin-bottom: 2rem;
                animation: fadeInUp 0.4s ease-out;
            }
            
            @keyframes fadeInUp {
                from { 
                    opacity: 0; 
                    transform: translateY(20px); 
                }
                to { 
                    opacity: 1; 
                    transform: translateY(0); 
                }
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
                padding: 1.2rem 1.5rem;
                border-radius: 20px;
                line-height: 1.6;
                word-wrap: break-word;
                position: relative;
            }
            
            .message-user .message-content {
                background: #ff6b35;
                color: white;
                border-bottom-right-radius: 6px;
                box-shadow: 0 2px 8px rgba(255, 107, 53, 0.2);
            }
            
            .message-assistant .message-content {
                background: #f0f0ee;
                color: #2d2d2d;
                border-bottom-left-radius: 6px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }
            
            .message-time {
                font-size: 0.75rem;
                color: #999;
                margin-top: 0.5rem;
                opacity: 0.8;
            }
            
            /* 입력 영역 */
            .chat-input {
                padding: 1.5rem 2rem 2rem;
                border-top: 1px solid #e5e5e0;
                background: white;
                max-width: 800px;
                margin: 0 auto;
                width: 100%;
                position: sticky;
                bottom: 0;
            }
            
            .input-container {
                position: relative;
                background: #f7f7f5;
                border-radius: 24px;
                border: 1px solid #e5e5e0;
                overflow: hidden;
                transition: all 0.2s ease;
            }
            
            .input-container:focus-within {
                border-color: #ff6b35;
                box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.1);
            }
            
            /* Streamlit 요소 커스터마이징 */
            .stTextArea > div > div > textarea {
                border: none !important;
                background: transparent !important;
                resize: none !important;
                padding: 1.2rem 4rem 1.2rem 1.5rem !important;
                font-size: 1rem !important;
                line-height: 1.5 !important;
                min-height: 24px !important;
                max-height: 200px !important;
                font-family: inherit !important;
            }
            
            .stTextArea > div > div > textarea:focus {
                outline: none !important;
                box-shadow: none !important;
            }
            
            .stTextArea > div > div > textarea::placeholder {
                color: #999 !important;
            }
            
            .stButton > button {
                position: absolute !important;
                right: 12px !important;
                top: 50% !important;
                transform: translateY(-50%) !important;
                background: #ff6b35 !important;
                color: white !important;
                border: none !important;
                border-radius: 50% !important;
                width: 36px !important;
                height: 36px !important;
                padding: 0 !important;
                font-size: 1.1rem !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                transition: all 0.2s ease !important;
                box-shadow: 0 2px 8px rgba(255, 107, 53, 0.3) !important;
            }
            
            .stButton > button:hover {
                background: #e55a2b !important;
                transform: translateY(-50%) scale(1.05) !important;
                box-shadow: 0 4px 12px rgba(255, 107, 53, 0.4) !important;
            }
            
            .stButton > button:disabled {
                background: #ccc !important;
                cursor: not-allowed !important;
                transform: translateY(-50%) !important;
                box-shadow: none !important;
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
                margin-bottom: 1.5rem;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            
            .welcome-title {
                font-size: 2.2rem;
                font-weight: 600;
                margin-bottom: 0.8rem;
                color: #2d2d2d;
                background: linear-gradient(135deg, #ff6b35, #e55a2b);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .welcome-subtitle {
                font-size: 1.1rem;
                margin-bottom: 2.5rem;
                opacity: 0.8;
                line-height: 1.5;
            }
            
            .suggestion-buttons {
                display: flex;
                gap: 1rem;
                flex-wrap: wrap;
                justify-content: center;
                margin-top: 2rem;
            }
            
            .suggestion-btn {
                background: #f0f0ee;
                padding: 1rem 1.5rem;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
                border: 1px solid #e5e5e0;
                font-size: 0.9rem;
                color: #5d5d5d;
            }
            
            .suggestion-btn:hover {
                background: #e8e8e5;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
            
            /* 로딩 상태 */
            .loading-message {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.8rem;
                color: #999;
                font-style: italic;
                padding: 1rem;
                animation: fadeIn 0.3s ease-in;
            }
            
            .loading-dots {
                display: inline-flex;
                gap: 0.2rem;
            }
            
            .loading-dots span {
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: #ff6b35;
                animation: bounce 1.4s infinite ease-in-out both;
            }
            
            .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
            .loading-dots span:nth-child(2) { animation-delay: -0.16s; }
            
            @keyframes bounce {
                0%, 80%, 100% { 
                    transform: scale(0);
                } 40% { 
                    transform: scale(1);
                }
            }
            
            /* 스크롤바 커스터마이징 */
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
            
            /* 파일 업로더 스타일 */
            .stFileUploader > div > div {
                background: transparent;
                border: 1px dashed #e5e5e0;
                border-radius: 8px;
                padding: 1rem;
                text-align: center;
                transition: all 0.2s ease;
            }
            
            .stFileUploader > div > div:hover {
                border-color: #ff6b35;
                background: rgba(255, 107, 53, 0.05);
            }
            
            /* 반응형 디자인 */
            @media (max-width: 768px) {
                .css-1d391kg {
                    width: 100% !important;
                }
                
                .chat-messages {
                    padding: 1rem;
                }
                
                .chat-input {
                    padding: 1rem;
                }
                
                .message-content {
                    max-width: 90%;
                    padding: 1rem 1.2rem;
                }
                
                .welcome-title {
                    font-size: 1.8rem;
                }
                
                .suggestion-buttons {
                    flex-direction: column;
                    align-items: center;
                }
            }
        </style>
        """, unsafe_allow_html=True)
    
    def init_session_state(self):
        """세션 상태 초기화"""
        defaults = {
            'current_session_id': None,
            'chat_sessions': [],
            'is_generating': False,
            'last_user_input': '',
            'message_counter': 0,
            'ui_mode': 'chat',  # chat, settings, documents
            'show_welcome': True
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @st.cache_resource
    def get_ai_engine(_self):
        """AI 엔진 초기화"""
        try:
            return LocalMindSystem()
        except Exception as e:
            st.error(f"AI 엔진 초기화 실패: {str(e)}")
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
            
            # 새 채팅 버튼
            if st.button("+ 새 채팅", key="new_chat", help="새로운 채팅 시작", use_container_width=True):
                self.create_new_session()
            
            # 문서 업로드
            uploaded_file = st.file_uploader(
                "📄 문서 업로드",
                type=['pdf', 'txt', 'md', 'docx'],
                help="PDF, TXT, MD, DOCX 파일 지원",
                key="file_uploader"
            )
            
            if uploaded_file:
                self.handle_file_upload(uploaded_file)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 채팅 세션 목록
            self.render_chat_sessions()
    
    def render_chat_sessions(self):
        """채팅 세션 목록 렌더링"""
        try:
            sessions = db.get_chat_sessions(limit=20)
            st.session_state.chat_sessions = sessions
            
            if sessions:
                st.markdown("**최근 채팅**")
                
                for session in sessions:
                    title = session['title'][:30] + "..." if len(session['title']) > 30 else session['title']
                    created_date = session['created_at'][:5] if session.get('created_at') else ""
                    
                    # 현재 세션 확인
                    is_active = st.session_state.current_session_id == session['id']
                    
                    # 세션 버튼
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        if st.button(
                            title,
                            key=f"session_{session['id']}",
                            help=f"생성: {session['created_at'][:16] if session.get('created_at') else ''}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary"
                        ):
                            self.load_session(session['id'])
                    
                    with col2:
                        if st.button("🗑️", key=f"delete_{session['id']}", help="삭제"):
                            self.delete_session(session['id'])
            
            else:
                st.info("아직 채팅 기록이 없습니다.\n새 채팅을 시작해보세요!")
                
        except Exception as e:
            st.error(f"세션 로딩 오류: {str(e)}")
    
    def render_main_chat(self):
        """메인 채팅 영역 렌더링"""
        # 채팅 헤더
        current_title = "LocalMind"
        if st.session_state.current_session_id:
            sessions = [s for s in st.session_state.chat_sessions 
                       if s['id'] == st.session_state.current_session_id]
            if sessions:
                current_title = sessions[0]['title']
        
        st.markdown(f"""
        <div class="chat-header">
            <h1 class="chat-title">{current_title}</h1>
        </div>
        """, unsafe_allow_html=True)
        
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
        """환영 화면 렌더링"""
        st.markdown("""
        <div class="welcome-screen">
            <div class="welcome-icon">🧠</div>
            <h1 class="welcome-title">오늘 밤 어떤 생각이 드시나요?</h1>
            <p class="welcome-subtitle">
                LocalMind와 함께 문서를 분석하고 대화해보세요<br>
                완전히 로컬에서 실행되는 AI 어시스턴트입니다
            </p>
            
            <div class="suggestion-buttons">
                <div class="suggestion-btn" onclick="fillInput('문서의 주요 내용을 요약해주세요')">
                    📄 문서 요약
                </div>
                <div class="suggestion-btn" onclick="fillInput('핵심 키워드를 추출해주세요')">
                    🔍 키워드 추출
                </div>
                <div class="suggestion-btn" onclick="fillInput('이 문서의 스타일로 새로운 텍스트를 작성해주세요')">
                    ✍️ 문체 모방
                </div>
            </div>
        </div>
        
        <script>
        function fillInput(text) {
            const textarea = document.querySelector('[data-testid="stTextArea"] textarea');
            if (textarea) {
                textarea.value = text;
                textarea.focus();
                // 이벤트 트리거
                const event = new Event('input', { bubbles: true });
                textarea.dispatchEvent(event);
            }
        }
        </script>
        """, unsafe_allow_html=True)
    
    def render_messages(self):
        """메시지 렌더링"""
        try:
            messages = db.get_chat_messages(st.session_state.current_session_id)
            
            if not messages:
                st.markdown("""
                <div style="text-align: center; padding: 3rem; color: #999;">
                    <h3>💬 대화를 시작해보세요!</h3>
                    <p>아래 입력창에 메시지를 입력하거나 제안 버튼을 사용해보세요.</p>
                </div>
                """, unsafe_allow_html=True)
                return
            
            # 메시지 표시
            for message in messages:
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
        
        # 코드 블록 처리 (간단한 버전)
        if '```' in content:
            parts = content.split('```')
            for i in range(1, len(parts), 2):
                parts[i] = f'<pre style="background: rgba(0,0,0,0.05); padding: 0.8rem; border-radius: 8px; overflow-x: auto; margin: 0.5rem 0;"><code>{parts[i]}</code></pre>'
            content = ''.join(parts)
        
        return content
    
    def render_input(self):
        """입력 영역 렌더링"""
        st.markdown('<div class="chat-input">', unsafe_allow_html=True)
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        
        # 입력 폼
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([10, 1])
            
            with col1:
                user_input = st.text_area(
                    "",
                    placeholder="메시지를 입력하세요... (Shift+Enter로 줄바꿈)",
                    height=50,
                    disabled=st.session_state.is_generating,
                    key="chat_input",
                    label_visibility="collapsed"
                )
            
            with col2:
                submit_icon = "⏳" if st.session_state.is_generating else "↑"
                submit = st.form_submit_button(
                    submit_icon,
                    disabled=st.session_state.is_generating
                )
        
        # 로딩 상태 표시
        if st.session_state.is_generating:
            st.markdown("""
            <div class="loading-message">
                <span>LocalMind가 생각하고 있습니다</span>
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 키보드 단축키 지원
        st.markdown("""
        <script>
        document.addEventListener('keydown', function(e) {
            const textarea = document.querySelector('[data-testid="stTextArea"] textarea');
            if (textarea && e.target === textarea) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    const submitBtn = document.querySelector('[data-testid="stFormSubmitButton"] button');
                    if (submitBtn && !submitBtn.disabled) {
                        submitBtn.click();
                    }
                }
            }
        });
        </script>
        """, unsafe_allow_html=True)
        
        # 메시지 처리
        if submit and user_input and user_input.strip():
            self.handle_message(user_input.strip())
    
    def handle_message(self, user_input: str):
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
            
            # AI 응답 생성
            if self.ai_engine:
                try:
                    # Function Call 확인
                    if user_input.startswith('@'):
                        # Function calling 처리
                        try:
                            function_call = function_manager.parse_function_call(user_input)
                            if function_call:
                                result = function_manager.execute_function(
                                    function_call['function_name'],
                                    **function_call['parameters']
                                )
                                response = f"Function 실행 결과:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                            else:
                                response = self.ai_engine.ask_content(user_input)
                        except Exception as e:
                            response = f"Function 실행 오류: {str(e)}\n\n일반 응답으로 전환합니다.\n\n{self.ai_engine.ask_content(user_input)}"
                    else:
                        # 일반 응답
                        response = self.ai_engine.ask_content(user_input)
                    
                    db.add_message(session_id, 'assistant', response)
                    
                except Exception as e:
                    error_response = f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"
                    db.add_message(session_id, 'assistant', error_response)
            else:
                db.add_message(session_id, 'assistant', "AI 엔진이 초기화되지 않았습니다. 페이지를 새로고침해주세요.")
            
        except Exception as e:
            st.error(f"메시지 처리 오류: {str(e)}")
        finally:
            st.session_state.is_generating = False
            time.sleep(0.1)  # UI 안정성을 위한 짧은 지연
            st.rerun()
    
    def create_new_session(self, title: str = None):
        """새 세션 생성"""
        if not title:
            title = f"새 채팅 {datetime.now().strftime('%m/%d %H:%M')}"
        
        try:
            session_id = db.create_chat_session(title)
            st.session_state.current_session_id = session_id
            st.session_state.show_welcome = False
            st.rerun()
        except Exception as e:
            st.error(f"세션 생성 오류: {str(e)}")
    
    def load_session(self, session_id: str):
        """세션 로드"""
        st.session_state.current_session_id = session_id
        st.session_state.is_generating = False
        st.session_state.show_welcome = False
        st.rerun()
    
    def delete_session(self, session_id: str):
        """세션 삭제"""
        try:
            db.delete_chat_session(session_id)
            
            # 현재 세션이 삭제된 세션이면 초기화
            if st.session_state.current_session_id == session_id:
                st.session_state.current_session_id = None
                st.session_state.show_welcome = True
            
            st.success("채팅 세션이 삭제되었습니다!")
            st.rerun()
            
        except Exception as e:
            st.error(f"세션 삭제 오류: {str(e)}")
    
    def handle_file_upload(self, uploaded_file):
        """파일 업로드 처리"""
        try:
            # 파일 저장
            upload_dir = "data"
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 데이터베이스에 문서 정보 저장
            doc_id = db.add_document(
                filename=uploaded_file.name,
                filepath=file_path,
                file_type=uploaded_file.type,
                file_size=uploaded_file.size
            )
            
            st.success(f"✅ {uploaded_file.name} 파일이 업로드되었습니다!")
            
            # 문서 처리 상태 업데이트
            db.update_document_processed(doc_id, True)
            
            # 새 채팅 세션 생성 (문서 기반)
            self.create_new_session(f"{uploaded_file.name} 분석")
            
        except Exception as e:
            st.error(f"❌ 파일 업로드 오류: {str(e)}")
    
    def run(self):
        """애플리케이션 실행"""
        try:
            # 레이아웃 렌더링
            self.render_sidebar()
            self.render_main_chat()
            
        except Exception as e:
            st.error(f"❌ 애플리케이션 실행 오류: {str(e)}")
            st.info("페이지를 새로고침해보세요.")

def main():
    """메인 함수"""
    try:
        app = LocalMindApp()
        app.run()
    except Exception as e:
        st.error(f"❌ 애플리케이션 초기화 오류: {str(e)}")
        st.info("페이지를 새로고침하거나 관리자에게 문의하세요.")

if __name__ == "__main__":
    main()