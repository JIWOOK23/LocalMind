"""
LocalMind 설정 파일
"""

import os
import json
from typing import Dict, Any

class Settings:
    """설정 클래스"""
    
    DEFAULT_CONFIG = {
        'ai_model': {
            'name': 'LGAI-EXAONE/EXAONE-4.0-1.2B',
            'embedding_model': 'BAAI/bge-m3',
            'device': 'auto',
            'max_tokens': 512,
            'temperature': 0.1
        },
        'database': {
            'path': 'localmind.db'
        },
        'ui': {
            'theme': 'claude',
            'language': 'ko'
        },
        'upload': {
            'max_file_size': 100,
            'allowed_extensions': ['.pdf', '.txt', '.md', '.docx'],
            'upload_dir': 'data'
        }
    }
    
    def __init__(self):
        self.config = self.DEFAULT_CONFIG.copy()
    
    def get(self, key: str, default=None):
        """설정 값 가져오기"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

# 전역 설정 인스턴스
settings = Settings()