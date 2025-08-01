# setup_guide.py
"""
Memvid RAG 시스템 설정 가이드 및 환경 검증 스크립트
"""

import os
import subprocess
import sys

def check_python_version():
    """Python 버전 확인"""
    version = sys.version_info
    print(f"🐍 Python 버전: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        return False
    else:
        print("✅ Python 버전이 적합합니다.")
        return True

def check_gpu():
    """GPU 확인"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"🎮 GPU: {gpu_name}")
            print(f"📊 GPU 메모리: {gpu_memory:.1f}GB")
            
            if gpu_memory >= 7.5:  # RTX 3060 Ti는 8GB
                print("✅ GPU 메모리가 충분합니다.")
                return True
            else:
                print("⚠️ GPU 메모리가 부족할 수 있습니다. (권장: 8GB 이상)")
                return True
        else:
            print("❌ CUDA GPU를 찾을 수 없습니다.")
            return False
    except ImportError:
        print("❌ PyTorch가 설치되지 않았습니다.")
        return False

def check_huggingface_model():
    """HuggingFace 모델 접근 확인"""
    try:
        import transformers
        from transformers import AutoTokenizer
        
        print("✅ Transformers 라이브러리가 설치되어 있습니다.")
        
        # 모델 접근 테스트 (토크나이저만 로드)
        print("   EXAONE-4.0-1.2B 모델 접근을 확인합니다...")
        tokenizer = AutoTokenizer.from_pretrained(
            "LGAI-EXAONE/EXAONE-4.0-1.2B",
            trust_remote_code=True
        )
        print("✅ EXAONE-4.0-1.2B 모델에 접근할 수 있습니다.")
        return True
        
    except ImportError:
        print("❌ Transformers 라이브러리가 설치되지 않았습니다.")
        return False
    except Exception as e:
        print(f"❌ 모델 접근 중 오류: {str(e)}")
        print("   - 인터넷 연결을 확인해주세요")
        print("   - HuggingFace 토큰이 필요할 수 있습니다")
        return False

def check_required_packages():
    """필수 패키지 설치 확인"""
    required_packages = [
        'memvid',
        'llama-index',
        'llama-index-llms-ollama',
        'llama-index-embeddings-huggingface',
        'kss',
        'evaluate',
        'nltk',
        'torch',
        'transformers'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n다음 패키지들을 설치해야 합니다:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    else:
        print("✅ 모든 필수 패키지가 설치되어 있습니다.")
        return True

def check_data_folder():
    """데이터 폴더 및 파일 확인"""
    if os.path.exists('./data'):
        files = os.listdir('./data')
        document_files = [f for f in files if f.endswith(('.pdf', '.txt', '.md')) and f != 'README.md']
        
        if document_files:
            print(f"✅ data 폴더에 {len(document_files)}개의 문서가 있습니다:")
            for file in document_files:
                print(f"   - {file}")
            return True
        else:
            print("⚠️ data 폴더에 분석할 문서가 없습니다.")
            print("   PDF, TXT, MD 파일을 data 폴더에 추가해주세요.")
            return False
    else:
        print("❌ data 폴더가 존재하지 않습니다.")
        return False

def main():
    """메인 검증 함수"""
    print("🔍 Memvid RAG 시스템 환경 검증을 시작합니다...\n")
    
    checks = [
        ("Python 버전", check_python_version),
        ("GPU 환경", check_gpu),
        ("HuggingFace 모델", check_huggingface_model),
        ("필수 패키지", check_required_packages),
        ("데이터 폴더", check_data_folder)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name} 확인 중...")
        result = check_func()
        results.append((check_name, result))
        print("-" * 50)
    
    # 결과 요약
    print("\n📊 환경 검증 결과:")
    all_passed = True
    
    for check_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {check_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 모든 환경 검증을 통과했습니다!")
        print("이제 다음 단계를 진행하세요:")
        print("1. python create_db.py  # 데이터베이스 생성")
        print("2. python main.py       # 시스템 실행")
        print("3. python evaluation.py # 성능 평가")
        print("\n💡 사용 중인 모델: EXAONE-4.0-1.2B (LG AI Research)")
    else:
        print("\n⚠️ 일부 환경 설정이 필요합니다.")
        print("위의 실패 항목들을 해결한 후 다시 실행해주세요.")

if __name__ == "__main__":
    main()