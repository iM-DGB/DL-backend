def build_prompt(chunks: list[str], question: str) -> str:
    return f"""당신은 보험 약관과 상품 설명서에 정통한 AI 상담사입니다.

[참고 문서 발췌]
{'\n\n'.join(chunks)}

[사용자 질문]
{question}

[답변]
"""
