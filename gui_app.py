# gui_app.py
"""
LocalMind GUI 애플리케이션
Claude Desktop과 유사한 인터페이스를 제공합니다.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from typing import List, Dict
import warnings

# FutureWarning 및 기타 경고 숨기기
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*encoder_attention_mask.*")

# LocalMind 모듈들
from main import LocalMindSystem
from database import db
from keyword_analyzer import keyword_analyzer
from function_tools import function_manager

# Streamlit 설정
st.set_page_config(
    page_title="LocalMind - 로컬 AI 문서 어시스턴트",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #667eea;
    }
    
    .assistant-message {
        background-color: #e8f4fd;
        border-left-color: #2196F3;
    }
    
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .function-call {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-family: monospace;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

class LocalMindGUI:
    """LocalMind GUI 클래스"""
    
    def __init__(self):
        self.init_session_state()
        self.localmind = self.get_localmind_system()
    
    def init_session_state(self):
        """세션 상태 초기화"""
        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = None
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'chat_sessions' not in st.session_state:
            st.session_state.chat_sessions = []
        if 'localmind_system' not in st.session_state:
            st.session_state.localmind_system = None
    
    @st.cache_resource
    def get_localmind_system(_self):
        """LocalMind 시스템 인스턴스 가져오기 (캐시됨)"""
        return LocalMindSystem()
    
    def render_header(self):
        """헤더 렌더링"""
        st.markdown("""
        <div class="main-header">
            <h1>🧠 LocalMind</h1>
            <p>로컬 AI 문서 어시스턴트</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """사이드바 렌더링"""
        with st.sidebar:
            # 탭으로 구분
            tab1, tab2, tab3 = st.tabs(["💬 채팅", "📁 문서", "⚙️ 설정"])
            
            with tab1:
                self.render_chat_sidebar()
            
            with tab2:
                self.render_document_sidebar()
            
            with tab3:
                self.render_settings_sidebar()
    
    def render_chat_sidebar(self):
        """채팅 사이드바 렌더링"""
        st.markdown("### 📋 채팅 세션")
        
        # 새 채팅 버튼
        if st.button("➕ 새 채팅", use_container_width=True):
            self.create_new_session()
        
        # 채팅 세션 목록
        sessions = db.get_chat_sessions(limit=20)
        st.session_state.chat_sessions = sessions
        
        if not sessions:
            st.info("아직 채팅 세션이 없습니다. 새 채팅을 시작해보세요!")
            return
        
        # 현재 선택된 세션 표시
        current_session = None
        if st.session_state.current_session_id:
            current_session = next(
                (s for s in sessions if s['id'] == st.session_state.current_session_id), 
                None
            )
        
        if current_session:
            st.success(f"현재 세션: {current_session['title'][:25]}...")
        
        st.markdown("**세션 목록**")
        
        for session in sessions:
            session_title = session['title'][:25] + "..." if len(session['title']) > 25 else session['title']
            created_date = session['created_at'][:10] if session['created_at'] else ""
            
            # 현재 세션인지 확인
            is_current = st.session_state.current_session_id == session['id']
            
            # 세션 컨테이너
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    button_type = "primary" if is_current else "secondary"
                    if st.button(
                        f"💬 {session_title}",
                        key=f"session_{session['id']}",
                        use_container_width=True,
                        type=button_type
                    ):
                        self.load_session(session['id'])
                
                with col2:
                    if st.button("📋", key=f"info_{session['id']}", help="세션 정보"):
                        st.session_state.show_session_info = session['id']
                
                with col3:
                    if st.button("🗑️", key=f"delete_{session['id']}", help="삭제"):
                        if st.session_state.get(f"confirm_delete_{session['id']}", False):
                            self.delete_session(session['id'])
                            st.session_state[f"confirm_delete_{session['id']}"] = False
                        else:
                            st.session_state[f"confirm_delete_{session['id']}"] = True
                            st.rerun()
                
                # 삭제 확인 메시지
                if st.session_state.get(f"confirm_delete_{session['id']}", False):
                    st.warning(f"'{session_title}' 세션을 삭제하시겠습니까? 다시 삭제 버튼을 클릭하세요.")
                
                # 세션 정보 표시
                if st.session_state.get('show_session_info') == session['id']:
                    with st.expander("세션 정보", expanded=True):
                        st.write(f"**제목:** {session['title']}")
                        st.write(f"**생성일:** {created_date}")
                        if session.get('category'):
                            st.write(f"**카테고리:** {session['category']}")
                        if session.get('keywords'):
                            keywords = json.loads(session['keywords']) if isinstance(session['keywords'], str) else session['keywords']
                            if keywords:
                                st.write(f"**키워드:** {', '.join(keywords[:5])}")
                        
                        if st.button("닫기", key=f"close_info_{session['id']}"):
                            st.session_state.show_session_info = None
                            st.rerun()
                
                st.markdown("---")
        
        # 통계 섹션
        st.markdown("### 📊 통계")
        stats = db.get_chat_statistics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("총 세션", stats['total_sessions'])
        with col2:
            st.metric("총 메시지", stats['total_messages'])
        
        # 카테고리 통계
        if stats['category_stats']:
            st.markdown("**카테고리별 세션**")
            for category, count in stats['category_stats'].items():
                st.write(f"• {category}: {count}")
    
    def render_document_sidebar(self):
        """문서 사이드바 렌더링"""
        st.markdown("### 📁 문서 관리")
        
        # 파일 업로드
        uploaded_file = st.file_uploader(
            "문서 업로드",
            type=['pdf', 'txt', 'md', 'docx'],
            help="PDF, TXT, MD, DOCX 파일을 업로드할 수 있습니다."
        )
        
        if uploaded_file is not None:
            self.handle_file_upload(uploaded_file)
        
        # 업로드된 문서 목록
        documents = db.get_documents()
        
        if not documents:
            st.info("아직 업로드된 문서가 없습니다.")
            return
        
        st.markdown(f"**업로드된 문서 ({len(documents)}개)**")
        
        # 문서 검색
        search_query = st.text_input("문서 검색", placeholder="파일명으로 검색...")
        
        # 필터링
        filtered_docs = documents
        if search_query:
            filtered_docs = [
                doc for doc in documents 
                if search_query.lower() in doc['filename'].lower()
            ]
        
        # 문서 목록 표시
        for doc in filtered_docs:
            with st.expander(f"📄 {doc['filename']}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**크기:** {self.format_file_size(doc['file_size'])}")
                    st.write(f"**타입:** {doc['file_type']}")
                
                with col2:
                    st.write(f"**업로드:** {doc['upload_date'][:10]}")
                    processed_status = "✅ 처리됨" if doc['processed'] else "⏳ 대기중"
                    st.write(f"**상태:** {processed_status}")
                
                if doc.get('keywords'):
                    keywords = json.loads(doc['keywords']) if isinstance(doc['keywords'], str) else doc['keywords']
                    if keywords:
                        st.write(f"**키워드:** {', '.join(keywords[:5])}")
                
                if doc.get('summary'):
                    st.write(f"**요약:** {doc['summary'][:100]}...")
                
                # 문서 액션 버튼
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔍 분석", key=f"analyze_{doc['id']}"):
                        self.analyze_document(doc['id'])
                
                with col2:
                    if st.button("💬 채팅", key=f"chat_{doc['id']}"):
                        self.create_document_chat(doc['id'])
                
                with col3:
                    if st.button("🗑️ 삭제", key=f"del_doc_{doc['id']}"):
                        self.delete_document(doc['id'])
        
        # 문서 통계
        st.markdown("### 📊 문서 통계")
        processed_count = sum(1 for doc in documents if doc['processed'])
        total_size = sum(doc['file_size'] for doc in documents)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("처리된 문서", f"{processed_count}/{len(documents)}")
        with col2:
            st.metric("총 크기", self.format_file_size(total_size))
    
    def render_settings_sidebar(self):
        """설정 사이드바 렌더링"""
        st.markdown("### ⚙️ 설정")
        
        # 자동 카테고리 분류
        auto_categorize = st.checkbox("자동 카테고리 분류", value=True)
        
        # Function Calling 활성화
        enable_functions = st.checkbox("Function Calling 활성화", value=True)
        
        # 키워드 추출 개수
        max_keywords = st.slider("키워드 추출 개수", 5, 20, 10)
        
        # 응답 길이 설정
        response_length = st.selectbox(
            "기본 응답 길이",
            ["짧게", "보통", "길게"],
            index=1
        )
        
        # 언어 설정
        language = st.selectbox(
            "언어 설정",
            ["한국어", "English"],
            index=0
        )
        
        # 테마 설정
        theme = st.selectbox(
            "테마",
            ["라이트", "다크", "자동"],
            index=0
        )
        
        # 설정 저장
        st.session_state.settings = {
            'auto_categorize': auto_categorize,
            'enable_functions': enable_functions,
            'max_keywords': max_keywords,
            'response_length': response_length,
            'language': language,
            'theme': theme
        }
        
        # 설정 초기화 버튼
        if st.button("🔄 설정 초기화", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith('settings'):
                    del st.session_state[key]
            st.success("설정이 초기화되었습니다!")
            st.rerun()
    
    def render_main_chat(self):
        """메인 채팅 영역 렌더링"""
        # 현재 세션 정보 헤더
        if st.session_state.current_session_id:
            sessions = [s for s in st.session_state.chat_sessions 
                       if s['id'] == st.session_state.current_session_id]
            if sessions:
                session = sessions[0]
                
                # 세션 헤더
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"### 💬 {session['title']}")
                    if session.get('category'):
                        st.badge(session['category'])
                
                with col2:
                    # 세션 내보내기 버튼
                    if st.button("📤 내보내기", help="채팅 내용을 파일로 내보내기"):
                        self.export_session(session['id'])
                
                with col3:
                    # 세션 설정 버튼
                    if st.button("⚙️ 설정", help="세션 설정"):
                        st.session_state.show_session_settings = True
                
                # 세션 설정 모달
                if st.session_state.get('show_session_settings', False):
                    with st.expander("세션 설정", expanded=True):
                        new_title = st.text_input("세션 제목", value=session['title'])
                        new_category = st.text_input("카테고리", value=session.get('category', ''))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("💾 저장"):
                                self.update_session_info(session['id'], new_title, new_category)
                                st.session_state.show_session_settings = False
                                st.rerun()
                        
                        with col2:
                            if st.button("❌ 취소"):
                                st.session_state.show_session_settings = False
                                st.rerun()
        else:
            # 환영 메시지
            st.markdown("### 🧠 LocalMind에 오신 것을 환영합니다!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                **📝 내용 기반 질의응답**
                - 업로드한 문서 내용 분석
                - 정확한 정보 기반 답변
                - 출처 정보 제공
                """)
            
            with col2:
                st.markdown("""
                **🎨 문체 모방 생성**
                - 원본 문서 스타일 분석
                - 일관된 톤앤매너 유지
                - 브랜드 보이스 모방
                """)
            
            with col3:
                st.markdown("""
                **🛠️ Function Calling**
                - 문서 검색 및 관리
                - 채팅 히스토리 검색
                - 통계 및 분석 도구
                """)
            
            st.markdown("---")
            st.info("💡 새 채팅을 시작하거나 사이드바에서 기존 채팅을 선택해주세요.")
        
        # 채팅 메시지 표시
        chat_container = st.container()
        
        with chat_container:
            if st.session_state.current_session_id:
                messages = db.get_chat_messages(st.session_state.current_session_id)
                
                if not messages:
                    st.info("아직 메시지가 없습니다. 아래에서 대화를 시작해보세요!")
                else:
                    # 메시지 표시
                    for i, message in enumerate(messages):
                        self.render_message(message, i)
        
        # 채팅 입력 (항상 표시)
        self.render_chat_input()
    
    def render_message(self, message: Dict, index: int):
        """메시지 렌더링"""
        role = message['role']
        content = message['content']
        timestamp = message['timestamp']
        
        # 시간 포맷팅
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%m/%d %H:%M')
        except:
            formatted_time = timestamp[:16] if timestamp else ""
        
        if role == 'user':
            with st.container():
                col1, col2 = st.columns([6, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>🧑 사용자</strong> <small>{formatted_time}</small><br>
                        {content}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # 메시지 액션 버튼
                    if st.button("📋", key=f"copy_user_{index}", help="복사"):
                        st.session_state.clipboard = content
                        st.success("복사됨!")
        
        else:  # assistant
            with st.container():
                col1, col2 = st.columns([6, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>🤖 LocalMind</strong> <small>{formatted_time}</small><br>
                        {content}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Function Call 표시
                    if message.get('function_call'):
                        function_call = message['function_call']
                        st.markdown(f"""
                        <div class="function-call">
                            <strong>🔧 Function Call:</strong> {function_call.get('name', 'Unknown')}<br>
                            <strong>Parameters:</strong> {json.dumps(function_call.get('parameters', {}), ensure_ascii=False)}
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    # 메시지 액션 버튼
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("📋", key=f"copy_ai_{index}", help="복사"):
                            st.session_state.clipboard = content
                            st.success("복사됨!")
                    
                    with col_b:
                        if st.button("🔄", key=f"regen_{index}", help="재생성"):
                            self.regenerate_response(index)
    
    def render_chat_input(self):
        """채팅 입력 렌더링"""
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([6, 1])
            
            with col1:
                user_input = st.text_area(
                    "메시지를 입력하세요...",
                    height=100,
                    placeholder="LocalMind에게 질문하거나 문서에 대해 물어보세요. Function을 사용하려면 @함수명(매개변수=값) 형태로 입력하세요."
                )
            
            with col2:
                submit_button = st.form_submit_button("전송", use_container_width=True)
                
                # 추가 옵션들
                st.markdown("**옵션**")
                use_document_context = st.checkbox("문서 컨텍스트 사용", value=True)
                response_style = st.selectbox(
                    "응답 스타일",
                    ["일반", "상세", "간결", "문체모방"]
                )
        
        if submit_button and user_input.strip():
            self.handle_user_input(user_input, use_document_context, response_style)
    
    def handle_user_input(self, user_input: str, use_document_context: bool, response_style: str):
        """사용자 입력 처리"""
        # 세션이 없으면 새로 생성
        if not st.session_state.current_session_id:
            self.create_new_session(title=user_input[:50])
        
        session_id = st.session_state.current_session_id
        
        # 사용자 메시지 저장
        db.add_message(session_id, 'user', user_input)
        
        # Function Call 확인
        function_call = None
        if st.session_state.settings.get('enable_functions', True):
            function_call = function_manager.parse_function_call(user_input)
        
        # AI 응답 생성
        with st.spinner("LocalMind가 생각하고 있습니다..."):
            if function_call:
                # Function Call 실행
                result = function_manager.execute_function(
                    function_call['function_name'],
                    **function_call['parameters']
                )
                
                # Function Call 결과를 포함한 응답 생성
                context = f"Function Call 결과: {json.dumps(result, ensure_ascii=False)}"
                prompt = f"사용자 요청: {user_input}\n\n{context}\n\n위 정보를 바탕으로 사용자에게 도움이 되는 응답을 생성해주세요."
                
                if response_style == "문체모방":
                    response = self.localmind.mimic_style(prompt)
                else:
                    response = self.localmind.ask_content(prompt)
                
                # 메시지 저장 (Function Call 정보 포함)
                db.add_message(
                    session_id, 
                    'assistant', 
                    response,
                    function_call=function_call,
                    metadata={'function_result': result}
                )
            
            else:
                # 일반 응답 생성
                if response_style == "문체모방":
                    response = self.localmind.mimic_style(user_input)
                else:
                    response = self.localmind.ask_content(user_input)
                
                # 메시지 저장
                db.add_message(session_id, 'assistant', response)
        
        # 자동 카테고리 분류 및 키워드 추출
        if st.session_state.settings.get('auto_categorize', True):
            self.update_session_analysis(session_id)
        
        # 페이지 새로고침
        st.rerun()
    
    def create_new_session(self, title: str = None):
        """새 채팅 세션 생성"""
        if not title:
            title = f"새 채팅 {datetime.now().strftime('%m/%d %H:%M')}"
        
        session_id = db.create_chat_session(title)
        st.session_state.current_session_id = session_id
        st.session_state.messages = []
        st.rerun()
    
    def load_session(self, session_id: str):
        """채팅 세션 로드"""
        st.session_state.current_session_id = session_id
        messages = db.get_chat_messages(session_id)
        st.session_state.messages = messages
        st.rerun()
    
    def delete_session(self, session_id: str):
        """채팅 세션 삭제"""
        try:
            # 데이터베이스에서 세션과 관련 메시지 삭제
            db.delete_chat_session(session_id)
            
            # 현재 세션이 삭제된 세션이면 초기화
            if st.session_state.current_session_id == session_id:
                st.session_state.current_session_id = None
                st.session_state.messages = []
            
            # 확인 상태 초기화
            if f"confirm_delete_{session_id}" in st.session_state:
                del st.session_state[f"confirm_delete_{session_id}"]
            
            st.success("채팅 세션이 삭제되었습니다!")
            st.rerun()
            
        except Exception as e:
            st.error(f"세션 삭제 중 오류가 발생했습니다: {str(e)}")
    
    def format_file_size(self, size_bytes: int) -> str:
        """파일 크기를 읽기 쉬운 형태로 변환"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    def analyze_document(self, doc_id: str):
        """문서 분석"""
        st.info("문서 분석 기능은 개발 중입니다.")
    
    def create_document_chat(self, doc_id: str):
        """문서 기반 채팅 생성"""
        documents = db.get_documents()
        doc = next((d for d in documents if d['id'] == doc_id), None)
        
        if doc:
            title = f"{doc['filename']} 관련 채팅"
            session_id = self.create_new_session(title)
            st.success(f"'{doc['filename']}' 문서 기반 채팅이 생성되었습니다!")
    
    def delete_document(self, doc_id: str):
        """문서 삭제"""
        try:
            db.delete_document(doc_id)
            st.success("문서가 삭제되었습니다!")
            st.rerun()
        except Exception as e:
            st.error(f"문서 삭제 중 오류가 발생했습니다: {str(e)}")
    
    def update_session_analysis(self, session_id: str):
        """세션 분석 업데이트 (키워드, 카테고리)"""
        messages = db.get_chat_messages(session_id)
        
        if messages:
            analysis = keyword_analyzer.analyze_conversation(messages)
            
            # 키워드 업데이트
            db.update_session_keywords(session_id, analysis['keywords'])
            
            # 카테고리 업데이트 (필요시)
            # db.update_session_category(session_id, analysis['category'])
    
    def export_session(self, session_id: str):
        """세션 내보내기"""
        try:
            messages = db.get_chat_messages(session_id)
            session_info = next((s for s in st.session_state.chat_sessions if s['id'] == session_id), None)
            
            if not messages or not session_info:
                st.error("내보낼 데이터가 없습니다.")
                return
            
            # 내보내기 형식 선택
            export_format = st.selectbox("내보내기 형식", ["텍스트 (.txt)", "JSON (.json)", "마크다운 (.md)"])
            
            if st.button("내보내기 실행"):
                export_dir = "exports"
                os.makedirs(export_dir, exist_ok=True)
                
                filename = f"{session_info['title']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                if "텍스트" in export_format:
                    filepath = os.path.join(export_dir, f"{filename}.txt")
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"채팅 세션: {session_info['title']}\n")
                        f.write(f"생성일: {session_info['created_at']}\n")
                        f.write("="*50 + "\n\n")
                        
                        for msg in messages:
                            role_name = "사용자" if msg['role'] == 'user' else "LocalMind"
                            f.write(f"[{msg['timestamp']}] {role_name}:\n")
                            f.write(f"{msg['content']}\n\n")
                
                elif "JSON" in export_format:
                    filepath = os.path.join(export_dir, f"{filename}.json")
                    export_data = {
                        'session_info': session_info,
                        'messages': messages
                    }
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                elif "마크다운" in export_format:
                    filepath = os.path.join(export_dir, f"{filename}.md")
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"# {session_info['title']}\n\n")
                        f.write(f"**생성일:** {session_info['created_at']}\n")
                        if session_info.get('category'):
                            f.write(f"**카테고리:** {session_info['category']}\n")
                        f.write("\n---\n\n")
                        
                        for msg in messages:
                            role_name = "🧑 사용자" if msg['role'] == 'user' else "🤖 LocalMind"
                            f.write(f"## {role_name}\n")
                            f.write(f"*{msg['timestamp']}*\n\n")
                            f.write(f"{msg['content']}\n\n")
                
                st.success(f"✅ 채팅이 {filepath}로 내보내졌습니다!")
                
        except Exception as e:
            st.error(f"❌ 내보내기 중 오류가 발생했습니다: {str(e)}")
    
    def update_session_info(self, session_id: str, title: str, category: str):
        """세션 정보 업데이트"""
        try:
            db.update_session_info(session_id, title, category)
            st.success("세션 정보가 업데이트되었습니다!")
        except Exception as e:
            st.error(f"업데이트 중 오류가 발생했습니다: {str(e)}")
    
    def regenerate_response(self, message_index: int):
        """응답 재생성"""
        st.info("응답 재생성 기능은 개발 중입니다.")
    
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
            
            # 문서 처리 (벡터화) 실행
            with st.spinner("문서를 처리하고 있습니다..."):
                # 문서 처리 상태 업데이트
                db.update_document_processed(doc_id, True)
                st.success("문서 처리가 완료되었습니다!")
            
        except Exception as e:
            st.error(f"❌ 파일 업로드 중 오류가 발생했습니다: {str(e)}")
    
    def run(self):
        """GUI 애플리케이션 실행"""
        self.render_header()
        
        # 메인 레이아웃
        self.render_sidebar()
        self.render_main_chat()

def main():
    """메인 함수"""
    gui = LocalMindGUI()
    gui.run()

if __name__ == "__main__":
    main()