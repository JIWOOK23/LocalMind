"""
AI 엔진 - 핵심 AI 기능 관리
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import numpy as np
import faiss
import pickle
import os
from typing import List, Dict, Optional, Tuple
import warnings
from datetime import datetime

from config.settings import config

# 경고 숨기기
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*encoder_attention_mask.*")

class AIEngine:
    """AI 엔진 클래스"""
    
    def __init__(self):
        self.device = self._get_device()
        self.model = None
        self.tokenizer = None
        self.embedding_model = None
        self.index = None
        self.texts = []
        self.metadatas = []
        self.is_initialized = False
        
        self._initialize()
    
    def _get_device(self) -> str:
        """디바이스 결정"""
        if config.model.device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return config.model.device
    
    def _initialize(self):
        """AI 엔진 초기화"""
        try:
            print("🚀 AI 엔진을 초기화합니다...")
            
            # LLM 초기화
            self._initialize_llm()
            
            # 임베딩 모델 초기화
            self._initialize_embedding()
            
            # 벡터 데이터베이스 로드
            self._load_vector_db()
            
            self.is_initialized = True
            print("✅ AI 엔진 초기화 완료!")
            
        except Exception as e:
            print(f"❌ AI 엔진 초기화 실패: {str(e)}")
            raise
    
    def _initialize_llm(self):
        """LLM 모델 초기화"""
        print(f"1. LLM 모델 로드 중... ({config.model.llm_model})")
        print(f"   디바이스: {self.device}")
        
        # 토크나이저 로드
        self.tokenizer = AutoTokenizer.from_pretrained(
            config.model.llm_model,
            trust_remote_code=True
        )
        
        # 모델 로드
        self.model = AutoModelForCausalLM.from_pretrained(
            config.model.llm_model,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
            trust_remote_code=True
        )
        
        print("   ✅ LLM 모델 로드 완료")
    
    def _initialize_embedding(self):
        """임베딩 모델 초기화"""
        print(f"2. 임베딩 모델 로드 중... ({config.model.embedding_model})")
        
        self.embedding_model = HuggingFaceEmbedding(
            model_name=config.model.embedding_model
        )
        
        print("   ✅ 임베딩 모델 로드 완료")
    
    def _load_vector_db(self):
        """벡터 데이터베이스 로드"""
        faiss_path = config.database.faiss_index_path
        data_path = config.database.text_data_path
        
        if not os.path.exists(faiss_path) or not os.path.exists(data_path):
            print("⚠️ 벡터 데이터베이스가 없습니다. 문서를 업로드한 후 create_db.py를 실행하세요.")
            return
        
        print("3. 벡터 데이터베이스 로드 중...")
        
        # FAISS 인덱스 로드
        self.index = faiss.read_index(faiss_path)
        
        # 텍스트 데이터 로드
        with open(data_path, "rb") as f:
            data = pickle.load(f)
            self.texts = data["texts"]
            self.metadatas = data["metadatas"]
        
        print(f"   ✅ {len(self.texts)}개의 문서 청크 로드 완료")
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """응답 생성"""
        if not self.is_initialized or not self.model:
            return "❌ AI 엔진이 초기화되지 않았습니다."
        
        try:
            # 파라미터 설정
            max_tokens = kwargs.get('max_tokens', config.model.max_tokens)
            temperature = kwargs.get('temperature', config.model.temperature)
            top_p = kwargs.get('top_p', config.model.top_p)
            
            # 채팅 템플릿 적용
            messages = [{"role": "user", "content": prompt}]
            formatted_prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # 토크나이징
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt")
            if self.device == "cuda":
                inputs = inputs.to(self.device)
            
            # 생성
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # 디코딩
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 프롬프트 부분 제거
            if formatted_prompt in response:
                response = response.replace(formatted_prompt, "").strip()
            
            return response
            
        except Exception as e:
            return f"❌ 응답 생성 중 오류: {str(e)}"
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict]:
        """문서 검색"""
        if not self.embedding_model or not self.index:
            return []
        
        try:
            # 쿼리를 벡터로 변환
            query_embedding = self.embedding_model.get_text_embedding(query)
            query_vector = np.array([query_embedding]).astype('float32')
            
            # FAISS로 유사한 문서 검색
            scores, indices = self.index.search(query_vector, top_k)
            
            # 결과 수집
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.texts) and score > 0.1:
                    results.append({
                        'text': self.texts[idx],
                        'metadata': self.metadatas[idx],
                        'score': float(score)
                    })
            
            return results
            
        except Exception as e:
            print(f"문서 검색 오류: {e}")
            return []
    
    def ask_content(self, question: str) -> str:
        """내용 기반 질의응답"""
        if not self.is_initialized:
            return "❌ AI 엔진이 초기화되지 않았습니다."
        
        try:
            # 관련 문서 검색
            search_results = self.search_documents(question)
            
            if not search_results:
                return "❌ 관련 문서를 찾을 수 없습니다. 문서를 업로드하고 데이터베이스를 생성해주세요."
            
            # 컨텍스트 구성
            context_parts = []
            for result in search_results:
                source = result['metadata'].get('source', 'Unknown')
                text = result['text']
                context_parts.append(f"[출처: {source}] {text}")
            
            context = "\n\n".join(context_parts)
            
            # 프롬프트 구성
            prompt = f"""다음 참고 문서를 바탕으로 질문에 답변해주세요.

참고 문서:
{context}

질문: {question}

답변 규칙:
1. 참고 문서에 명시된 정보만 사용하세요
2. 문서에서 확인할 수 없는 내용은 추론하지 마세요
3. 한국어로 명확하게 답변하세요
4. 가능하면 출처를 언급해주세요

답변:"""
            
            return self.generate_response(prompt)
            
        except Exception as e:
            return f"❌ 질의 처리 중 오류: {str(e)}"
    
    def mimic_style(self, content: str) -> str:
        """문체 모방 생성"""
        if not self.is_initialized:
            return "❌ AI 엔진이 초기화되지 않았습니다."
        
        try:
            # 스타일 참조를 위한 문서 검색
            search_results = self.search_documents(content)
            
            if not search_results:
                return "❌ 참조할 문서를 찾을 수 없습니다."
            
            # 컨텍스트 구성
            context_parts = []
            for result in search_results:
                context_parts.append(result['text'])
            
            context = "\n\n".join(context_parts)
            
            # 스타일 모방 프롬프트
            prompt = f"""다음 참고 문서의 문체를 분석하고 모방하여 입력 내용을 재작성해주세요.

참고 문서:
{context}

입력 내용: {content}

작업 순서:
1. 참고 문서의 문체(어휘, 문장 구조, 톤앤매너) 분석
2. 핵심 스타일 규칙 정의
3. 입력 내용을 해당 스타일로 재작성

재작성된 결과:"""
            
            return self.generate_response(prompt)
            
        except Exception as e:
            return f"❌ 문체 모방 중 오류: {str(e)}"
    
    def get_system_info(self) -> Dict:
        """시스템 정보 반환"""
        return {
            'is_initialized': self.is_initialized,
            'device': self.device,
            'model_name': config.model.llm_model,
            'embedding_model': config.model.embedding_model,
            'document_count': len(self.texts),
            'has_vector_db': self.index is not None
        }

# 전역 AI 엔진 인스턴스
ai_engine = None

def get_ai_engine() -> AIEngine:
    """AI 엔진 인스턴스 반환"""
    global ai_engine
    if ai_engine is None:
        ai_engine = AIEngine()
    return ai_engine