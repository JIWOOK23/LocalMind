# function_tools.py
"""
LocalMind Function Calling 도구들
AI가 사용할 수 있는 다양한 도구들을 정의합니다.
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from database import db
from keyword_analyzer import keyword_analyzer
import plotly.express as px
import plotly.graph_objects as go

class FunctionTool:
    """Function Tool 베이스 클래스"""
    
    def __init__(self, name: str, description: str, parameters: Dict):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """도구 실행 (하위 클래스에서 구현)"""
        raise NotImplementedError

class SearchDocumentsTool(FunctionTool):
    """문서 검색 도구"""
    
    def __init__(self):
        super().__init__(
            name="search_documents",
            description="업로드된 문서들을 검색합니다.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 키워드나 문구"
                    },
                    "file_type": {
                        "type": "string",
                        "description": "파일 타입 필터 (pdf, txt, md 등)",
                        "enum": ["pdf", "txt", "md", "docx", "all"]
                    }
                },
                "required": ["query"]
            }
        )
    
    def execute(self, query: str, file_type: str = "all") -> Dict[str, Any]:
        """문서 검색 실행"""
        try:
            documents = db.get_documents()
            
            # 파일 타입 필터링
            if file_type != "all":
                documents = [doc for doc in documents if doc['file_type'] == file_type]
            
            # 키워드 검색
            results = []
            for doc in documents:
                if (query.lower() in doc['filename'].lower() or 
                    (doc['summary'] and query.lower() in doc['summary'].lower()) or
                    (doc['keywords'] and query.lower() in doc['keywords'].lower())):
                    results.append(doc)
            
            return {
                "success": True,
                "results": results,
                "count": len(results),
                "message": f"'{query}'에 대한 검색 결과 {len(results)}개를 찾았습니다."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "문서 검색 중 오류가 발생했습니다."
            }

class SearchChatHistoryTool(FunctionTool):
    """채팅 히스토리 검색 도구"""
    
    def __init__(self):
        super().__init__(
            name="search_chat_history",
            description="과거 채팅 기록을 검색합니다.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 키워드나 문구"
                    },
                    "category": {
                        "type": "string",
                        "description": "카테고리 필터"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "검색 결과 개수 제한",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        )
    
    def execute(self, query: str, category: str = None, limit: int = 10) -> Dict[str, Any]:
        """채팅 히스토리 검색 실행"""
        try:
            messages = db.search_messages(query, limit)
            
            # 카테고리 필터링
            if category:
                messages = [msg for msg in messages if msg.get('category') == category]
            
            return {
                "success": True,
                "results": messages,
                "count": len(messages),
                "message": f"'{query}'에 대한 채팅 기록 {len(messages)}개를 찾았습니다."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "채팅 기록 검색 중 오류가 발생했습니다."
            }

class GetChatStatisticsTool(FunctionTool):
    """채팅 통계 조회 도구"""
    
    def __init__(self):
        super().__init__(
            name="get_chat_statistics",
            description="채팅 사용 통계를 조회합니다.",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    
    def execute(self) -> Dict[str, Any]:
        """채팅 통계 조회 실행"""
        try:
            stats = db.get_chat_statistics()
            
            return {
                "success": True,
                "statistics": stats,
                "message": "채팅 통계를 성공적으로 조회했습니다."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "통계 조회 중 오류가 발생했습니다."
            }

class CreateCategoryTool(FunctionTool):
    """카테고리 생성 도구"""
    
    def __init__(self):
        super().__init__(
            name="create_category",
            description="새로운 대화 카테고리를 생성합니다.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "카테고리 이름"
                    },
                    "description": {
                        "type": "string",
                        "description": "카테고리 설명"
                    },
                    "color": {
                        "type": "string",
                        "description": "카테고리 색상 (hex 코드)",
                        "default": "#007bff"
                    }
                },
                "required": ["name"]
            }
        )
    
    def execute(self, name: str, description: str = None, color: str = "#007bff") -> Dict[str, Any]:
        """카테고리 생성 실행"""
        try:
            category_id = db.add_category(name, description, color)
            
            return {
                "success": True,
                "category_id": category_id,
                "message": f"'{name}' 카테고리가 성공적으로 생성되었습니다."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "카테고리 생성 중 오류가 발생했습니다."
            }

class AnalyzeKeywordsTool(FunctionTool):
    """키워드 분석 도구"""
    
    def __init__(self):
        super().__init__(
            name="analyze_keywords",
            description="텍스트에서 키워드를 분석하고 카테고리를 추천합니다.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "분석할 텍스트"
                    },
                    "max_keywords": {
                        "type": "integer",
                        "description": "추출할 최대 키워드 수",
                        "default": 10
                    }
                },
                "required": ["text"]
            }
        )
    
    def execute(self, text: str, max_keywords: int = 10) -> Dict[str, Any]:
        """키워드 분석 실행"""
        try:
            keywords = keyword_analyzer.extract_keywords(text, max_keywords)
            category = keyword_analyzer.categorize_by_keywords(keywords)
            
            return {
                "success": True,
                "keywords": keywords,
                "recommended_category": category,
                "message": f"{len(keywords)}개의 키워드를 추출했습니다."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "키워드 분석 중 오류가 발생했습니다."
            }

class ExportChatTool(FunctionTool):
    """채팅 내보내기 도구"""
    
    def __init__(self):
        super().__init__(
            name="export_chat",
            description="채팅 세션을 파일로 내보냅니다.",
            parameters={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "내보낼 세션 ID"
                    },
                    "format": {
                        "type": "string",
                        "description": "내보낼 파일 형식",
                        "enum": ["json", "txt", "md"],
                        "default": "md"
                    }
                },
                "required": ["session_id"]
            }
        )
    
    def execute(self, session_id: str, format: str = "md") -> Dict[str, Any]:
        """채팅 내보내기 실행"""
        try:
            messages = db.get_chat_messages(session_id)
            sessions = db.get_chat_sessions(limit=1000)
            session_info = next((s for s in sessions if s['id'] == session_id), None)
            
            if not session_info:
                return {
                    "success": False,
                    "message": "세션을 찾을 수 없습니다."
                }
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_export_{session_id[:8]}_{timestamp}.{format}"
            
            if format == "json":
                content = json.dumps({
                    "session_info": session_info,
                    "messages": messages
                }, ensure_ascii=False, indent=2)
            
            elif format == "txt":
                content = f"채팅 세션: {session_info['title']}\n"
                content += f"카테고리: {session_info.get('category', 'N/A')}\n"
                content += f"생성일: {session_info['created_at']}\n"
                content += "=" * 50 + "\n\n"
                
                for msg in messages:
                    role = "사용자" if msg['role'] == 'user' else "어시스턴트"
                    content += f"[{role}] {msg['timestamp']}\n"
                    content += f"{msg['content']}\n\n"
            
            elif format == "md":
                content = f"# {session_info['title']}\n\n"
                content += f"- **카테고리**: {session_info.get('category', 'N/A')}\n"
                content += f"- **생성일**: {session_info['created_at']}\n"
                content += f"- **메시지 수**: {len(messages)}\n\n"
                content += "---\n\n"
                
                for msg in messages:
                    role = "🧑 사용자" if msg['role'] == 'user' else "🤖 LocalMind"
                    content += f"## {role}\n"
                    content += f"*{msg['timestamp']}*\n\n"
                    content += f"{msg['content']}\n\n"
            
            # 파일 저장
            export_dir = "exports"
            os.makedirs(export_dir, exist_ok=True)
            filepath = os.path.join(export_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "filepath": filepath,
                "filename": filename,
                "message": f"채팅이 {filename}으로 내보내졌습니다."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "채팅 내보내기 중 오류가 발생했습니다."
            }

class FunctionCallManager:
    """Function Call 관리자"""
    
    def __init__(self):
        self.tools = {
            "search_documents": SearchDocumentsTool(),
            "search_chat_history": SearchChatHistoryTool(),
            "get_chat_statistics": GetChatStatisticsTool(),
            "create_category": CreateCategoryTool(),
            "analyze_keywords": AnalyzeKeywordsTool(),
            "export_chat": ExportChatTool()
        }
    
    def get_available_tools(self) -> List[Dict]:
        """사용 가능한 도구 목록 반환"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]
    
    def execute_function(self, function_name: str, **kwargs) -> Dict[str, Any]:
        """함수 실행"""
        if function_name not in self.tools:
            return {
                "success": False,
                "error": f"Unknown function: {function_name}",
                "message": f"'{function_name}' 함수를 찾을 수 없습니다."
            }
        
        try:
            tool = self.tools[function_name]
            result = tool.execute(**kwargs)
            
            # 실행 로그 추가
            result["function_name"] = function_name
            result["executed_at"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"'{function_name}' 실행 중 오류가 발생했습니다."
            }
    
    def parse_function_call(self, text: str) -> Optional[Dict]:
        """텍스트에서 함수 호출 파싱"""
        # 간단한 함수 호출 파싱 (실제로는 더 정교한 파싱이 필요)
        import re
        
        # 함수 호출 패턴 매칭
        pattern = r'@(\w+)\((.*?)\)'
        match = re.search(pattern, text)
        
        if match:
            function_name = match.group(1)
            params_str = match.group(2)
            
            # 파라미터 파싱 (간단한 버전)
            params = {}
            if params_str:
                for param in params_str.split(','):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key.strip()] = value.strip().strip('"\'')
            
            return {
                "function_name": function_name,
                "parameters": params
            }
        
        return None

# 전역 Function Call 관리자 인스턴스
function_manager = FunctionCallManager()