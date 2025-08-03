<div align="center">

![LocalMind Logo](Gemini_Generated_Image_t7sbxkt7sbxkt7sb.png)

# 🧠 LocalMind
### *로컬 AI 문서 어시스턴트*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![EXAONE](https://img.shields.io/badge/Model-EXAONE--4.0--1.2B-green.svg)](https://huggingface.co/LGAI-EXAONE/EXAONE-4.0-1.2B)
[![GPU](https://img.shields.io/badge/GPU-RTX%203060%20Ti-orange.svg)](https://www.nvidia.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**개인 컴퓨터에서 완전히 독립적으로 실행되는 지능형 문서 분석 및 질의응답 시스템**

[🚀 빠른 시작](#-설치-및-실행) • [📖 사용법](#-사용법) • [🛠️ 기술 스택](TECH_STACK.md) • [❓ 문제 해결](#-문제-해결)

</div>

---

## ✨ LocalMind란?

LocalMind는 **NVIDIA GeForce RTX 3060 Ti (8GB VRAM)** 환경에서 작동하는 한국어 특화 로컬 RAG 시스템입니다. 서버 없이 개인 컴퓨터에서 완전히 독립적으로 실행되며, 문서를 분석하고 질문에 답변하는 지능형 AI 어시스턴트입니다.

## 🎯 주요 기능

<table>
<tr>
<td width="33%">

### � GUI 반채팅 인터페이스
- Claude Desktop 스타일의 직관적 UI
- 실시간 채팅 및 대화 히스토리 관리
- 드래그앤드롭 파일 업로드

</td>
<td width="33%">

### 📝 내용 기반 질의응답
- 업로드한 문서 내용을 정확히 분석
- 문서에 기반한 신뢰할 수 있는 답변 제공
- 출처 정보와 함께 상세한 응답

</td>
<td width="33%">

### 🎨 문체 모방 생성
- 원본 문서의 문체와 톤앤매너 분석
- 학습된 스타일로 새로운 텍스트 생성
- 일관된 브랜드 보이스 유지

</td>
</tr>
</table>

<table>
<tr>
<td width="33%">

### 🛠️ Function Calling
- 문서 검색, 채팅 히스토리 검색
- 통계 조회, 카테고리 관리
- 채팅 내보내기 등 다양한 도구

</td>
<td width="33%">

### 🏷️ 스마트 분류
- 키워드 기반 자동 카테고리 분류
- 대화 내용 분석 및 태깅
- 검색 최적화를 위한 인덱싱

</td>
<td width="33%">

### 📊 데이터 관리
- SQLite 기반 로컬 데이터 저장
- 채팅 히스토리 및 문서 관리
- 통계 및 분석 대시보드

</td>
</tr>
</table>

## 🌟 LocalMind의 특별한 점

<div align="center">

| 🧠 **지능형 분석** | 🇰🇷 **한국어 특화** | ⚡ **빠른 검색** |
|:---:|:---:|:---:|
| EXAONE 모델 기반<br/>고도화된 문서 이해 | 한국어에 최적화된<br/>자연어 처리 | FAISS 기반<br/>실시간 벡터 검색 |

| 🎯 **정확한 답변** | 💻 **완전 로컬** | 🔒 **프라이버시** |
|:---:|:---:|:---:|
| 문서 내용에만 기반한<br/>신뢰할 수 있는 응답 | 인터넷 없이<br/>독립 실행 | 모든 데이터가<br/>로컬에서만 처리 |

| 💬 **GUI 인터페이스** | 🛠️ **Function Calling** | 📊 **데이터 관리** |
|:---:|:---:|:---:|
| Claude Desktop 스타일<br/>직관적 사용자 경험 | 다양한 도구와<br/>자동화 기능 | SQLite 기반<br/>체계적 데이터 저장 |

</div>

## 🚀 설치 및 실행

### 📋 시스템 요구사항

<div align="center">

| 구성 요소 | 최소 사양 | 권장 사양 |
|:---:|:---:|:---:|
| **GPU** | NVIDIA RTX 3060 Ti (8GB) | RTX 4070 이상 |
| **RAM** | 16GB | 32GB |
| **Python** | 3.8+ | 3.10+ |
| **OS** | Windows 11, Ubuntu 22.04 | - |

</div>

### ⚙️ 설치 과정

```bash
# 1️⃣ 가상환경 생성
python -m venv venv

# 2️⃣ 가상환경 활성화
# Windows
.\venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 3️⃣ 패키지 설치
pip install -r requirements.txt

# 4️⃣ 환경 검증
python setup_guide.py
```

### 🎮 사용법

#### 🖥️ GUI 모드 (권장)
```bash
# 🚀 GUI 애플리케이션 실행
python run_gui.py

# 브라우저에서 http://localhost:8501 접속
```

#### 💻 CLI 모드
```bash
# 📁 문서를 data/ 폴더에 추가 후

# 🔧 데이터베이스 생성
python create_db.py

# 🚀 LocalMind 실행
python main.py

# 📊 성능 평가 (선택사항)
python evaluation.py
```

## 📁 프로젝트 구조

```
LocalMind/
├── 🖼️  Gemini_Generated_Image_t7sbxkt7sbxkt7sb.png  # 프로젝트 로고
├── 📁  data/                                        # 원본 문서 폴더
├── �️   gui_app.py                                  # GUI 애플리케이션
├── 🚀  run_gui.py                                  # GUI 실행 스크립트
├── �️   database.py                                 # 데이터베이스 관리
├── 🔍  keyword_analyzer.py                         # 키워드 분석
├── 🛠️  function_tools.py                           # Function Calling 도구
├── �  rcreate_db.py                                # 벡터 DB 생성
├── 🧠  main.py                                     # CLI 메인 스크립트
├── �️  evaluation.py                               # 성능 평가
├── 🧪  test_model.py                               # 모델 테스트
├── ⚙️  setup_guide.py                              # 환경 검증
├── 📦  requirements.txt                            # 패키지 목록
├── 📚  TECH_STACK.md                              # 기술 문서
├── 🗃️  document_memory.faiss                       # FAISS 인덱스 (자동생성)
├── 💾  document_memory.pkl                         # 텍스트 데이터 (자동생성)
├── 🗄️  localmind.db                                # SQLite 데이터베이스 (자동생성)
└── 📤  exports/                                    # 채팅 내보내기 폴더 (자동생성)
```

## 🎨 사용 모델

<div align="center">

### 🤖 AI 모델 스택

| 역할 | 모델 | 특징 |
|:---:|:---:|:---:|
| **🧠 언어 모델** | [EXAONE-4.0-1.2B](https://huggingface.co/LGAI-EXAONE/EXAONE-4.0-1.2B) | LG AI Research 개발<br/>한국어 특화 모델 |
| **🔍 임베딩** | [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) | 다국어 지원<br/>고성능 벡터 임베딩 |

</div>

## 📸 스크린샷

<div align="center">

### 💬 질의응답 예시
![질의응답 예시](https://via.placeholder.com/600x300/4CAF50/white?text=LocalMind+Q%26A+Example)

### 🎨 문체 모방 예시
![문체 모방 예시](https://via.placeholder.com/600x300/2196F3/white?text=LocalMind+Style+Mimicking)

</div>

## 🛠️ 문제 해결

<details>
<summary>🔧 자주 발생하는 문제들</summary>

### ❌ GPU 메모리 부족
```bash
# 다른 GPU 사용 프로그램 종료 후 재시도
python setup_guide.py  # GPU 상태 확인
```

### ❌ 모델 다운로드 실패
```bash
# 인터넷 연결 확인 후
python test_model.py  # 모델 연결 테스트
```

### ❌ 문서 인식 실패
```bash
# data 폴더에 PDF, TXT, MD 파일 확인
ls data/  # 파일 목록 확인
```

</details>

## 🤝 기여하기

LocalMind 프로젝트에 기여하고 싶으시다면:

1. 🍴 Fork the repository
2. 🌿 Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. 💾 Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. 📤 Push to the branch (`git push origin feature/AmazingFeature`)
5. 🔄 Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

<div align="center">

### 🧠 LocalMind - 당신의 개인 AI 문서 어시스턴트

*로컬에서 실행되는 지능형 문서 분석 시스템*

**Made with ❤️ by LocalMind Team**

[![GitHub stars](https://img.shields.io/github/stars/yourusername/LocalMind?style=social)](https://github.com/JIWOOK23/LocalMind)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/LocalMind?style=social)](https://github.com/JIWOOK23/LocalMind)

</div>