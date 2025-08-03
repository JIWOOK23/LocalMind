"""
문서 처리 서비스 - 고도화된 문서 관리
"""

import os
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import mimetypes
from datetime import datetime

# 문서 처리 라이브러리
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core.text_splitter import SentenceSplitter
import kss
import faiss
import numpy as np
import pickle

from config.settings import config
from src.services.database_service import db_service
from src.core.ai_engine import get_ai_engine

class DocumentProcessor:
    """문서 처리기"""
    
    def __init__(self):
        self.supported_formats = config.processing.supported_formats
        self.max_file_size = config.processing.max_file_size
        self.chunk_size = config.processing.chunk_size
        self.chunk_overlap = config.processing.chunk_overlap
        self.batch_size = config.processing.batch_size
    
    def validate_file(self, filepath: str) -> Tuple[bool, str]:
        """파일 유효성 검사"""
        if not os.path.exists(filepath):
            return False, "파일이 존재하지 않습니다."
        
        # 파일 크기 확인
        file_size = os.path.getsize(filepath)
        if file_size > self.max_file_size:
            return False, f"파일 크기가 너무 큽니다. (최대: {self.max_file_size // (1024*1024)}MB)"
        
        # 파일 형식 확인
        file_ext = Path(filepath).suffix.lower()
        if file_ext not in self.supported_formats:
            return False, f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(self.supported_formats)}"
        
        return True, "유효한 파일입니다."
    
    def calculate_file_hash(self, filepath: str) -> str:
        """파일 해시 계산"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def extract_text(self, filepath: str) -> List[Document]:
        """텍스트 추출"""
        try:
            # SimpleDirectoryReader로 문서 로드
            documents = SimpleDirectoryReader(
                input_files=[filepath]
            ).load_data()
            
            return documents
            
        except Exception as e:
            raise Exception(f"텍스트 추출 실패: {str(e)}")
    
    def split_text(self, documents: List[Document]) -> List[Dict]:
        """텍스트 분할"""
        chunks = []
        
        for doc in documents:
            # 한국어 문장 분리
            sentences = kss.split_sentences(doc.text)
            
            # 청크 단위로 분할
            current_chunk = ""
            current_length = 0
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence or len(sentence) < 10:
                    continue
                
                # 청크 크기 확인
                if current_length + len(sentence) > self.chunk_size and current_chunk:
                    # 현재 청크 저장
                    chunks.append({
                        'text': current_chunk.strip(),
                        'metadata': {
                            'source': doc.metadata.get('file_name', 'Unknown'),
                            'chunk_id': len(chunks),
                            'length': len(current_chunk.strip())
                        }
                    })
                    
                    # 새 청크 시작 (오버랩 고려)
                    if self.chunk_overlap > 0:
                        overlap_text = current_chunk[-self.chunk_overlap:]
                        current_chunk = overlap_text + " " + sentence
                        current_length = len(current_chunk)
                    else:
                        current_chunk = sentence
                        current_length = len(sentence)
                else:
                    current_chunk += " " + sentence
                    current_length += len(sentence)
            
            # 마지막 청크 저장
            if current_chunk.strip():
                chunks.append({
                    'text': current_chunk.strip(),
                    'metadata': {
                        'source': doc.metadata.get('file_name', 'Unknown'),
                        'chunk_id': len(chunks),
                        'length': len(current_chunk.strip())
                    }
                })
        
        return chunks
    
    def create_embeddings(self, chunks: List[Dict]) -> np.ndarray:
        """임베딩 생성"""
        ai_engine = get_ai_engine()
        
        if not ai_engine.embedding_model:
            raise Exception("임베딩 모델이 초기화되지 않았습니다.")
        
        embeddings = []
        texts = [chunk['text'] for chunk in chunks]
        
        # 배치 단위로 처리
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_embeddings = ai_engine.embedding_model.get_text_embedding_batch(batch_texts)
            embeddings.extend(batch_embeddings)
            
            print(f"   임베딩 진행률: {min(i + self.batch_size, len(texts))}/{len(texts)}")
        
        return np.array(embeddings).astype('float32')

class DocumentService:
    """문서 서비스"""
    
    def __init__(self):
        self.processor = DocumentProcessor()
        self.upload_dir = Path("data/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def upload_document(self, file_content: bytes, filename: str) -> Dict:
        """문서 업로드"""
        try:
            # 파일 저장
            filepath = self.upload_dir / filename
            with open(filepath, 'wb') as f:
                f.write(file_content)
            
            # 파일 유효성 검사
            is_valid, message = self.processor.validate_file(str(filepath))
            if not is_valid:
                os.remove(filepath)
                return {'success': False, 'message': message}
            
            # 파일 정보 수집
            file_size = len(file_content)
            file_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            file_hash = self.processor.calculate_file_hash(str(filepath))
            
            # 중복 파일 확인
            existing_docs = db_service.get_documents()
            for doc in existing_docs:
                if doc['hash'] == file_hash:
                    os.remove(filepath)
                    return {
                        'success': False, 
                        'message': f"동일한 파일이 이미 존재합니다: {doc['filename']}"
                    }
            
            # 데이터베이스에 저장
            doc_id = db_service.add_document(
                filename=filename,
                filepath=str(filepath),
                file_type=file_type,
                file_size=file_size,
                file_hash=file_hash
            )
            
            return {
                'success': True,
                'message': f'파일 "{filename}"이 성공적으로 업로드되었습니다.',
                'document_id': doc_id
            }
            
        except Exception as e:
            return {'success': False, 'message': f'업로드 실패: {str(e)}'}
    
    def process_document(self, doc_id: str) -> Dict:
        """문서 처리"""
        start_time = time.time()
        
        try:
            # 문서 정보 조회
            documents = db_service.get_documents()
            doc_info = next((d for d in documents if d['id'] == doc_id), None)
            
            if not doc_info:
                return {'success': False, 'message': '문서를 찾을 수 없습니다.'}
            
            if doc_info['processed']:
                return {'success': False, 'message': '이미 처리된 문서입니다.'}
            
            filepath = doc_info['filepath']
            
            print(f"📄 문서 처리 시작: {doc_info['filename']}")
            
            # 1. 텍스트 추출
            print("1. 텍스트 추출 중...")
            documents = self.processor.extract_text(filepath)
            
            # 2. 텍스트 분할
            print("2. 텍스트 분할 중...")
            chunks = self.processor.split_text(documents)
            
            if not chunks:
                return {'success': False, 'message': '처리할 텍스트가 없습니다.'}
            
            # 3. 임베딩 생성
            print("3. 임베딩 생성 중...")
            embeddings = self.processor.create_embeddings(chunks)
            
            # 4. 벡터 데이터베이스 업데이트
            print("4. 벡터 데이터베이스 업데이트 중...")
            self._update_vector_database(chunks, embeddings)
            
            # 5. 처리 완료 상태 업데이트
            processing_time = time.time() - start_time
            db_service.update_document_processed(
                doc_id=doc_id,
                processed=True,
                processing_time=processing_time,
                chunk_count=len(chunks)
            )
            
            # 로그 기록
            db_service.add_log(
                level='INFO',
                message=f'문서 처리 완료: {doc_info["filename"]}',
                module='DocumentService',
                metadata={
                    'document_id': doc_id,
                    'chunk_count': len(chunks),
                    'processing_time': processing_time
                }
            )
            
            print(f"✅ 문서 처리 완료! ({processing_time:.2f}초)")
            
            return {
                'success': True,
                'message': f'문서 "{doc_info["filename"]}" 처리가 완료되었습니다.',
                'chunk_count': len(chunks),
                'processing_time': processing_time
            }
            
        except Exception as e:
            # 오류 로그 기록
            db_service.add_log(
                level='ERROR',
                message=f'문서 처리 실패: {str(e)}',
                module='DocumentService',
                metadata={'document_id': doc_id}
            )
            
            return {'success': False, 'message': f'문서 처리 실패: {str(e)}'}
    
    def _update_vector_database(self, chunks: List[Dict], embeddings: np.ndarray):
        """벡터 데이터베이스 업데이트"""
        faiss_path = config.database.faiss_index_path
        data_path = config.database.text_data_path
        
        # 기존 데이터 로드
        existing_texts = []
        existing_metadatas = []
        existing_embeddings = None
        
        if os.path.exists(faiss_path) and os.path.exists(data_path):
            # 기존 FAISS 인덱스 로드
            existing_index = faiss.read_index(faiss_path)
            existing_embeddings = np.zeros((existing_index.ntotal, existing_index.d), dtype=np.float32)
            existing_index.reconstruct_n(0, existing_index.ntotal, existing_embeddings)
            
            # 기존 텍스트 데이터 로드
            with open(data_path, 'rb') as f:
                data = pickle.load(f)
                existing_texts = data['texts']
                existing_metadatas = data['metadatas']
        
        # 새 데이터 추가
        new_texts = [chunk['text'] for chunk in chunks]
        new_metadatas = [chunk['metadata'] for chunk in chunks]
        
        all_texts = existing_texts + new_texts
        all_metadatas = existing_metadatas + new_metadatas
        
        # 임베딩 결합
        if existing_embeddings is not None:
            all_embeddings = np.vstack([existing_embeddings, embeddings])
        else:
            all_embeddings = embeddings
        
        # 새 FAISS 인덱스 생성
        dimension = all_embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(all_embeddings)
        
        # 저장
        os.makedirs(os.path.dirname(faiss_path), exist_ok=True)
        faiss.write_index(index, faiss_path)
        
        with open(data_path, 'wb') as f:
            pickle.dump({
                'texts': all_texts,
                'metadatas': all_metadatas,
                'embedding_model': config.model.embedding_model
            }, f)
    
    def delete_document(self, doc_id: str) -> Dict:
        """문서 삭제"""
        try:
            success = db_service.delete_document(doc_id)
            
            if success:
                # TODO: 벡터 데이터베이스에서도 해당 문서의 청크들 제거
                # 현재는 전체 재구축이 필요함
                
                db_service.add_log(
                    level='INFO',
                    message=f'문서 삭제 완료: {doc_id}',
                    module='DocumentService'
                )
                
                return {'success': True, 'message': '문서가 삭제되었습니다.'}
            else:
                return {'success': False, 'message': '문서를 찾을 수 없습니다.'}
                
        except Exception as e:
            return {'success': False, 'message': f'삭제 실패: {str(e)}'}
    
    def get_document_stats(self) -> Dict:
        """문서 통계"""
        documents = db_service.get_documents()
        
        total_count = len(documents)
        processed_count = sum(1 for doc in documents if doc['processed'])
        total_size = sum(doc['file_size'] for doc in documents)
        total_chunks = sum(doc['chunk_count'] or 0 for doc in documents)
        
        # 파일 형식별 통계
        format_stats = {}
        for doc in documents:
            ext = Path(doc['filename']).suffix.lower()
            format_stats[ext] = format_stats.get(ext, 0) + 1
        
        return {
            'total_documents': total_count,
            'processed_documents': processed_count,
            'pending_documents': total_count - processed_count,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'total_chunks': total_chunks,
            'format_distribution': format_stats
        }
    
    def rebuild_vector_database(self) -> Dict:
        """벡터 데이터베이스 재구축"""
        try:
            print("🔄 벡터 데이터베이스 재구축 시작...")
            
            # 처리된 문서들 조회
            documents = db_service.get_documents(processed_only=True)
            
            if not documents:
                return {'success': False, 'message': '처리된 문서가 없습니다.'}
            
            all_chunks = []
            all_embeddings = []
            
            for doc in documents:
                print(f"📄 처리 중: {doc['filename']}")
                
                # 문서 재처리
                doc_chunks = self.processor.split_text(
                    self.processor.extract_text(doc['filepath'])
                )
                
                chunk_embeddings = self.processor.create_embeddings(doc_chunks)
                
                all_chunks.extend(doc_chunks)
                all_embeddings.append(chunk_embeddings)
            
            # 임베딩 결합
            combined_embeddings = np.vstack(all_embeddings)
            
            # 벡터 데이터베이스 업데이트
            self._update_vector_database(all_chunks, combined_embeddings)
            
            print("✅ 벡터 데이터베이스 재구축 완료!")
            
            return {
                'success': True,
                'message': f'벡터 데이터베이스가 재구축되었습니다. (총 {len(all_chunks)}개 청크)',
                'chunk_count': len(all_chunks)
            }
            
        except Exception as e:
            return {'success': False, 'message': f'재구축 실패: {str(e)}'}

# 전역 문서 서비스 인스턴스
document_service = DocumentService()