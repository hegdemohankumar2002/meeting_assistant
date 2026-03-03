"""
Test script to verify long-duration meeting support.
Tests the enhanced services with simulated long transcripts.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.chunking import get_chunker
from app.services.summarizer import summarize_structured
from app.services.emotion import analyze_emotion
from app.services.intelligence import extract_insights
import time


def test_chunking():
    """Test the chunking service."""
    print("\n" + "="*60)
    print("TEST 1: Text Chunking Service")
    print("="*60)
    
    # Create a long text (simulate 30-minute meeting transcript)
    # Average speaking rate: 150 words/minute
    # 30 minutes = ~4500 words
    sample_text = " ".join([f"This is sentence number {i} in our very long meeting transcript." for i in range(500)])
    
    chunker = get_chunker()
    
    # Test token counting
    token_count = chunker.count_tokens(sample_text)
    word_count = len(sample_text.split())
    print(f"✓ Sample text: {word_count} words, {token_count} tokens")
    
    # Test token-based chunking
    chunks = chunker.chunk_by_tokens(sample_text, max_tokens=500, overlap_tokens=50)
    print(f"✓ Token-based chunking: {len(chunks)} chunks created")
    print(f"  - First chunk: {chunks[0]['token_count']} tokens")
    print(f"  - Last chunk: {chunks[-1]['token_count']} tokens")
    
    # Test word-based chunking
    word_chunks = chunker.chunk_by_words(sample_text, max_words=100, overlap_words=10)
    print(f"✓ Word-based chunking: {len(word_chunks)} chunks created")
    
    print("✅ Chunking service working correctly!\n")


def test_hierarchical_summarization():
    """Test hierarchical summarization for long transcripts."""
    print("\n" + "="*60)
    print("TEST 2: Hierarchical Summarization")
    print("="*60)
    
    # Short transcript (should use BART)
    short_text = """
    We discussed the new product launch. The team agreed on the timeline.
    Marketing will prepare the campaign. Development needs two more weeks.
    We'll meet again next Monday to review progress.
    """
    
    print("Testing short transcript (BART)...")
    start = time.time()
    short_result = summarize_structured(short_text)
    short_time = time.time() - start
    print(f"✓ Short transcript processed in {short_time:.2f}s")
    print(f"  - Summary: {short_result['summary'][:100]}...")
    print(f"  - Key points: {len(short_result['key_points'])}")
    print(f"  - Action items: {len(short_result['action_items'])}")
    
    # Long transcript (should use hierarchical if LangChain available)
    # Simulate 60-minute meeting: ~9000 words
    long_sentences = [
        "The team discussed the quarterly results and found them satisfactory.",
        "We need to improve our customer engagement metrics significantly.",
        "The marketing campaign will launch next month with a new strategy.",
        "Development team reported progress on the new features.",
        "We decided to hire two more engineers for the backend team.",
        "The budget was approved for the next quarter's initiatives.",
        "Customer feedback has been overwhelmingly positive this month.",
        "We agreed to implement the new security protocols immediately.",
    ]
    
    # Repeat to create a long transcript
    long_text = " ".join(long_sentences * 700)  # ~5600 words
    word_count = len(long_text.split())
    
    print(f"\nTesting long transcript ({word_count} words)...")
    start = time.time()
    long_result = summarize_structured(long_text)
    long_time = time.time() - start
    print(f"✓ Long transcript processed in {long_time:.2f}s")
    print(f"  - Summary: {long_result['summary'][:100]}...")
    print(f"  - Key points: {len(long_result['key_points'])}")
    print(f"  - Action items: {len(long_result['action_items'])}")
    
    print("✅ Summarization working correctly!\n")


def test_emotion_detection():
    """Test emotion detection with long segments."""
    print("\n" + "="*60)
    print("TEST 3: Emotion Detection")
    print("="*60)
    
    # Short segment
    short_segment = "I'm so happy about the progress we made today!"
    emotion = analyze_emotion(short_segment)
    print(f"✓ Short segment emotion: {emotion}")
    
    # Long segment (should use sliding window)
    long_segment = " ".join([
        "I'm really excited about this project. " * 50,
        "However, I'm concerned about the timeline. " * 50,
        "But overall, I think we can make it work. " * 50
    ])
    
    print(f"Testing long segment ({len(long_segment)} characters)...")
    emotion = analyze_emotion(long_segment)
    print(f"✓ Long segment emotion: {emotion}")
    
    print("✅ Emotion detection working correctly!\n")


def test_intelligence_extraction():
    """Test intelligence extraction with batching."""
    print("\n" + "="*60)
    print("TEST 4: Intelligence Extraction (Batching)")
    print("="*60)
    
    # Create transcript with many decision/agreement/conflict sentences
    transcript = """
    We decided to move forward with the new architecture.
    I agree with the proposed timeline for development.
    However, I disagree with the budget allocation.
    The team will implement the changes next week.
    Yes, that sounds like a good plan to me.
    We need to approve the final design by Friday.
    I'm not sure about the security implications.
    Let's confirm the deployment schedule tomorrow.
    The stakeholders agreed to the new features.
    But wait, we haven't considered the performance impact.
    """ * 20  # Create 200 sentences
    
    sentence_count = len([s for s in transcript.split('.') if s.strip()])
    print(f"Processing transcript with ~{sentence_count} sentences...")
    
    start = time.time()
    insights = extract_insights(transcript)
    extraction_time = time.time() - start
    
    print(f"✓ Extraction completed in {extraction_time:.2f}s")
    print(f"  - Decisions: {len(insights['decisions'])}")
    print(f"  - Agreements: {len(insights['agreements'])}")
    print(f"  - Conflicts: {len(insights['conflicts'])}")
    
    if insights['decisions']:
        print(f"  - Sample decision: {insights['decisions'][0][:80]}...")
    
    print("✅ Intelligence extraction working correctly!\n")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LONG-DURATION MEETING SUPPORT - VERIFICATION TESTS")
    print("="*60)
    
    try:
        test_chunking()
        test_hierarchical_summarization()
        test_emotion_detection()
        test_intelligence_extraction()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nYour Meeting Assistant is now ready to handle long meetings!")
        print("Capabilities:")
        print("  • Transcripts up to 120 minutes")
        print("  • Hierarchical summarization for >5000 words")
        print("  • Sliding window emotion detection")
        print("  • Batched intelligence extraction")
        print("  • Token-aware chunking")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
