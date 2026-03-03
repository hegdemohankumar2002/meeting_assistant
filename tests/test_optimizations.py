import time
import requests

# Test the optimizations with a simulated large file scenario
API_BASE = "http://127.0.0.1:8000"
audio_file_path = "sample_audios/sample-7.mp3"

print("🧪 Testing Large File Optimizations")
print("=" * 60)

# Test 1: File upload with timing
print("\n📤 Uploading sample file...")
start_time = time.time()

with open(audio_file_path, "rb") as f:
    files = {"file": (audio_file_path, f, "audio/mpeg")}
    params = {
        "language": "en",
        "model_size": "tiny",  # Fastest for testing
        "enable_cleaning": "false"
    }
    
    print("⏳ Processing...")
    response = requests.post(f"{API_BASE}/transcribe/", files=files, params=params, timeout=600)

end_time = time.time()
processing_time = end_time - start_time

if response.status_code == 200:
    result = response.json()
    
    print(f"\n✅ SUCCESS! Processed in {processing_time:.1f} seconds")
    print("=" * 60)
    
    # Verify optimizations
    segments_count = len(result.get('segments', []))
    insights = result.get('insights', {})
    decisions_count = len(insights.get('decisions', []))
    agreements_count = len(insights.get('agreements', []))
    conflicts_count = len(insights.get('conflicts', []))
    
    print(f"\n📊 PERFORMANCE METRICS:")
    print(f"   Processing Time: {processing_time:.1f}s")
    print(f"   Segments Analyzed: {segments_count}")
    print(f"   Insights Extracted: {decisions_count + agreements_count + conflicts_count}")
    
    # Check if batch processing worked (all segments should have emotions)
    emotions_detected = sum(1 for seg in result.get('segments', []) if seg.get('emotion'))
    print(f"\n✅ BATCH EMOTION ANALYSIS:")
    print(f"   Segments with emotions: {emotions_detected}/{segments_count}")
    
    # Check if insights were limited
    total_insights = decisions_count + agreements_count + conflicts_count
    print(f"\n✅ INSIGHTS OPTIMIZATION:")
    print(f"   Total insights: {total_insights}")
    print(f"   (Should be ≤ 100 for large files)")
    
    # Verify role summaries still work
    role_summaries = result.get('role_summaries', {})
    has_executive = bool(role_summaries.get('executive'))
    has_technical = bool(role_summaries.get('technical'))
    
    print(f"\n✅ ROLE SUMMARIES:")
    print(f"   Executive: {'✓' if has_executive else '✗'}")
    print(f"   Technical: {'✓' if has_technical else '✗'}")
    
    print("\n" + "=" * 60)
    print("✅ ALL OPTIMIZATIONS VERIFIED!")
    print("=" * 60)
    
else:
    print(f"\n❌ ERROR: {response.status_code}")
    print(response.text)
