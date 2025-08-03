"""
LocalMind 설정 관리
"""

import os
from pathlib import Path
from typing import Dict, Any
import json
from dataclasses import dataclass, asdict

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent

@dataclass
class ModelConfig:
    """AI 모델 설정"""
    llm_model: str = "LGAI-EXAONE/EXAONE-4.0-1.2B"
    embedding_model: str = "BAAI/bge-m3"
    device: str = "auto"  # auto, cpu, cuda
    max_tokens: int = 512
    temperature: float = 0.1
    top_p: float = 0.9

@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""
    db_path: str = "data/localmind.db"
    faiss_index_path: str = "data/document_memory.faiss"
    text_data_path: str = "data/document_memory.pkl"
    backup_enabled: bool = True
    backup_interval: int = 3600  # seconds

@dataclass
class UIConfig:
    """UI 설정"""
    theme: str = "claude"  # claude, dark, light
    language: str = "ko"
    page_title: str = "LocalMind"
    page_icon: str = "🧠"
    layout: str = "wide"
    sidebar_state: str = "collapsed"

@dataclass
class ProcessingConfig:
    """문서 처리 설정"""
    supported_formats: list = None
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    chunk_size: int = 1000
    chunk_overlap: int = 200
    batch_size: int = 32

    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ['.pdf', '.txt', '.md', '.docx', '.doc']

@dataclass
class SecurityConfig:
    """보안 설정"""
    enable_auth: bool = False
    session_timeout: int = 3600
    max_sessions: int = 10
    rate_limit: int = 100  # requests per minute

@dataclass
class AppConfig:
    """전체 애플리케이션 설정"""
    model: ModelConfig = None
    database: DatabaseConfig = None
    ui: UIConfig = None
    processing: ProcessingConfig = None
    security: SecurityConfig = None
    
    def __post_init__(self):
        if self.model is None:
            self.model = ModelConfig()
        if self.database is None:
            self.database = DatabaseConfig()
        if self.ui is None:
            self.ui = UIConfig()
        if self.processing is None:
            self.processing = ProcessingConfig()
        if self.security is None:
            self.security = SecurityConfig()

class ConfigManager:
    """설정 관리자"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or PROJECT_ROOT / "config" / "app_config.json"
        self.config = self.load_config()
    
    def load_config(self) -> AppConfig:
        """설정 로드"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return self._dict_to_config(data)
            except Exception as e:
                print(f"설정 로드 실패: {e}")
        
        # 기본 설정 반환
        return AppConfig()
    
    def save_config(self):
        """설정 저장"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_to_dict(self.config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"설정 저장 실패: {e}")
    
    def _config_to_dict(self, config: AppConfig) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            'model': asdict(config.model),
            'database': asdict(config.database),
            'ui': asdict(config.ui),
            'processing': asdict(config.processing),
            'security': asdict(config.security)
        }
    
    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        """딕셔너리를 설정으로 변환"""
        return AppConfig(
            model=ModelConfig(**data.get('model', {})),
            database=DatabaseConfig(**data.get('database', {})),
            ui=UIConfig(**data.get('ui', {})),
            processing=ProcessingConfig(**data.get('processing', {})),
            security=SecurityConfig(**data.get('security', {}))
        )
    
    def update_config(self, **kwargs):
        """설정 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()

# 전역 설정 인스턴스
config_manager = ConfigManager()
config = config_manager.config