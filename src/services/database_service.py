"""
데이터베이스 서비스 - 개선된 데이터 관리
"""

import sqlite3
import json
import uuid
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import threading
from pathlib import Path

from config.settings import config

class DatabaseService:
    """개선된 데이터베이스 서비스"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.database.db_path
        self.lock = threading.Lock()
        self._ensure_db_directory()
        self.init_database()
    
    def _ensure_db_directory(self):
        """데이터베이스 디렉토리 생성"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """안전한 데이터베이스 연결"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
            try:
                yield conn
            finally:
                conn.close()
    
    def init_database(self):
        """데이터베이스 초기화"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 채팅 세션 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    keywords TEXT,
                    summary TEXT,
                    message_count INTEGER DEFAULT 0,
                    is_archived BOOLEAN DEFAULT FALSE
                )
            """)
            
            # 채팅 메시지 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    function_call TEXT,
                    metadata TEXT,
                    tokens_used INTEGER DEFAULT 0,
                    response_time REAL DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
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
                    processing_time REAL DEFAULT 0,
                    chunk_count INTEGER DEFAULT 0,
                    keywords TEXT,
                    summary TEXT,
                    hash TEXT UNIQUE
                )
            """)
            
            # 사용자 설정 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 시스템 로그 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    module TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # 인덱스 생성
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON chat_messages(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_updated ON chat_sessions(updated_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed)")
            
            conn.commit()
    
    # 채팅 세션 관리
    def create_chat_session(self, title: str, category: str = None) -> str:
        """채팅 세션 생성"""
        session_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_sessions (id, title, category)
                VALUES (?, ?, ?)
            """, (session_id, title, category))
            conn.commit()
        
        return session_id
    
    def get_chat_sessions(self, limit: int = 50, include_archived: bool = False) -> List[Dict]:
        """채팅 세션 목록 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            where_clause = "" if include_archived else "WHERE is_archived = FALSE"
            
            cursor.execute(f"""
                SELECT id, title, category, created_at, updated_at, 
                       keywords, summary, message_count, is_archived
                FROM chat_sessions
                {where_clause}
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_session_info(self, session_id: str, title: str = None, 
                          category: str = None, summary: str = None) -> bool:
        """세션 정보 업데이트"""
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if summary is not None:
            updates.append("summary = ?")
            params.append(summary)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(session_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE chat_sessions 
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_chat_session(self, session_id: str) -> bool:
        """채팅 세션 삭제"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def archive_session(self, session_id: str) -> bool:
        """세션 아카이브"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE chat_sessions 
                SET is_archived = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (session_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # 메시지 관리
    def add_message(self, session_id: str, role: str, content: str,
                   function_call: Dict = None, metadata: Dict = None,
                   tokens_used: int = 0, response_time: float = 0) -> str:
        """메시지 추가"""
        message_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 메시지 추가
            cursor.execute("""
                INSERT INTO chat_messages 
                (id, session_id, role, content, function_call, metadata, tokens_used, response_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_id, session_id, role, content,
                json.dumps(function_call) if function_call else None,
                json.dumps(metadata) if metadata else None,
                tokens_used, response_time
            ))
            
            # 세션의 메시지 수 업데이트
            cursor.execute("""
                UPDATE chat_sessions 
                SET message_count = message_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (session_id,))
            
            conn.commit()
        
        return message_id
    
    def get_chat_messages(self, session_id: str, limit: int = None) -> List[Dict]:
        """세션의 메시지 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT id, role, content, timestamp, function_call, 
                       metadata, tokens_used, response_time
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """
            
            params = [session_id]
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            
            messages = []
            for row in cursor.fetchall():
                message = dict(row)
                # JSON 필드 파싱
                if message['function_call']:
                    message['function_call'] = json.loads(message['function_call'])
                if message['metadata']:
                    message['metadata'] = json.loads(message['metadata'])
                messages.append(message)
            
            return messages
    
    def search_messages(self, query: str, session_id: str = None, limit: int = 20) -> List[Dict]:
        """메시지 검색"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            base_query = """
                SELECT cm.*, cs.title as session_title, cs.category
                FROM chat_messages cm
                JOIN chat_sessions cs ON cm.session_id = cs.id
                WHERE cm.content LIKE ?
            """
            
            params = [f'%{query}%']
            
            if session_id:
                base_query += " AND cm.session_id = ?"
                params.append(session_id)
            
            base_query += " ORDER BY cm.timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(base_query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # 문서 관리
    def add_document(self, filename: str, filepath: str, file_type: str,
                    file_size: int, file_hash: str = None) -> str:
        """문서 추가"""
        doc_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO documents 
                (id, filename, filepath, file_type, file_size, hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc_id, filename, filepath, file_type, file_size, file_hash))
            conn.commit()
        
        return doc_id
    
    def get_documents(self, processed_only: bool = False) -> List[Dict]:
        """문서 목록 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT id, filename, filepath, file_type, file_size,
                       upload_date, processed, processing_time, chunk_count,
                       keywords, summary, hash
                FROM documents
            """
            
            if processed_only:
                query += " WHERE processed = TRUE"
            
            query += " ORDER BY upload_date DESC"
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_document_processed(self, doc_id: str, processed: bool = True,
                                processing_time: float = 0, chunk_count: int = 0) -> bool:
        """문서 처리 상태 업데이트"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents 
                SET processed = ?, processing_time = ?, chunk_count = ?
                WHERE id = ?
            """, (processed, processing_time, chunk_count, doc_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_document(self, doc_id: str) -> bool:
        """문서 삭제"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 파일 경로 조회
            cursor.execute("SELECT filepath FROM documents WHERE id = ?", (doc_id,))
            result = cursor.fetchone()
            
            if result:
                filepath = result['filepath']
                
                # 실제 파일 삭제
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except Exception as e:
                    print(f"파일 삭제 실패: {e}")
                
                # 데이터베이스에서 삭제
                cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                conn.commit()
                return cursor.rowcount > 0
            
            return False
    
    # 통계 및 분석
    def get_chat_statistics(self) -> Dict:
        """채팅 통계 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 기본 통계
            cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE is_archived = FALSE")
            total_sessions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chat_messages")
            total_messages = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM documents WHERE processed = TRUE")
            processed_documents = cursor.fetchone()[0]
            
            # 카테고리별 세션 수
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM chat_sessions
                WHERE category IS NOT NULL AND is_archived = FALSE
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
            
            # 토큰 사용량 통계
            cursor.execute("SELECT SUM(tokens_used) FROM chat_messages")
            total_tokens = cursor.fetchone()[0] or 0
            
            # 평균 응답 시간
            cursor.execute("""
                SELECT AVG(response_time) 
                FROM chat_messages 
                WHERE role = 'assistant' AND response_time > 0
            """)
            avg_response_time = cursor.fetchone()[0] or 0
            
            return {
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'processed_documents': processed_documents,
                'category_stats': category_stats,
                'recent_activity': recent_activity,
                'total_tokens': total_tokens,
                'avg_response_time': round(avg_response_time, 2)
            }
    
    # 설정 관리
    def get_user_setting(self, key: str, default=None):
        """사용자 설정 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            
            if result:
                try:
                    return json.loads(result['value'])
                except:
                    return result['value']
            
            return default
    
    def set_user_setting(self, key: str, value):
        """사용자 설정 저장"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # JSON으로 직렬화
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value_str))
            conn.commit()
    
    # 로그 관리
    def add_log(self, level: str, message: str, module: str = None, metadata: Dict = None):
        """시스템 로그 추가"""
        log_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_logs (id, level, message, module, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                log_id, level, message, module,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
    
    def get_logs(self, level: str = None, limit: int = 100) -> List[Dict]:
        """시스템 로그 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM system_logs"
            params = []
            
            if level:
                query += " WHERE level = ?"
                params.append(level)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

# 전역 데이터베이스 서비스 인스턴스
db_service = DatabaseService()