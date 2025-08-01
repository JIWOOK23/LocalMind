# keyword_analyzer.py
"""
LocalMind 키워드 분석 모듈
대화 내용에서 키워드를 추출하고 분류합니다.
"""

import re
from typing import List, Dict, Tuple
from collections import Counter
import kss
try:
    from konlpy.tag import Okt
    KONLPY_AVAILABLE = True
except ImportError:
    KONLPY_AVAILABLE = False
    print("⚠️ KoNLPy가 설치되지 않았습니다. 기본 키워드 추출을 사용합니다.")

class KeywordAnalyzer:
    """키워드 분석 클래스"""
    
    def __init__(self):
        self.okt = Okt() if KONLPY_AVAILABLE else None
        
        # 불용어 리스트
        self.stopwords = {
            '이', '그', '저', '것', '수', '등', '들', '및', '또는', '그리고',
            '하지만', '그러나', '따라서', '그래서', '또한', '즉', '예를 들어',
            '있다', '없다', '이다', '아니다', '되다', '하다', '가다', '오다',
            '보다', '주다', '받다', '말하다', '생각하다', '알다', '모르다',
            '좋다', '나쁘다', '크다', '작다', '많다', '적다', '높다', '낮다',
            '안녕하세요', '감사합니다', '죄송합니다', '네', '아니요', '예',
            '뭐', '어떤', '어떻게', '왜', '언제', '어디서', '누가', '무엇을'
        }
        
        # 카테고리 키워드 매핑
        self.category_keywords = {
            '기술': ['프로그래밍', '개발', '코딩', '알고리즘', 'AI', '인공지능', '머신러닝', 
                   '딥러닝', '데이터', '분석', '시스템', '서버', '데이터베이스', '웹', '앱'],
            '업무': ['회의', '프로젝트', '업무', '일정', '계획', '보고서', '문서', '발표',
                   '팀', '협업', '관리', '성과', '목표', '전략', '마케팅'],
            '학습': ['공부', '학습', '교육', '강의', '책', '논문', '연구', '시험', '과제',
                   '지식', '이해', '설명', '개념', '이론', '실습'],
            '일반': ['질문', '답변', '도움', '문제', '해결', '방법', '정보', '내용',
                   '설명', '예시', '경우', '상황', '결과', '이유', '목적']
        }
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """텍스트에서 키워드 추출"""
        if not text.strip():
            return []
        
        if self.okt:
            return self._extract_with_konlpy(text, max_keywords)
        else:
            return self._extract_basic(text, max_keywords)
    
    def _extract_with_konlpy(self, text: str, max_keywords: int) -> List[str]:
        """KoNLPy를 사용한 키워드 추출"""
        try:
            # 문장 분리
            sentences = kss.split_sentences(text)
            
            keywords = []
            for sentence in sentences:
                # 형태소 분석
                morphs = self.okt.pos(sentence, stem=True)
                
                # 명사, 형용사, 동사만 추출
                for word, pos in morphs:
                    if (pos in ['Noun', 'Adjective', 'Verb'] and 
                        len(word) > 1 and 
                        word not in self.stopwords and
                        not word.isdigit()):
                        keywords.append(word)
            
            # 빈도수 기반 상위 키워드 반환
            counter = Counter(keywords)
            return [word for word, count in counter.most_common(max_keywords)]
            
        except Exception as e:
            print(f"KoNLPy 키워드 추출 오류: {e}")
            return self._extract_basic(text, max_keywords)
    
    def _extract_basic(self, text: str, max_keywords: int) -> List[str]:
        """기본 키워드 추출 (형태소 분석 없이)"""
        # 특수문자 제거 및 단어 분리
        words = re.findall(r'[가-힣a-zA-Z]+', text)
        
        # 필터링
        filtered_words = []
        for word in words:
            if (len(word) > 1 and 
                word not in self.stopwords and
                not word.isdigit()):
                filtered_words.append(word)
        
        # 빈도수 기반 상위 키워드 반환
        counter = Counter(filtered_words)
        return [word for word, count in counter.most_common(max_keywords)]
    
    def categorize_by_keywords(self, keywords: List[str]) -> str:
        """키워드 기반 카테고리 분류"""
        if not keywords:
            return '일반'
        
        category_scores = {}
        
        for category, category_keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                for cat_keyword in category_keywords:
                    if keyword in cat_keyword or cat_keyword in keyword:
                        score += 1
            category_scores[category] = score
        
        # 가장 높은 점수의 카테고리 반환
        if max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        else:
            return '일반'
    
    def analyze_conversation(self, messages: List[Dict]) -> Dict:
        """대화 전체 분석"""
        all_text = ""
        user_messages = []
        assistant_messages = []
        
        for message in messages:
            content = message.get('content', '')
            all_text += content + " "
            
            if message.get('role') == 'user':
                user_messages.append(content)
            elif message.get('role') == 'assistant':
                assistant_messages.append(content)
        
        # 전체 키워드 추출
        keywords = self.extract_keywords(all_text, max_keywords=15)
        
        # 카테고리 분류
        category = self.categorize_by_keywords(keywords)
        
        # 대화 요약 생성 (간단한 버전)
        summary = self._generate_simple_summary(user_messages, keywords)
        
        return {
            'keywords': keywords,
            'category': category,
            'summary': summary,
            'message_count': len(messages),
            'user_message_count': len(user_messages),
            'assistant_message_count': len(assistant_messages)
        }
    
    def _generate_simple_summary(self, user_messages: List[str], keywords: List[str]) -> str:
        """간단한 대화 요약 생성"""
        if not user_messages:
            return "대화 내용 없음"
        
        # 첫 번째 사용자 메시지와 주요 키워드 조합
        first_message = user_messages[0][:50] + "..." if len(user_messages[0]) > 50 else user_messages[0]
        
        if keywords:
            top_keywords = ", ".join(keywords[:3])
            return f"{first_message} (주요 키워드: {top_keywords})"
        else:
            return first_message
    
    def search_by_keywords(self, query: str, target_keywords_list: List[List[str]]) -> List[Tuple[int, float]]:
        """키워드 기반 검색"""
        query_keywords = self.extract_keywords(query, max_keywords=5)
        
        if not query_keywords:
            return []
        
        results = []
        for idx, target_keywords in enumerate(target_keywords_list):
            if not target_keywords:
                continue
            
            # 키워드 매칭 점수 계산
            score = 0
            for q_keyword in query_keywords:
                for t_keyword in target_keywords:
                    if q_keyword == t_keyword:
                        score += 2  # 완전 일치
                    elif q_keyword in t_keyword or t_keyword in q_keyword:
                        score += 1  # 부분 일치
            
            if score > 0:
                # 정규화된 점수 (0-1 사이)
                normalized_score = score / (len(query_keywords) * 2)
                results.append((idx, normalized_score))
        
        # 점수 순으로 정렬
        results.sort(key=lambda x: x[1], reverse=True)
        return results

# 전역 키워드 분석기 인스턴스
keyword_analyzer = KeywordAnalyzer()