# Test imports for 방안 1+2 implementation
try:
    from extraction_verifier import (
        verify_llm_extraction,
        two_stage_extraction,
        extract_key_sentences_verified,
        _calculate_similarity
    )
    print("extraction_verifier: OK")
except Exception as e:
    print(f"extraction_verifier: FAILED - {e}")

try:
    from llm_utils import _llm_try_extract_or_reuse
    print("llm_utils: OK")
except Exception as e:
    print(f"llm_utils: FAILED - {e}")

try:
    from feedback_analyzer import (
        analyze_answer,
        extract_verified_key_context,
        verify_attack_point_in_essay
    )
    print("feedback_analyzer: OK")
except Exception as e:
    print(f"feedback_analyzer: FAILED - {e}")

print("\nAll imports completed!")
