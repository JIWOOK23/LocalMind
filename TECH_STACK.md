# LocalMind - 기술 스택 및 요구사항

## 하드웨어 요구사항
- **GPU**: NVIDIA GeForce RTX 3060 Ti (8GB VRAM)
- **RAM**: 16GB 이상 권장
- **CPU**: 4코어 이상 권장

## 소프트웨어 환경
- **OS**: Windows 11 (WSL2) 또는 Ubuntu 22.04
- **Python**: 3.8 이상
- **LLM 서빙**: HuggingFace Transformers

## AI 모델
| 구분 | 모델명 | 용도 |
|------|--------|------|
| 생성 LLM | EXAONE-4.0-1.2B | 내용 생성 및 스타일 모방 과업 수행 |
| 임베딩 모델 | BAAI/bge-m3 | 다국어 텍스트의 의미론적 벡터 표현 추출 |

## 핵심 라이브러리
| 라이브러리 | 용도 |
|------------|------|
| faiss-cpu | 벡터 유사도 검색 및 인덱싱 |
| llama-index | RAG 파이프라인의 통합 구성 및 제어 |
| llama-index-llms-huggingface | LlamaIndex와 HuggingFace 모델 연동 |
| llama-index-embeddings-huggingface | LlamaIndex와 HuggingFace 임베딩 모델 연동 |
| kss | 한국어 텍스트의 구조적 분할 (문장 단위) |
| evaluate, nltk | ROUGE, BLEU 성능 지표 측정 |
| faststylometry | 문체 분석 지표 측정 |

## 모델 변경 이유
- **기존**: deepseek-r1:7b
- **변경**: EXAONE-4.0-1.2B
- **변경 사유**: 
  - LG AI Research에서 개발한 한국어 특화 모델
  - 더 작은 모델 크기로 효율적인 추론
  - 한국어 이해 및 생성 성능 최적화
  - HuggingFace에서 직접 사용 가능