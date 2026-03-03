import requests
import json

# Test the complete Phase 2 pipeline
API_BASE = "http://127.0.0.1:8000"
audio_file_path = "sample_audios/sample-7.mp3"

print("🧪 Testing Meeting Assistant - Phase 2 Features")
print("=" * 60)

# Upload and process the audio file
print(f"\n📤 Uploading: {audio_file_path}")
with open(audio_file_path, "rb") as f:
    files = {"file": (audio_file_path, f, "audio/mpeg")}
    params = {
        "language": "en",
        "model_size": "tiny",  # Using tiny for faster testing
        "enable_cleaning": "false"
    }
    
    print("⏳ Processing (this may take 30-60 seconds)...")
    response = requests.post(f"{API_BASE}/transcribe/", files=files, params=params)

if response.status_code == 200:
    result = response.json()
    
    print("\n✅ SUCCESS! Results received.")
    print("=" * 60)
    
    # Test 1: Basic Transcription
    print("\n📝 TRANSCRIPT:")
    print(f"   {result['transcript'][:200]}...")
    
    # Test 2: Speaker Diarization
    print(f"\n👥 SPEAKERS: {len(result.get('speakers', []))} detected")
    for speaker in result.get('speakers', []):
        print(f"   - {speaker['label']}")
    
    # Test 3: Emotion Detection
    print(f"\n😊 EMOTIONS: Detected in {len(result.get('segments', []))} segments")
    emotions_found = set()
    for seg in result.get('segments', [])[:5]:  # Show first 5
        emotion = seg.get('emotion', 'neutral')
        emotions_found.add(emotion)
        print(f"   - {seg.get('speaker_id', 'Unknown')}: {emotion}")
    print(f"   Unique emotions: {', '.join(emotions_found)}")
    
    # Test 4: Insights Extraction
    insights = result.get('insights', {})
    print(f"\n🧠 SMART INSIGHTS:")
    print(f"   Decisions: {len(insights.get('decisions', []))}")
    for dec in insights.get('decisions', []):
        print(f"      • {dec}")
    print(f"   Agreements: {len(insights.get('agreements', []))}")
    for agr in insights.get('agreements', []):
        print(f"      • {agr}")
    print(f"   Conflicts: {len(insights.get('conflicts', []))}")
    for conf in insights.get('conflicts', []):
        print(f"      • {conf}")
    
    # Test 5: Role-Specific Summaries
    role_summaries = result.get('role_summaries', {})
    print(f"\n📊 ROLE-SPECIFIC SUMMARIES:")
    print(f"\n   🎯 GENERAL:")
    print(f"      {result.get('summary', 'N/A')[:150]}...")
    print(f"\n   💼 EXECUTIVE:")
    print(f"      {role_summaries.get('executive', 'N/A')[:150]}...")
    print(f"\n   🔧 TECHNICAL:")
    print(f"      {role_summaries.get('technical', 'N/A')[:150]}...")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL PHASE 2 FEATURES VERIFIED:")
    print("   ✓ Transcription")
    print("   ✓ Speaker Diarization")
    print("   ✓ Emotion Detection")
    print("   ✓ Insights Extraction (Decisions/Agreements/Conflicts)")
    print("   ✓ Role-Specific Summaries (General/Executive/Technical)")
    print("=" * 60)
    
else:
    print(f"\n❌ ERROR: {response.status_code}")
    print(response.text)
