# evaluation.py
"""
Memvid RAG 시스템 성능 평가 스크립트
ROUGE, BLEU 점수 및 문체 유사도를 측정합니다.
"""

import json
import time
from datetime import datetime
from main import LocalMindSystem
import evaluate
import nltk
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# NLTK 데이터 다운로드 (최초 실행시)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class LocalMindEvaluator:
    """LocalMind 시스템 성능 평가 클래스"""
    
    def __init__(self):
        """평가기 초기화"""
        self.localmind = LocalMindSystem()
        self.rouge = evaluate.load('rouge')
        self.bleu = evaluate.load('bleu')
        self.results = {
            'content_qa': [],
            'style_mimicking': [],
            'evaluation_time': datetime.now().isoformat()
        }
    
    def create_test_dataset(self):
        """테스트 데이터셋 생성"""
        
        # 내용 기반 질의응답 테스트 데이터
        content_qa_tests = [
            {
                'question': '문서의 주요 목적은 무엇인가요?',
                'reference': '문서의 주요 목적을 설명하는 참조 답변'
            },
            {
                'question': '핵심 개념이나 용어를 설명해주세요.',
                'reference': '핵심 개념에 대한 참조 설명'
            },
            {
                'question': '문서에서 제시하는 해결책은 무엇인가요?',
                'reference': '제시된 해결책에 대한 참조 답변'
            },
            {
                'question': '결론 부분의 주요 내용은 무엇인가요?',
                'reference': '결론 부분의 주요 내용 참조'
            },
            {
                'question': '문서에서 강조하는 중요한 포인트는?',
                'reference': '중요한 포인트에 대한 참조 답변'
            }
        ]
        
        # 문체 모방 테스트 데이터
        style_mimicking_tests = [
            {
                'input': '인공지능 기술이 빠르게 발전하고 있습니다.',
                'reference': '원본 문서 스타일로 재작성된 참조 텍스트'
            },
            {
                'input': '새로운 프로젝트를 시작하려고 합니다.',
                'reference': '원본 문서 스타일로 재작성된 참조 텍스트'
            },
            {
                'input': '데이터 분석 결과를 보고하겠습니다.',
                'reference': '원본 문서 스타일로 재작성된 참조 텍스트'
            },
            {
                'input': '시스템 성능이 향상되었습니다.',
                'reference': '원본 문서 스타일로 재작성된 참조 텍스트'
            },
            {
                'input': '사용자 피드백을 수집했습니다.',
                'reference': '원본 문서 스타일로 재작성된 참조 텍스트'
            }
        ]
        
        return content_qa_tests, style_mimicking_tests
    
    def evaluate_content_qa(self, test_data):
        """내용 기반 질의응답 평가"""
        print("\n🔍 내용 기반 질의응답 성능 평가 중...")
        
        for i, test_case in enumerate(test_data, 1):
            print(f"  테스트 {i}/{len(test_data)} 진행 중...")
            
            start_time = time.time()
            generated_answer = self.localmind.ask_content(test_case['question'])
            response_time = time.time() - start_time
            
            # ROUGE 점수 계산
            rouge_scores = self.rouge.compute(
                predictions=[generated_answer],
                references=[test_case['reference']]
            )
            
            # BLEU 점수 계산
            bleu_score = self.bleu.compute(
                predictions=[generated_answer.split()],
                references=[[test_case['reference'].split()]]
            )
            
            # 결과 저장
            result = {
                'test_id': i,
                'question': test_case['question'],
                'generated_answer': generated_answer,
                'reference_answer': test_case['reference'],
                'rouge_scores': rouge_scores,
                'bleu_score': bleu_score['bleu'],
                'response_time': response_time
            }
            
            self.results['content_qa'].append(result)
        
        print("  ✅ 내용 기반 질의응답 평가 완료")
    
    def evaluate_style_mimicking(self, test_data):
        """문체 모방 성능 평가"""
        print("\n✍️ 문체 모방 성능 평가 중...")
        
        for i, test_case in enumerate(test_data, 1):
            print(f"  테스트 {i}/{len(test_data)} 진행 중...")
            
            start_time = time.time()
            generated_text = self.localmind.mimic_style(test_case['input'])
            response_time = time.time() - start_time
            
            # 문체 유사도 계산 (TF-IDF 기반 코사인 유사도)
            style_similarity = self.calculate_style_similarity(
                generated_text, 
                test_case['reference']
            )
            
            # ROUGE 점수 계산 (내용 보존도 측정)
            rouge_scores = self.rouge.compute(
                predictions=[generated_text],
                references=[test_case['reference']]
            )
            
            # 결과 저장
            result = {
                'test_id': i,
                'input_text': test_case['input'],
                'generated_text': generated_text,
                'reference_text': test_case['reference'],
                'style_similarity': style_similarity,
                'rouge_scores': rouge_scores,
                'response_time': response_time
            }
            
            self.results['style_mimicking'].append(result)
        
        print("  ✅ 문체 모방 평가 완료")
    
    def calculate_style_similarity(self, text1, text2):
        """TF-IDF 기반 문체 유사도 계산"""
        try:
            vectorizer = TfidfVectorizer(max_features=1000, stop_words=None)
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except:
            return 0.0
    
    def calculate_average_scores(self):
        """평균 점수 계산"""
        print("\n📊 평균 성능 지표 계산 중...")
        
        # 내용 기반 질의응답 평균 점수
        if self.results['content_qa']:
            content_qa_rouge1 = sum(r['rouge_scores']['rouge1'] for r in self.results['content_qa']) / len(self.results['content_qa'])
            content_qa_rouge2 = sum(r['rouge_scores']['rouge2'] for r in self.results['content_qa']) / len(self.results['content_qa'])
            content_qa_rougeL = sum(r['rouge_scores']['rougeL'] for r in self.results['content_qa']) / len(self.results['content_qa'])
            content_qa_bleu = sum(r['bleu_score'] for r in self.results['content_qa']) / len(self.results['content_qa'])
            content_qa_time = sum(r['response_time'] for r in self.results['content_qa']) / len(self.results['content_qa'])
            
            print(f"  내용 기반 질의응답 평균 성능:")
            print(f"    - ROUGE-1: {content_qa_rouge1:.4f}")
            print(f"    - ROUGE-2: {content_qa_rouge2:.4f}")
            print(f"    - ROUGE-L: {content_qa_rougeL:.4f}")
            print(f"    - BLEU: {content_qa_bleu:.4f}")
            print(f"    - 평균 응답 시간: {content_qa_time:.2f}초")
        
        # 문체 모방 평균 점수
        if self.results['style_mimicking']:
            style_similarity = sum(r['style_similarity'] for r in self.results['style_mimicking']) / len(self.results['style_mimicking'])
            style_rouge1 = sum(r['rouge_scores']['rouge1'] for r in self.results['style_mimicking']) / len(self.results['style_mimicking'])
            style_time = sum(r['response_time'] for r in self.results['style_mimicking']) / len(self.results['style_mimicking'])
            
            print(f"  문체 모방 평균 성능:")
            print(f"    - 문체 유사도: {style_similarity:.4f}")
            print(f"    - ROUGE-1 (내용 보존): {style_rouge1:.4f}")
            print(f"    - 평균 응답 시간: {style_time:.2f}초")
    
    def save_results(self, filename="evaluation_results.json"):
        """평가 결과 저장"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 평가 결과가 {filename}에 저장되었습니다.")
    
    def run_evaluation(self):
        """전체 평가 실행"""
        print("🚀 LocalMind 시스템 성능 평가를 시작합니다...")
        
        if not self.localmind.model:
            print("❌ LocalMind 시스템 초기화에 실패했습니다.")
            return
        
        # 테스트 데이터셋 생성
        content_qa_tests, style_mimicking_tests = self.create_test_dataset()
        
        # 평가 실행
        self.evaluate_content_qa(content_qa_tests)
        self.evaluate_style_mimicking(style_mimicking_tests)
        
        # 결과 분석
        self.calculate_average_scores()
        
        # 결과 저장
        self.save_results()
        
        print("\n✅ 모든 평가가 완료되었습니다!")

def main():
    """메인 실행 함수"""
    evaluator = LocalMindEvaluator()
    evaluator.run_evaluation()

if __name__ == "__main__":
    main()