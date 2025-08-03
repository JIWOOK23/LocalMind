"""
메인 GUI 애플리케이션 - 고도화된 아키텍처
"""

import streamlit as st
import time
from datetime import datetime
from typing import Dict, List, Optional

# 내부 모듈들
from config.settings import config
from src.core.ai_engine import get_ai_engine
from src.services.database_service import db_service
from src.services.document_service import document_service
from src.ui.components import UIComponents, ADDITIONAL_CSS

class LocalMindApp:
    """LocalMind 메인 애플리케이션"""
    
    def __init__(self):
        self.setup_page_config()
        self.load_css()
        self.init_session_state()
        self.ai_engine = get_ai_engine()
    
    def setup_page_config(self):
        """페이지 설정"""
        st.set_page_config(
            page_title=config.ui.page_title,
            page_icon=config.ui.page_icon,
            layout=config.ui.layout,
            initial_sidebar_state=config.ui.sidebar_state
        )
    
    def load_css(self):
        """CSS 로드"""
        # 기본 Claude 스타일 CSS
        st.markdown("""
        <style>
            /* 전체 앱 스타일 */
    