# main.py
"""
FAISS 기반 로컬 RAG 시스템 메인 실행 스크립트
내용 기반 질의응답과 문체 모방 생성 기능을 제공합니다.
"""

import os
import pickle
import numpy as np
import faiss
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import warnings

# FutureWarning 숨기기
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

class LocalMindSystem:
    """LocalMind - 로컬 AI 문서 어시스턴트 시스템 클래스"""
    
    def __init__(self, faiss_path="document_memory.faiss", data_path="document_memory.pkl"):
        """시스템 초기화"""
        self.faiss_path = faiss_path
        self.data_path = data_path
        self.model = None
        self.tokenizer = None
        self.embedding_model = None
        self.index = None
        self.texts = []
        self.metadatas = []
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self._initialize_system()
    
    def _initialize_system(self):
        """시스템 컴포넌트 초기화"""
        try:
            print("🚀 LocalMind 시스템을 초기화합니다...")
            
            # 데이터베이스 파일 존재 확인
            if not os.path.exists(self.faiss_path) or not os.path.exists(self.data_path):
                print(f"❌ 데이터베이스 파일이 존재하지 않습니다.")
                print("   먼저 'python create_db.py'를 실행하여 데이터베이스를 생성해주세요.")
                return
            
            # LLM 초기화
            print("1. LLM 모델을 초기화합니다... (EXAONE-4.0-1.2B)")
            print(f"   사용 디바이스: {self.device}")
            
            model_name = "LGAI-EXAONE/EXAONE-4.0-1.2B"
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            
            # 모델 로드
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True
            )
            
            # 임베딩 모델 초기화
            print("2. 임베딩 모델을 초기화합니다...")
            self.embedding_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
            
            # FAISS 인덱스 로드
            print("3. FAISS 인덱스를 로드합니다...")
            self.index = faiss.read_index(self.faiss_path)
            
            # 텍스트 데이터 로드
            print("4. 텍스트 데이터를 로드합니다...")
            with open(self.data_path, "rb") as f:
                data = pickle.load(f)
                self.texts = data["texts"]
                self.metadatas = data["metadatas"]
            
            print(f"   ✅ {len(self.texts)}개의 문서가 로드되었습니다.")
            print("✅ 시스템 초기화가 완료되었습니다!")
            
        except Exception as e:
            print(f"❌ 시스템 초기화 중 오류가 발생했습니다: {str(e)}")
            print("   - 인터넷 연결이 안정적인지 확인해주세요 (모델 다운로드)")
            print("   - GPU 메모리가 충분한지 확인해주세요 (최소 4GB 권장)")
            print("   - HuggingFace 토큰이 필요할 수 있습니다")
            import traceback
            traceback.print_exc()
    
    def _get_relevant_context(self, query, top_k=5):
        """관련 문서 검색"""
        try:
            if not self.embedding_model or not self.index:
                return ""
            
            # 쿼리를 벡터로 변환
            query_embedding = self.embedding_model.get_text_embedding(query)
            query_vector = np.array([query_embedding]).astype('float32')
            
            # FAISS로 유사한 문서 검색
            scores, indices = self.index.search(query_vector, top_k)
            
            # 관련 텍스트 수집
            context_parts = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.texts) and score > 0.1:  # 유사도 임계값
                    text = self.texts[idx]
                    metadata = self.metadatas[idx]
                    context_parts.append(f"[출처: {metadata['source']}] {text}")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            print(f"검색 중 오류: {e}")
            return ""
    
    def _generate_response(self, prompt):
        """EXAONE 모델로 응답 생성"""
        try:
            if not self.model or not self.tokenizer:
                return "❌ 모델이 초기화되지 않았습니다."
            
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
                    max_new_tokens=512,
                    temperature=0.1,
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
    
    def ask_content(self, question):
        """내용 기반 질의응답"""
        if not self.model or not self.embedding_model:
            return "❌ 시스템이 초기화되지 않았습니다."
        
        try:
            print(f"\n🔍 내용 검색 중: {question}")
            
            # 관련 문서 검색
            context = self._get_relevant_context(question)
            
            if not context:
                return "❌ 관련 문서를 찾을 수 없습니다."
            
            # 내용 필사 프롬프트
            prompt = f"""다음 참고 문서를 바탕으로 질문에 답변해주세요.

참고 문서:
{context}

질문: {question}

답변 규칙:
1. 참고 문서에 명시된 정보만 사용하세요
2. 문서에서 확인할 수 없는 내용은 추론하지 마세요
3. 한국어로 명확하게 답변하세요"""
            
            response = self._generate_response(prompt)
            return response
            
        except Exception as e:
            return f"❌ 질의 처리 중 오류가 발생했습니다: {str(e)}"
    
    def mimic_style(self, content):
        """문체 모방 생성"""
        if not self.model or not self.embedding_model:
            return "❌ 시스템이 초기화되지 않았습니다."
        
        try:
            print(f"\n✍️ 문체 모방 중: {content[:50]}...")
            
            # 스타일 참조를 위한 문서 검색
            context = self._get_relevant_context(content)
            
            if not context:
                return "❌ 참조할 문서를 찾을 수 없습니다."
            
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
            
            response = self._generate_response(prompt)
            return response
            
        except Exception as e:
            return f"❌ 문체 모방 중 오류가 발생했습니다: {str(e)}"

def main():
    """메인 실행 함수"""
    
    # 시스템 초기화
    localmind = LocalMindSystem()
    
    if not localmind.model:
        print("시스템 초기화에 실패했습니다. 프로그램을 종료합니다.")
        return
    
    print("\n" + "="*60)
    print("🧠 LocalMind - 로컬 AI 문서 어시스턴트")
    print("="*60)
    print("1. 내용 질의응답 테스트")
    print("2. 문체 모방 테스트")
    print("="*60)
    
    # 기능 테스트 실행
    print("\n📋 기능 테스트를 시작합니다...")
    
    # 1. 내용 기반 질의응답 테스트
    test_questions = [
        "문서의 주요 내용은 무엇인가요?",
        "핵심 키워드나 개념을 설명해주세요.",
        "문서에서 가장 중요한 결론은 무엇인가요?"
    ]
    
    print("\n🔍 내용 기반 질의응답 테스트:")
    for i, question in enumerate(test_questions, 1):
        print(f"\n[테스트 {i}] {question}")
        answer = localmind.ask_content(question)
        print(f"[답변] {answer}")
        print("-" * 40)
    
    # 2. 문체 모방 테스트
    test_contents = [
        "이 보고서를 간결하고 전문적인 톤으로 요약하시오.",
        "다음 내용을 학술적인 문체로 재작성해주세요: 인공지능 기술이 발전하고 있다.",
        "비즈니스 제안서 형태로 다음을 작성해주세요: 새로운 프로젝트 아이디어"
    ]
    
    print("\n✍️ 문체 모방 테스트:")
    for i, content in enumerate(test_contents, 1):
        print(f"\n[테스트 {i}] {content}")
        result = localmind.mimic_style(content)
        print(f"[결과] {result}")
        print("-" * 40)
    
    print("\n✅ 모든 테스트가 완료되었습니다!")

if __name__ == "__main__":
    main()