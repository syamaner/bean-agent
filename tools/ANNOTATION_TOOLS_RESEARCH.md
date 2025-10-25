# Audio Annotation Tools Research

Research on open-source tools for annotating audio files with time-based labels for first crack detection.

## Requirements

Our ideal tool should:
- ✅ Visualize audio waveform
- ✅ Play audio segments
- ✅ Select time ranges with precision
- ✅ Add labels to time ranges
- ✅ Export annotations in JSON or similar format
- ✅ Work on macOS
- ✅ Handle long audio files (10+ minutes)
- ✅ Support multiple audio files

---

## Option 1: Audacity (with Label Track)

**Description**: Popular open-source audio editor with label track support

**Pros:**
- ✅ Free and widely used
- ✅ Excellent waveform visualization
- ✅ Precise time selection
- ✅ Label track feature for annotations
- ✅ Native macOS support
- ✅ Spectral analysis available
- ✅ Export labels to text file

**Cons:**
- ❌ Labels export as `.txt`, not JSON (need conversion script)
- ❌ Not designed specifically for annotation workflow
- ❌ Manual process for each file

**Label Export Format:**
```
0.000000	30.000000	no_first_crack
420.500000	450.500000	first_crack
```

**Installation:**
```bash
brew install --cask audacity
```

**Workflow:**
1. Open audio file
2. Select region → Cmd+B to add label
3. Type label name
4. Repeat for all regions
5. Export → Export Labels
6. Convert .txt to JSON with script

**Recommendation:** ⭐⭐⭐⭐ Good for initial work, needs conversion script

---

## Option 2: Label Studio

**Description**: ML data labeling platform with audio support

**Pros:**
- ✅ Web-based UI
- ✅ Purpose-built for ML annotation
- ✅ JSON export
- ✅ Multiple file support
- ✅ Waveform visualization
- ✅ Time-based region selection
- ✅ Project management features

**Cons:**
- ❌ Requires server setup
- ❌ More complex than needed
- ❌ Heavy for just 4 files

**Installation:**
```bash
pip install label-studio
label-studio start
```

**Configuration:**
```xml
<View>
  <Audio name="audio" value="$audio"/>
  <Labels name="label" toName="audio">
    <Label value="no_first_crack" background="blue"/>
    <Label value="first_crack" background="red"/>
  </Labels>
</View>
```

**Export Format:** JSON with regions and labels

**Recommendation:** ⭐⭐⭐⭐⭐ Best for scalable annotation workflow

---

## Option 3: Sonic Visualiser

**Description**: Audio analysis and annotation tool

**Pros:**
- ✅ Powerful visualization
- ✅ Spectral analysis
- ✅ Time instants and regions
- ✅ Layer-based annotations
- ✅ Native macOS support
- ✅ Export annotations

**Cons:**
- ❌ Steeper learning curve
- ❌ Export format is RDF/XML (need conversion)
- ❌ More focused on analysis than annotation

**Installation:**
```bash
brew install --cask sonic-visualiser
```

**Recommendation:** ⭐⭐⭐ Overkill for our needs

---

## Option 4: Praat

**Description**: Phonetics analysis tool with annotation

**Pros:**
- ✅ Precise time-based annotation
- ✅ TextGrid format
- ✅ Strong academic use

**Cons:**
- ❌ Designed for speech analysis
- ❌ Complex interface
- ❌ TextGrid format needs conversion

**Recommendation:** ⭐⭐ Not ideal for our use case

---

## Option 5: ELAN

**Description**: Multimedia annotation tool

**Pros:**
- ✅ Time-aligned annotations
- ✅ Multiple tiers
- ✅ Good for long files

**Cons:**
- ❌ Complex for simple task
- ❌ XML export (needs conversion)

**Recommendation:** ⭐⭐ Too complex

---

## Option 6: audio-annotator (Web-based)

**Description**: Simple web-based audio annotation tool

**GitHub:** https://github.com/CrowdCurio/audio-annotator

**Pros:**
- ✅ Simple web interface
- ✅ Time-based regions
- ✅ JSON export
- ✅ Lightweight

**Cons:**
- ❌ Requires local server setup
- ❌ Limited maintenance
- ❌ Basic features only

**Recommendation:** ⭐⭐⭐ Good but unmaintained

---

## Option 7: wavesurfer.js (Custom Tool)

**Description:** Build our own tool using wavesurfer.js library

**Pros:**
- ✅ Full control over workflow
- ✅ Perfect JSON export format
- ✅ Can integrate with our pipeline
- ✅ Waveform visualization
- ✅ Modern web interface

**Cons:**
- ❌ Need to build it
- ❌ Time investment upfront

**Tech Stack:**
- Frontend: React + wavesurfer.js
- Backend: FastAPI
- Storage: JSON files directly

**Recommendation:** ⭐⭐⭐⭐ Best long-term solution

---

## Comparison Matrix

| Tool | Setup | UI | Export | macOS | Score |
|------|-------|----|----|-------|-------|
| Audacity | Easy | ⭐⭐⭐⭐ | TXT→JSON | ✅ | 4/5 |
| Label Studio | Medium | ⭐⭐⭐⭐⭐ | JSON | ✅ | 5/5 |
| Sonic Visualiser | Easy | ⭐⭐⭐ | RDF→JSON | ✅ | 3/5 |
| Praat | Easy | ⭐⭐ | TextGrid→JSON | ✅ | 2/5 |
| ELAN | Medium | ⭐⭐ | XML→JSON | ✅ | 2/5 |
| audio-annotator | Medium | ⭐⭐⭐ | JSON | ✅ | 3/5 |
| Custom (wavesurfer) | Hard | ⭐⭐⭐⭐⭐ | JSON | ✅ | 4/5 |

---

## Recommended Approach

### Phase 1: Quick Start (4 files)
**Use Audacity + Conversion Script**

1. Install Audacity
2. Annotate 4 files manually
3. Write simple Python script to convert .txt → JSON
4. Pros: Fast to start, good visualization
5. Time: ~2 hours total

### Phase 2: Scale Up (10+ files)
**Use Label Studio**

1. Install Label Studio
2. Set up audio annotation project
3. Import all files
4. Native JSON export
5. Pros: Built for this purpose, scalable
6. Time: ~30 min setup, faster annotation

### Phase 3: Production (Optional)
**Build Custom Tool**

Only if we need:
- Integration with training pipeline
- Custom preprocessing
- Automated quality checks

---

## Decision

For **immediate needs (4 files)**: 
✅ **Audacity + Conversion Script**

For **future scaling (10+ files)**:
✅ **Label Studio**

---

## Next Steps

1. Install Audacity: `brew install --cask audacity`
2. Test annotation workflow with one file
3. Create conversion script: `src/data_prep/convert_audacity_labels.py`
4. Document process in VALIDATION.md

---

## Conversion Script Example

```python
# src/data_prep/convert_audacity_labels.py
import json
import librosa

def convert_audacity_to_json(txt_path, audio_path, output_path):
    """
    Convert Audacity label export to our JSON format
    """
    # Get audio info
    audio, sr = librosa.load(audio_path, sr=None, duration=1)
    duration = librosa.get_duration(path=audio_path)
    
    annotations = []
    with open(txt_path, 'r') as f:
        for i, line in enumerate(f):
            parts = line.strip().split('\t')
            if len(parts) == 3:
                start, end, label = parts
                annotations.append({
                    "id": f"chunk_{i:03d}",
                    "start_time": float(start),
                    "end_time": float(end),
                    "label": label,
                    "confidence": "high"
                })
    
    output = {
        "audio_file": os.path.basename(audio_path),
        "duration": duration,
        "sample_rate": 44100,
        "annotations": annotations
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
```

---

**Research Date:** 2025-10-18
**Status:** ✅ Decision Made

## Final Decision

**Selected Tool: Label Studio** ⭐⭐⭐⭐⭐

**Reasons:**
- User already familiar with Audacity (used for recording)
- Label Studio purpose-built for ML annotation
- Native JSON export (no conversion needed)
- Better workflow for multiple files
- Progress tracking and review features
- Scalable for future recordings (10+)
- Open source (Apache 2.0 license)

**Installation:** ✅ Complete (v1.21.0)
**Configuration:** ✅ Created (`tools/label-studio/label-studio-config.xml`)
**Guide:** ✅ Created (`tools/label-studio/LABEL_STUDIO_GUIDE.md`)

**Next:** Follow the guide to start annotating!
