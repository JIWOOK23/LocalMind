# database.py
"""
LocalMind 데이터베이스 관리 모듈
채팅 히스토리, 문서, 카테고리 등을 관리합니다.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd

class LocalMindDB:
    """LocalMind 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = "localmind.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 채팅 세션 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    keywords TEXT,  -- JSON 형태로 저장
                    summary TEXT
                )
            """)
            
            # 채팅 메시지 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,  -- 'user' or 'assistant'
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    function_call TEXT,  -- JSON 형태로 저장
                    metadata TEXT,  -- JSON 형태로 저장
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
                )
            """)
            
            # 문서 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    file_type TEXT,
                    file_size INTEGER,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE,
                    keywords TEXT,  -- JSON 형태로 저장
                    summary TEXT
                )
            """)
            
            # 카테고리 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    color TEXT DEFAULT '#007bff',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 키워드 테이블 (검색 최적화용)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keywords (
                    id TEXT PRIMARY KEY,
                    keyword TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    source_type TEXT,  -- 'chat', 'document'
                    source_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def create_chat_session(self, title: str, category: str = None) -> str:
        """새 채팅 세션 생성"""
        session_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_sessions (id, title, category)
                VALUES (?, ?, ?)
            """, (session_id, title, category))
            conn.commit()
        
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str, 
                   function_call: Dict = None, metadata: Dict = None) -> str:
        """채팅 메시지 추가"""
        message_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_messages (id, session_id, role, content, function_call, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                message_id, session_id, role, content,
                json.dumps(function_call) if function_call else None,
                json.dumps(metadata) if metadata else None
            ))
            
            # 세션 업데이트 시간 갱신
            cursor.execute("""
                UPDATE chat_sessions 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (session_id,))
            
            conn.commit()
        
        return message_id
    
    def get_chat_sessions(self, limit: int = 50) -> List[Dict]:
        """채팅 세션 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, category, created_at, updated_at, keywords, summary
                FROM chat_sessions
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_chat_messages(self, session_id: str) -> List[Dict]:
        """특정 세션의 메시지 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, role, content, timestamp, function_call, metadata
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))
            
            columns = [desc[0] for desc in cursor.description]
            messages = []
            for row in cursor.fetchall():
                message = dict(zip(columns, row))
                # JSON 필드 파싱
                if message['function_call']:
                    message['function_call'] = json.loads(message['function_call'])
                if message['metadata']:
                    message['metadata'] = json.loads(message['metadata'])
                messages.append(message)
            
            return messages
    
    def search_messages(self, query: str, limit: int = 20) -> List[Dict]:
        """메시지 검색"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cm.*, cs.title as session_title, cs.category
                FROM chat_messages cm
                JOIN chat_sessions cs ON cm.session_id = cs.id
                WHERE cm.content LIKE ? OR cs.title LIKE ? OR cs.keywords LIKE ?
                ORDER BY cm.timestamp DESC
                LIMIT ?
            """, (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def add_document(self, filename: str, filepath: str, file_type: str, 
                    file_size: int) -> str:
        """문서 추가"""
        doc_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO documents (id, filename, filepath, file_type, file_size)
                VALUES (?, ?, ?, ?, ?)
            """, (doc_id, filename, filepath, file_type, file_size))
            conn.commit()
        
        return doc_id
    
    def get_documents(self) -> List[Dict]:
        """문서 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, filepath, file_type, file_size, 
                       upload_date, processed, keywords, summary
                FROM documents
                ORDER BY upload_date DESC
            """)
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_session_keywords(self, session_id: str, keywords: List[str]):
        """세션 키워드 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE chat_sessions 
                SET keywords = ?
                WHERE id = ?
            """, (json.dumps(keywords), session_id))
            conn.commit()
    
    def get_categories(self) -> List[Dict]:
        """카테고리 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, description, color, created_at
                FROM categories
                ORDER BY name
            """)
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def add_category(self, name: str, description: str = None, color: str = '#007bff') -> str:
        """카테고리 추가"""
        category_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO categories (id, name, description, color)
                VALUES (?, ?, ?, ?)
            """, (category_id, name, description, color))
            conn.commit()
        
        return category_id
    
    def delete_chat_session(self, session_id: str):
        """채팅 세션 삭제 (관련 메시지도 함께 삭제)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 관련 메시지 먼저 삭제
            cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            
            # 세션 삭제
            cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            
            conn.commit()
    
    def delete_document(self, doc_id: str):
        """문서 삭제"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 문서 정보 조회 (파일 경로 확인용)
            cursor.execute("SELECT filepath FROM documents WHERE id = ?", (doc_id,))
            result = cursor.fetchone()
            
            if result:
                filepath = result[0]
                
                # 실제 파일 삭제
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except Exception as e:
                    print(f"파일 삭제 실패: {e}")
                
                # 데이터베이스에서 문서 정보 삭제
                cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                conn.commit()
    
    def update_document_processed(self, doc_id: str, processed: bool = True):
        """문서 처리 상태 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents 
                SET processed = ?
                WHERE id = ?
            """, (processed, doc_id))
            conn.commit()
    
    def update_session_info(self, session_id: str, title: str, category: str = None):
        """세션 정보 업데이트"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE chat_sessions 
                SET title = ?, category = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (title, category, session_id))
            conn.commit()
    
    def get_chat_statistics(self) -> Dict:
        """채팅 통계 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 총 세션 수
            cursor.execute("SELECT COUNT(*) FROM chat_sessions")
            total_sessions = cursor.fetchone()[0]
            
            # 총 메시지 수
            cursor.execute("SELECT COUNT(*) FROM chat_messages")
            total_messages = cursor.fetchone()[0]
            
            # 카테고리별 세션 수
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM chat_sessions
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
            """)
            category_stats = dict(cursor.fetchall())
            
            # 최근 7일 활동
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM chat_sessions
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            recent_activity = dict(cursor.fetchall())
            
            return {
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'category_stats': category_stats,
                'recent_activity': recent_activity
            }

# 전역 데이터베이스 인스턴스
db = LocalMindDB()