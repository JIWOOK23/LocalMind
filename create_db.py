# create_db.py
"""
벡터 데이터베이스 생성 스크립트
원본 문서들을 벡터화하여 FAISS 인덱스로 저장합니다.
"""

import os
import json
import pickle
from llama_index.core import SimpleDirectoryReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import kss
import faiss
import numpy as np

def create_database():
    """벡터 데이터베이스 생성 메인 함수"""
    
    # data 폴더 존재 확인
    if not os.path.exists("./data"):
        print("❌ data 폴더가 존재하지 않습니다. data 폴더를 생성하고 문서를 추가해주세요.")
        os.makedirs("./data")
        print("✅ data 폴더를 생성했습니다. 분석할 문서들을 data 폴더에 넣어주세요.")
        return
    
    # 문서 파일 확인
    files = os.listdir("./data")
    document_files = [f for f in files if f.endswith(('.pdf', '.txt', '.md')) and f != 'README.md']
    if not document_files:
        print("❌ data 폴더에 문서가 없습니다. PDF, TXT 등의 문서를 추가해주세요.")
        return
    
    print(f"📁 발견된 문서 파일: {document_files}")
    
    try:
        print("1. 원본 문서 로딩을 시작합니다...")
        documents = SimpleDirectoryReader("./data").load_data()
        print(f"   ✅ {len(documents)}개의 문서를 로딩했습니다.")
        
        print("2. kss 라이브러리를 통해 한국어 문장을 분리합니다...")
        texts = []
        metadatas = []
        
        for doc in documents:
            # README.md 파일 제외
            if doc.metadata.get("file_name", "") == "README.md":
                continue
                
            sentences = kss.split_sentences(doc.text)
            
            for sentence in sentences:
                if sentence.strip() and len(sentence.strip()) > 10:  # 너무 짧은 문장 제외
                    texts.append(sentence.strip())
                    metadatas.append({
                        "source": doc.metadata.get("file_name", "N/A"),
                        "length": len(sentence.strip())
                    })
        
        print(f"   ✅ 총 {len(texts)}개의 문장으로 분리했습니다.")
        
        if not texts:
            print("❌ 처리할 텍스트가 없습니다.")
            return
        
        print("3. 임베딩 모델을 초기화합니다...")
        embedding_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
        
        print("4. 텍스트를 벡터로 변환합니다...")
        print("   (이 과정은 문서 크기에 따라 시간이 걸릴 수 있습니다)")
        
        embeddings = []
        batch_size = 32
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = embedding_model.get_text_embedding_batch(batch_texts)
            embeddings.extend(batch_embeddings)
            print(f"   진행률: {min(i+batch_size, len(texts))}/{len(texts)}")
        
        print("5. FAISS 인덱스를 생성합니다...")
        embeddings_array = np.array(embeddings).astype('float32')
        dimension = embeddings_array.shape[1]
        
        # FAISS 인덱스 생성
        index = faiss.IndexFlatIP(dimension)  # 내적 유사도 사용
        index.add(embeddings_array)
        
        print("6. 데이터베이스 파일을 저장합니다...")
        
        # FAISS 인덱스 저장
        faiss.write_index(index, "document_memory.faiss")
        
        # 텍스트와 메타데이터 저장
        with open("document_memory.pkl", "wb") as f:
            pickle.dump({
                "texts": texts,
                "metadatas": metadatas,
                "embedding_model": "BAAI/bge-m3"
            }, f)
        
        print("✅ 벡터 데이터베이스 생성이 완료되었습니다!")
        print(f"📊 처리된 문장 수: {len(texts)}")
        print(f"📊 벡터 차원: {dimension}")
        
        # 생성된 파일 크기 확인
        faiss_size = os.path.getsize("document_memory.faiss") / (1024 * 1024)
        pkl_size = os.path.getsize("document_memory.pkl") / (1024 * 1024)
        print(f"📊 FAISS 인덱스 크기: {faiss_size:.2f} MB")
        print(f"📊 텍스트 데이터 크기: {pkl_size:.2f} MB")
        
    except Exception as e:
        print(f"❌ 데이터베이스 생성 중 오류가 발생했습니다: {str(e)}")
        print("   - 필요한 패키지가 모두 설치되었는지 확인해주세요")
        print("   - GPU 메모리가 충분한지 확인해주세요")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_database()