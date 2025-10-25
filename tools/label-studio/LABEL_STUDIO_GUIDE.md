# Label Studio Guide for Audio Annotation

Complete guide for using Label Studio to annotate coffee roast audio files for first crack detection.

## What is Label Studio?

Label Studio is an open-source data labeling platform that supports audio, images, text, and more. Perfect for ML training data preparation.

- **License**: Apache 2.0 (Open Source)
- **GitHub**: https://github.com/HumanSignal/label-studio
- **Docs**: https://labelstud.io/guide/

---

## Installation

Already installed in your virtual environment:

```bash
./venv/bin/pip install label-studio
```

Version: 1.21.0 ✅

---

## Quick Start

### 1. Start Label Studio Server

```bash
# From project root
./venv/bin/label-studio start
```

This will:
- Start web server on http://localhost:8080
- Open browser automatically
- Create local database in `~/.local/share/label-studio/`

### 2. Initial Setup (First Time Only)

1. Browser opens to http://localhost:8080
2. Create account (local only, stored on your machine)
   - Email: your@email.com (can be anything)
   - Password: choose a password
3. You'll be taken to Projects page

---

## Creating the Audio Annotation Project

### Step 1: Create New Project

1. Click **"Create Project"**
2. Project Name: `Coffee Roast First Crack Detection`
3. Description: `Annotating first crack events in coffee roasting audio recordings`

### Step 2: Import Audio Files

**Option A: Import from Local Files**
1. Go to "Data Import" tab
2. Click "Upload Files"
3. Select your 4 WAV files from `data/raw/`:
   - roast-1-costarica-hermosa-hp-a.wav
   - roast-2-costarica-hermosa-hp-a.wav
   - roast-3-costarica-hermosa-hp-a.wav
   - roast-4-costarica-hermosa-hp-a.wav

**Option B: Import from Directory** (Better for large files)
1. Set up local file serving (see Advanced Setup below)

### Step 3: Configure Labeling Interface

1. Go to "Settings" → "Labeling Interface"
2. Click "Code" view
3. Copy content from `tools/label-studio/label-studio-config.xml`
4. Paste into the editor
5. Click "Save"

**What this configuration provides:**
- Audio player with waveform
- Two label types: `no_first_crack` (blue) and `first_crack` (red)
- Zoom and speed controls
- Optional notes field

---

## Annotation Workflow

### Basic Workflow

1. **Open a task**: Click on an audio file from the task list
2. **Listen**: Play the audio, identify first crack timing
3. **Select region**: 
   - Click and drag on waveform to select time range
   - Or use the region controls
4. **Label region**:
   - Click "first_crack" (red) for regions with first crack
   - Click "no_first_crack" (blue) for regions without
5. **Add notes** (optional): Add any observations
6. **Submit**: Click "Submit" to save annotations
7. **Next**: Automatically moves to next audio file

### Tips for Efficient Annotation

1. **Use keyboard shortcuts**:
   - Space: Play/Pause
   - ← →: Skip backward/forward
   - Ctrl/Cmd + Enter: Submit

2. **Zoom in** for precise timing:
   - Use zoom slider to see waveform details
   - Helps identify exact first crack start

3. **Adjust speed** if needed:
   - Slow down (0.5x) to hear subtle cracks
   - Speed up (2x) for pre-crack sections

### Recommended Annotation Strategy (Event Detection)

We're using **event detection** rather than phase-based annotation. This means marking individual crack sounds, not continuous time periods.

For each ~10-minute roast:

1. **Quick listen**: Play entire file to identify approximate first crack time
   - First crack typically occurs around 8-10 minutes
   - Note the timestamp for reference

2. **Pre-crack sections** (0 to first crack):
   - **Sparse sampling**: Create 3-5 representative segments
   - Each segment: ~5 seconds duration
   - Spread throughout the pre-crack period
   - Label: `no_first_crack` (blue)
   - Purpose: Teach model what background roasting sounds like
   - ⚠️ No need to annotate every second—just representative samples

3. **First crack events** (~8-10 minutes onwards):
   - **Event-based**: Mark each individual crack sound
   - Each event: 1-3 seconds duration
   - Be precise—zoom in to capture just the crack sound
   - Label: `first_crack` (red)
   - Use 0.5x speed if needed to hear subtle cracks
   - Purpose: Precise event detection for each crack

4. **Post-crack sections** (after first crack activity ends):
   - **Sparse sampling**: Create 2-3 representative segments
   - Each segment: ~5 seconds duration
   - Label: `no_first_crack` (blue)

**Expected Result**: 
- Pre-crack: 3-5 short negative samples
- First crack: 15-30 individual crack events (varies by roast intensity)
- Post-crack: 2-3 short negative samples
- Total: ~20-40 regions per file (mostly crack events)

---

## Export Annotations

### Export to JSON

1. Go to project page
2. Click "Export" button
3. Choose **"JSON"** format
4. Download file

### JSON Structure

```json
[
  {
    "id": 1,
    "data": {
      "audio": "/data/upload/1/roast-1-costarica-hermosa-hp-a.wav"
    },
    "annotations": [
      {
        "id": 1,
        "completed_by": 1,
        "result": [
          {
            "value": {
              "start": 420.5,
              "end": 450.5,
              "labels": ["first_crack"]
            },
            "from_name": "label",
            "to_name": "audio",
            "type": "labels"
          }
        ]
      }
    ]
  }
]
```

### Convert to Our Format

We'll create a conversion script: `src/data_prep/convert_labelstudio_export.py`

```python
# Converts Label Studio JSON → Our annotation JSON format
# Run after exporting from Label Studio
```

---

## Advanced Setup

### Serve Local Files (For Large Audio Files)

Label Studio can access files directly without uploading:

1. **Option A: Use Label Studio's local file serving**

```bash
# Start with local file serving enabled
./venv/bin/label-studio start --label-config tools/label-studio/label-studio-config.xml \
    --input-path data/raw \
    --input-format audio-dir
```

2. **Option B: Create import JSON**

Use the pre-created `tools/label-studio/import-tasks.json`:
```json
[
  {"audio": "<PROJECT_ROOT>/data/raw/roast-1-costarica-hermosa-hp-a.wav"},
  {"audio": "<PROJECT_ROOT>/data/raw/roast-2-costarica-hermosa-hp-a.wav"},
  {"audio": "<PROJECT_ROOT>/data/raw/roast-3-costarica-hermosa-hp-a.wav"},
  {"audio": "<PROJECT_ROOT>/data/raw/roast-4-costarica-hermosa-hp-a.wav"}
]
```

**Note**: Replace `<PROJECT_ROOT>` with your actual project path.

Then import via UI: Data Import → Upload → Select `tools/label-studio/import-tasks.json`

---

## Project Management

### Viewing Progress

- **Tasks**: Shows all audio files and annotation status
- **Completed**: Green checkmark
- **In Progress**: Yellow indicator  
- **Not Started**: No indicator

### Quality Control

1. **Review mode**: Go back and review completed annotations
2. **Edit**: Click on completed task to edit
3. **Delete**: Remove incorrect regions

### Backup Annotations

Regularly export and save:

```bash
# In project settings
Export → JSON → Save to: data/labels/labelstudio-backup-YYYY-MM-DD.json
```

---

## Troubleshooting

### Audio Not Playing

- Check file format (WAV should work)
- Try browser console for errors
- Ensure file path is correct

### Slow Performance

- Label Studio loads entire audio into browser
- For 10+ minute files, may be slow
- Solution: Pre-process large files into smaller chunks if needed

### Can't See Waveform

- Waveform generation requires audio decoding
- Large files may take time to load
- Check browser console for errors

### Lost Annotations

- Annotations saved immediately on Submit
- Check Export to verify
- Database at: `~/.local/share/label-studio/label_studio.sqlite3`

---

## Workflow Integration

### Full Pipeline

```
1. Record roast session (Audacity)
   ↓
2. Save WAV to data/raw/
   ↓
3. Annotate in Label Studio
   ↓
4. Export JSON from Label Studio
   ↓
5. Convert to our format (Python script)
   ↓
6. Process annotations → Audio chunks
   ↓
7. Train model
```

---

## Comparison: Audacity vs Label Studio

| Feature | Audacity | Label Studio |
|---------|----------|--------------|
| Waveform | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Ease of use | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Audio playback | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Labeling UI | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| JSON export | ❌ (needs script) | ✅ Native |
| Multi-file | ❌ One at a time | ✅ Batch mode |
| Progress tracking | ❌ | ✅ |
| Review/Edit | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Verdict**: Label Studio is better for ML annotation workflow!

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Play/Pause | Space |
| Skip forward | → |
| Skip backward | ← |
| Submit annotation | Ctrl/Cmd + Enter |
| Undo | Ctrl/Cmd + Z |
| Delete region | Delete/Backspace |

---

## Next Steps

After annotating all 4 files:

1. ✅ Export annotations to JSON
2. ✅ Convert to our format (`src/data_prep/convert_labelstudio_export.py`)
3. ✅ Process annotations → audio chunks (`src/data_prep/audio_processor.py`)
4. ✅ Create train/val/test splits
5. ✅ Begin model training

---

## Resources

- [Label Studio Documentation](https://labelstud.io/guide/)
- [Audio Labeling Tutorial](https://labelstud.io/templates/audio_classification.html)
- [JSON Export Format](https://labelstud.io/guide/export.html)

---

**Created**: 2025-10-18  
**Last Updated**: 2025-10-18
