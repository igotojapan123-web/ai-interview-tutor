# -*- coding: utf-8 -*-
"""
phase_final_check.py
Comprehensive test script for Phase 1, Phase 2, and Enhanced Voice Analysis features.

This script tests:
1. Phase 1 Features: D-ID API, Video Utils, Voice Utils, Emotion Analysis, TTS
2. Phase 2 Features: Webcam Analyzer, MediaPipe models, Webcam Component
3. Enhanced Voice Analysis: Advanced analysis functions and sub-functions
4. UI/Page Checks: Syntax, imports, session state in 모의면접.py

Run: python phase_final_check.py
"""

import os
import sys
import ast
import importlib.util
from typing import Tuple, List, Dict, Any

# Ensure proper encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Test results storage
results: List[Dict[str, Any]] = []


def record_result(category: str, test_name: str, passed: bool, message: str = ""):
    """Record a test result."""
    status = "PASS" if passed else "FAIL"
    results.append({
        "category": category,
        "test": test_name,
        "passed": passed,
        "status": status,
        "message": message
    })
    print(f"  [{status}] {test_name}")
    if message and not passed:
        print(f"         -> {message}")


def test_module_import(module_name: str, category: str) -> Any:
    """Attempt to import a module and record result."""
    try:
        module = importlib.import_module(module_name)
        record_result(category, f"Import {module_name}", True)
        return module
    except ImportError as e:
        record_result(category, f"Import {module_name}", False, str(e))
        return None
    except Exception as e:
        record_result(category, f"Import {module_name}", False, f"Unexpected error: {e}")
        return None


def test_function_exists(module: Any, func_name: str, category: str, test_label: str = None) -> bool:
    """Check if a function exists in a module."""
    label = test_label or f"Function {func_name} exists"
    if module is None:
        record_result(category, label, False, "Module not imported")
        return False

    if hasattr(module, func_name) and callable(getattr(module, func_name)):
        record_result(category, label, True)
        return True
    else:
        record_result(category, label, False, f"Function '{func_name}' not found")
        return False


def test_file_exists(filepath: str, category: str, test_label: str = None) -> bool:
    """Check if a file exists."""
    label = test_label or f"File exists: {os.path.basename(filepath)}"
    exists = os.path.isfile(filepath)
    record_result(category, label, exists, "" if exists else f"File not found: {filepath}")
    return exists


# =============================================================================
# Phase 1 Tests
# =============================================================================
def test_phase1():
    """Test Phase 1 features."""
    print("\n" + "=" * 60)
    print("PHASE 1 TESTS: D-ID, Video/Voice Utils, Emotion, TTS")
    print("=" * 60)

    # Test video_utils module
    print("\n[video_utils]")
    video_utils = test_module_import("video_utils", "Phase 1")

    if video_utils:
        # D-ID API availability check function
        test_function_exists(video_utils, "check_did_api_available", "Phase 1",
                           "D-ID API check function")

        # Test actual D-ID API availability (may fail without API key)
        try:
            is_available = video_utils.check_did_api_available()
            record_result("Phase 1", "D-ID API availability check callable", True,
                         f"API available: {is_available}")
        except Exception as e:
            record_result("Phase 1", "D-ID API availability check callable", False, str(e))

        # Video utility functions
        test_function_exists(video_utils, "create_interviewer_video", "Phase 1")
        test_function_exists(video_utils, "get_video_html", "Phase 1")
        test_function_exists(video_utils, "get_fallback_avatar_html", "Phase 1")
        test_function_exists(video_utils, "get_enhanced_fallback_avatar_html", "Phase 1",
                           "Enhanced fallback avatar HTML function")

    # Test voice_utils module
    print("\n[voice_utils]")
    voice_utils = test_module_import("voice_utils", "Phase 1")

    if voice_utils:
        # Core voice functions
        test_function_exists(voice_utils, "transcribe_audio", "Phase 1")
        test_function_exists(voice_utils, "analyze_voice_quality", "Phase 1")
        test_function_exists(voice_utils, "analyze_voice_complete", "Phase 1")

        # Emotion analysis
        test_function_exists(voice_utils, "analyze_interview_emotion", "Phase 1",
                           "Emotion analysis function")

        # TTS generation
        test_function_exists(voice_utils, "generate_tts_audio", "Phase 1",
                           "TTS generation function")


# =============================================================================
# Phase 2 Tests
# =============================================================================
def test_phase2():
    """Test Phase 2 features."""
    print("\n" + "=" * 60)
    print("PHASE 2 TESTS: Webcam Analyzer, MediaPipe, Webcam Component")
    print("=" * 60)

    # Check webcam_analyzer.py exists
    print("\n[webcam_analyzer]")
    webcam_analyzer_path = os.path.join(PROJECT_ROOT, "webcam_analyzer.py")
    test_file_exists(webcam_analyzer_path, "Phase 2", "webcam_analyzer.py exists")

    # Try to import webcam_analyzer
    webcam_analyzer = test_module_import("webcam_analyzer", "Phase 2")

    if webcam_analyzer:
        test_function_exists(webcam_analyzer, "get_webcam_analyzer", "Phase 2")
        test_function_exists(webcam_analyzer, "is_webcam_analysis_available", "Phase 2")

        # Check class exists
        if hasattr(webcam_analyzer, "WebcamAnalyzer"):
            record_result("Phase 2", "WebcamAnalyzer class exists", True)
        else:
            record_result("Phase 2", "WebcamAnalyzer class exists", False)

        # Check MEDIAPIPE_AVAILABLE flag
        if hasattr(webcam_analyzer, "MEDIAPIPE_AVAILABLE"):
            mp_avail = webcam_analyzer.MEDIAPIPE_AVAILABLE
            record_result("Phase 2", "MediaPipe availability flag", True,
                         f"MEDIAPIPE_AVAILABLE = {mp_avail}")
        else:
            record_result("Phase 2", "MediaPipe availability flag", False)

    # Check MediaPipe model files
    print("\n[MediaPipe Models]")
    models_dir = os.path.join(PROJECT_ROOT, "models")
    model_files = [
        ("face_landmarker.task", "Face Landmarker model"),
        ("pose_landmarker_heavy.task", "Pose Landmarker model"),
        ("hand_landmarker.task", "Hand Landmarker model"),
    ]

    for model_file, label in model_files:
        model_path = os.path.join(models_dir, model_file)
        test_file_exists(model_path, "Phase 2", label)

    # Check webcam_component.py exists
    print("\n[webcam_component]")
    webcam_component_path = os.path.join(PROJECT_ROOT, "webcam_component.py")
    test_file_exists(webcam_component_path, "Phase 2", "webcam_component.py exists")

    # Try to import webcam_component
    webcam_component = test_module_import("webcam_component", "Phase 2")

    if webcam_component:
        test_function_exists(webcam_component, "create_webcam_streamer", "Phase 2")
        test_function_exists(webcam_component, "is_webcam_available", "Phase 2")
        test_function_exists(webcam_component, "get_realtime_feedback_html", "Phase 2")
        test_function_exists(webcam_component, "get_score_gauge_html", "Phase 2")


# =============================================================================
# Enhanced Voice Analysis Tests
# =============================================================================
def test_enhanced_voice_analysis():
    """Test enhanced voice analysis features."""
    print("\n" + "=" * 60)
    print("ENHANCED VOICE ANALYSIS TESTS")
    print("=" * 60)

    print("\n[analyze_voice_advanced]")
    voice_utils = None
    try:
        voice_utils = importlib.import_module("voice_utils")
    except ImportError as e:
        record_result("Voice Advanced", "Import voice_utils", False, str(e))
        return

    # Main advanced analysis function
    test_function_exists(voice_utils, "analyze_voice_advanced", "Voice Advanced",
                        "analyze_voice_advanced function")

    # Sub-functions for detailed analysis
    print("\n[Sub-functions]")
    sub_functions = [
        "_analyze_speech_rate",
        "_analyze_filler_words",
        "_analyze_pauses",
        "_analyze_energy_pattern",
        "_analyze_pronunciation",
        "_analyze_answer_structure",
    ]

    for func_name in sub_functions:
        test_function_exists(voice_utils, func_name, "Voice Advanced",
                           f"{func_name} sub-function")

    # Test if analyze_voice_advanced is callable (basic structure test)
    if hasattr(voice_utils, "analyze_voice_advanced"):
        try:
            # Create minimal test data (won't actually analyze, just check function signature)
            func = getattr(voice_utils, "analyze_voice_advanced")
            import inspect
            sig = inspect.signature(func)
            param_count = len(sig.parameters)
            record_result("Voice Advanced", "Function signature valid", True,
                         f"Parameters: {list(sig.parameters.keys())}")
        except Exception as e:
            record_result("Voice Advanced", "Function signature valid", False, str(e))


# =============================================================================
# UI/Page Tests
# =============================================================================
def test_ui_pages():
    """Test UI page files."""
    print("\n" + "=" * 60)
    print("UI/PAGE TESTS: Syntax and Integration Checks")
    print("=" * 60)

    mock_interview_path = os.path.join(PROJECT_ROOT, "pages", "4_모의면접.py")

    print("\n[4_모의면접.py]")

    # Check file exists
    if not test_file_exists(mock_interview_path, "UI/Pages", "4_모의면접.py exists"):
        return

    # Syntax check using AST
    try:
        with open(mock_interview_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        ast.parse(source_code)
        record_result("UI/Pages", "Syntax check (AST parse)", True)
    except SyntaxError as e:
        record_result("UI/Pages", "Syntax check (AST parse)", False,
                     f"Line {e.lineno}: {e.msg}")
    except Exception as e:
        record_result("UI/Pages", "Syntax check (AST parse)", False, str(e))

    # Check for analyze_voice_advanced import
    if "analyze_voice_advanced" in source_code:
        # More specific check - is it in an import statement?
        if "from voice_utils import" in source_code and "analyze_voice_advanced" in source_code:
            record_result("UI/Pages", "analyze_voice_advanced import", True)
        else:
            record_result("UI/Pages", "analyze_voice_advanced import", False,
                         "Found in code but not in proper import statement")
    else:
        record_result("UI/Pages", "analyze_voice_advanced import", False,
                     "analyze_voice_advanced not found in file")

    # Check for mock_advanced_analyses session state
    if "mock_advanced_analyses" in source_code:
        # Check if it's properly initialized
        if '"mock_advanced_analyses"' in source_code or "'mock_advanced_analyses'" in source_code:
            record_result("UI/Pages", "mock_advanced_analyses session state defined", True)
        else:
            record_result("UI/Pages", "mock_advanced_analyses session state defined", False,
                         "Found reference but not as string key")
    else:
        record_result("UI/Pages", "mock_advanced_analyses session state defined", False,
                     "mock_advanced_analyses not found in file")

    # Check for analyze_interview_emotion import (Phase 1)
    if "analyze_interview_emotion" in source_code:
        record_result("UI/Pages", "analyze_interview_emotion import", True)
    else:
        record_result("UI/Pages", "analyze_interview_emotion import", False)


# =============================================================================
# Summary
# =============================================================================
def print_summary():
    """Print test summary."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    # Count by category
    categories = {}
    total_passed = 0
    total_failed = 0

    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"passed": 0, "failed": 0}

        if r["passed"]:
            categories[cat]["passed"] += 1
            total_passed += 1
        else:
            categories[cat]["failed"] += 1
            total_failed += 1

    # Print by category
    for cat, counts in categories.items():
        total = counts["passed"] + counts["failed"]
        pct = (counts["passed"] / total * 100) if total > 0 else 0
        status = "OK" if counts["failed"] == 0 else "ISSUES"
        print(f"\n{cat}:")
        print(f"  Passed: {counts['passed']}/{total} ({pct:.0f}%) [{status}]")

        # List failures
        if counts["failed"] > 0:
            print("  Failed tests:")
            for r in results:
                if r["category"] == cat and not r["passed"]:
                    print(f"    - {r['test']}")
                    if r["message"]:
                        print(f"      ({r['message']})")

    # Overall
    total = total_passed + total_failed
    overall_pct = (total_passed / total * 100) if total > 0 else 0

    print("\n" + "-" * 60)
    print(f"OVERALL: {total_passed}/{total} tests passed ({overall_pct:.0f}%)")

    if total_failed == 0:
        print("\n[SUCCESS] All tests passed!")
    else:
        print(f"\n[WARNING] {total_failed} test(s) failed. Review the issues above.")

    print("=" * 60)

    return total_failed == 0


# =============================================================================
# Main
# =============================================================================
def main():
    """Run all tests."""
    print("=" * 60)
    print("PHASE FINAL CHECK - Comprehensive Test Script")
    print(f"Project Root: {PROJECT_ROOT}")
    print("=" * 60)

    # Run all test categories
    test_phase1()
    test_phase2()
    test_enhanced_voice_analysis()
    test_ui_pages()

    # Print summary and return exit code
    success = print_summary()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
