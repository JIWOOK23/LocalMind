# test_model.py
"""
LocalMind - EXAONE 모델 테스트 스크립트
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def test_localmind_model():
    try:
        print("🔍 LocalMind - EXAONE 모델을 테스트합니다...")
        
        # GPU 사용 가능 여부 확인
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"   사용 디바이스: {device}")
        
        # 모델과 토크나이저 로드
        model_name = "LGAI-EXAONE/EXAONE-4.0-1.2B"
        
        print("   토크나이저를 로드합니다...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        print("   모델을 로드합니다...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True
        )
        
        # 채팅 템플릿 사용
        messages = [
            {"role": "user", "content": "안녕하세요. 간단히 인사해주세요."}
        ]
        
        # 채팅 템플릿 적용
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        print(f"   사용된 프롬프트: {prompt}")
        
        # 토크나이징
        inputs = tokenizer(prompt, return_tensors="pt")
        if device == "cuda":
            inputs = inputs.to(device)
        
        # 생성
        print("📝 응답을 생성합니다...")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # 디코딩
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 프롬프트 부분 제거
        if prompt in response:
            response = response.replace(prompt, "").strip()
        
        print(f"✅ 응답: {response}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_localmind_model()