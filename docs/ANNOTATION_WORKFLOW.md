# Audio Annotation Workflow Guide

Complete guide for annotating coffee roast audio recordings to identify first crack events. Use this guide for new recordings or revisiting existing annotations.

---

## Quick Reference

### For New Recordings

```bash
# 1. Copy WAV file to data/raw/
cp ~/path/to/new-roast.wav data/raw/

# 2. Start Label Studio
./venv/bin/label-studio start

# 3. Add file to existing project (or create new project)
# 4. Annotate in Label Studio
# 5. Export annotations
# 6. Convert to our format
./venv/bin/python src/data_prep/convert_labelstudio_export.py \
    --input data/labels/project-1-at-YYYY-MM-DD-HH-MM-XXXXXX.json \
    --output data/labels

# 7. Process into audio chunks (Task 2.6)
# (Script to be created)
```

### For Revisiting Existing Annotations

```bash
# 1. Start Label Studio
./venv/bin/label-studio start

# 2. Open existing project at http://localhost:8080
# 3. Edit annotations
# 4. Re-export and reconvert
```

---

## Detailed Workflow

## Step 1: Prepare Audio Files

### 1.1 Record Roasting Session
- Use Audacity or your preferred recording software
- **Settings**: 44.1kHz, 16-bit, Mono (or Stereo - will convert to Mono)
- **Format**: WAV (uncompressed)
- **Duration**: Full roast cycle (~10-15 minutes)
- **Filename convention**: `roast-N-bean-origin-profile.wav`
  - Example: `roast-5-ethiopia-natural-med.wav`

### 1.2 Copy to Project
```bash
# Copy to data/raw/
cp ~/Desktop/recordings/roast-5-*.wav data/raw/

# Verify
ls -lh data/raw/roast-5-*.wav
```

---

## Step 2: Start Label Studio

### 2.1 Launch Server
```bash
# From project root
./venv/bin/label-studio start
```

**What happens:**
- Server starts at http://localhost:8080
- Browser opens automatically
- If already set up, you'll see existing projects

### 2.2 Sign In
- Use your existing local credentials
- All data stored locally in `~/.local/share/label-studio/`

---

## Step 3: Set Up Project (First Time Only)

Skip this if you already have the "Coffee Roast First Crack Detection" project.

### 3.1 Create Project
1. Click **"Create Project"**
2. **Project Name**: `Coffee Roast First Crack Detection`
3. **Description**: `Annotating first crack events in coffee roasting audio`
4. Click **"Create"**

### 3.2 Configure Labeling Interface
1. Go to **Settings** → **Labeling Interface**
2. Click **"Code"** view
3. Copy content from `tools/label-studio/label-studio-config.xml`:

```xml
<View>
  <Header value="Coffee Roast First Crack Detection"/>
  <Text name="instructions" value="Listen to the audio and mark regions where first crack occurs. Mark other regions as no_first_crack."/>
  
  <Audio name="audio" value="$audio" zoom="true" speed="true"/>
  
  <Labels name="label" toName="audio">
    <Label value="no_first_crack" background="#3498db"/>
    <Label value="first_crack" background="#e74c3c"/>
  </Labels>
  
  <TextArea name="notes" toName="audio" 
            placeholder="Optional notes about this region (e.g., 'very clear pops', 'subtle', etc.)"
            editable="true"/>
</View>
```

4. Click **"Save"**

---

## Step 4: Import Audio Files

### Option A: Upload Single File (Recommended for New Files)

1. In project, go to **"Data Import"** tab
2. Click **"Upload Files"**
3. Select WAV file(s) from `data/raw/`
4. Click **"Import"**

### Option B: Bulk Import with JSON

For multiple files, create an import JSON:

```bash
# Create import-new-files.json
cat > tools/label-studio/import-new-files.json << 'EOF'
[
  {"audio": "<PROJECT_ROOT>/data/raw/roast-5-ethiopia-natural-med.wav"},
  {"audio": "<PROJECT_ROOT>/data/raw/roast-6-colombia-washed-light.wav"}
]
EOF
```

**Note**: Replace `<PROJECT_ROOT>` with your actual project path.

Then import:
1. Go to **Data Import** tab
2. Click **"Upload Files"**
3. Select `tools/label-studio/import-new-files.json`
4. Click **"Import"**

---

## Step 5: Annotate Audio

### 5.1 Open Task
- Click on an audio file from the task list
- Audio player loads with waveform

### 5.2 Annotation Strategy: Event Detection Approach

**Goal**: Mark individual crack sounds as discrete events, not continuous phases.

**For each ~10-minute roast:**

1. **Quick Listen** (first pass)
   - Play entire file at normal speed
   - Note approximate first crack timestamp
   - Example: "First crack around 8:30"
   - Note intensity: sparse cracks vs. rapid succession

2. **Pre-First Crack** (0 to FC start — typically first ~8 minutes)
   - **Sparse negative sampling**
   - Create 3-5 short segments (~5 seconds each)
   - Spread throughout this period (e.g., at 1:00, 3:00, 5:00, 7:00)
   - Label: `no_first_crack` (blue)
   - Purpose: Teach model what background roasting sounds like
   - ⚠️ **Important**: Do NOT annotate every second—just representative samples
   - Goal: 3-5 negative samples

3. **First Crack Events** (FC start to FC end — typically 8-10 min onwards)
   - **Event-based annotation**
   - Listen carefully, use 0.5x speed if needed
   - Use zoom to see waveform details
   - For EACH individual crack sound:
     - Create a short region (1-3 seconds)
     - Center on the crack sound
     - Label: `first_crack` (red)
   - Be precise—capture just the crack event, not gaps between
   - ⚠️ **Important**: Mark every single crack you hear
   - Goal: 15-30 crack events (varies by roast intensity)

4. **Post-First Crack** (FC end to file end)
   - **Sparse negative sampling**
   - Create 2-3 short segments (~5 seconds each)
   - Label: `no_first_crack` (blue)
   - Goal: 2-3 negative samples

**Expected Output per file:**
- Pre-crack negative samples: 3-5 regions
- First crack events: 15-30 regions (each 1-3 seconds)
- Post-crack negative samples: 2-3 regions
- **Total: ~20-40 regions** (mostly crack events)

### 5.3 Workflow Tips

**Create a Region:**
1. Click and drag on waveform to select time range
2. Or: Use region controls to set start/end precisely

**Label a Region:**
1. Select region
2. Click label: `first_crack` (red) or `no_first_crack` (blue)
3. Optional: Add notes in text field

**Keyboard Shortcuts:**
- **Space**: Play/Pause
- **← →**: Skip backward/forward
- **Ctrl/Cmd + Z**: Undo
- **Delete/Backspace**: Delete selected region
- **Ctrl/Cmd + Enter**: Submit annotation

**Pro Tips:**
- Use zoom slider for precise event timing
- Use speed controls (0.5x) for subtle first cracks
- Focus on precision for crack events—each should capture just that sound
- For negative samples, any representative 5-second segment is fine
- Add notes for ambiguous sounds ("faint crack?" or "mechanical noise")
- ⚠️ **Avoid overlapping regions**—each timestamp should have one label

### 5.4 Submit Annotation
1. Review all regions
2. Click **"Submit"**
3. Moves to next file automatically

---

## Step 6: Export Annotations

### 6.1 Export from Label Studio

1. Go to project main page
2. Click **"Export"** button (top right)
3. Select **"JSON"** format
4. Click **"Export"**
5. Download saves as: `project-1-at-YYYY-MM-DD-HH-MM-XXXXXX.json`

### 6.2 Save to Project

```bash
# Move to data/labels/
mv ~/Downloads/project-1-at-*.json data/labels/

# Create timestamped backup
cp data/labels/project-1-at-*.json data/labels/labelstudio-export-$(date +%Y%m%d-%H%M).json

# List to verify
ls -lh data/labels/*.json
```

---

## Step 7: Convert to Our Format

### 7.1 Run Conversion Script

```bash
./venv/bin/python src/data_prep/convert_labelstudio_export.py \
    --input data/labels/project-1-at-YYYY-MM-DD-HH-MM-XXXXXX.json \
    --output data/labels \
    --data-root data/raw
```

**Parameters:**
- `--input`: Path to Label Studio JSON export
- `--output`: Directory to save converted annotations (usually `data/labels`)
- `--data-root`: Where WAV files are located (default: `data/raw`)

**What it does:**
- Reads Label Studio export
- For each audio file, creates a JSON in our format
- Strips Label Studio hash prefixes from filenames
- Calculates audio duration
- Saves as: `roast-N-*.json`

### 7.2 Verify Conversion

```bash
# Check created files
ls -lh data/labels/roast-*.json

# View summary statistics
./venv/bin/python -c "
import json
from pathlib import Path

for f in sorted(Path('data/labels').glob('roast-*.json')):
    d = json.load(f.open())
    anns = d['annotations']
    fc = [a for a in anns if a['label']=='first_crack']
    nfc = [a for a in anns if a['label']=='no_first_crack']
    print(f'=== {f.name} ===')
    print(f'Duration: {d[\"duration\"]:.1f}s ({d[\"duration\"]/60:.1f} min)')
    print(f'Total regions: {len(anns)}')
    print(f'  - first_crack: {len(fc)}')
    print(f'  - no_first_crack: {len(nfc)}')
    if fc:
        fc_start = min(a['start_time'] for a in fc)
        print(f'First crack starts: {fc_start:.1f}s ({fc_start/60:.1f} min)')
    print()
"
```

**Expected Output:**
```
=== roast-1-costarica-hermosa-hp-a.json ===
Duration: 639.7s (10.7 min)
Total regions: 23
  - first_crack: 4
  - no_first_crack: 19
First crack starts: 526.5s (8.8 min)
```

### 7.3 Inspect JSON Structure

```bash
# View one annotation file
cat data/labels/roast-1-costarica-hermosa-hp-a.json
```

**Our Format:**
```json
{
  "audio_file": "roast-1-costarica-hermosa-hp-a.wav",
  "duration": 639.72,
  "sample_rate": 44100,
  "annotations": [
    {
      "id": "chunk_000",
      "start_time": 0.0,
      "end_time": 30.43,
      "label": "no_first_crack",
      "confidence": "high"
    },
    ...
  ]
}
```

---

## Step 8: Process into Audio Chunks (Task 2.6)

**Note**: Script to be created in Task 2.6.

```bash
# Will extract audio segments based on annotations
python src/data_prep/audio_processor.py --annotations data/labels/

# Output:
#   data/processed/first_crack/*.wav
#   data/processed/no_first_crack/*.wav
```

---

## Revisiting Existing Annotations

### When to Revisit
- Found mislabeled regions
- Want to add more precision to first crack timing
- Need to add/remove regions

### Workflow

1. **Start Label Studio**
   ```bash
   ./venv/bin/label-studio start
   ```

2. **Open Project**
   - Go to http://localhost:8080
   - Click on "Coffee Roast First Crack Detection"

3. **Find Task**
   - Tasks list shows all audio files
   - Green checkmark = completed
   - Click on any task to edit

4. **Edit Annotations**
   - Modify existing regions
   - Add new regions
   - Delete incorrect regions
   - Update labels

5. **Re-Submit**
   - Click "Update" (not "Submit" - already completed)

6. **Re-Export**
   - Export → JSON
   - Creates new timestamped export

7. **Re-Convert**
   ```bash
   ./venv/bin/python src/data_prep/convert_labelstudio_export.py \
       --input data/labels/project-1-at-NEW-TIMESTAMP.json \
       --output data/labels
   ```

8. **Re-Process Chunks** (Task 2.6)
   - Will overwrite previous chunks
   - Ensure downstream pipeline is re-run

---

## Adding Many New Recordings

### Batch Workflow

1. **Copy all files**
   ```bash
   cp ~/roast-sessions/*.wav data/raw/
   ```

2. **Create bulk import JSON**
   ```bash
   # Generate import JSON automatically
   ./venv/bin/python -c "
   import json
   from pathlib import Path
   
   files = sorted(Path('data/raw').glob('roast-*.wav'))
   tasks = [{'audio': str(f.absolute())} for f in files]
   
   with open('tools/label-studio/import-all-current.json', 'w') as f:
       json.dump(tasks, f, indent=2)
   
   print(f'Created import JSON with {len(tasks)} files')
   "
   ```

3. **Import to Label Studio**
   - Data Import → Upload Files
   - Select `tools/label-studio/import-all-current.json`

4. **Annotate incrementally**
   - Do 2-3 files per session
   - Export regularly
   - Convert after each export batch

---

## Troubleshooting

### Label Studio won't start
```bash
# Check if already running
ps aux | grep label-studio

# Kill existing process
pkill -f label-studio

# Restart
./venv/bin/label-studio start
```

### Can't find exported JSON
- Check `~/Downloads/`
- Look for `project-1-at-*.json`
- Export again if lost

### Conversion script errors
```bash
# Verify input file exists
ls -lh data/labels/project-1-at-*.json

# Check WAV files exist
ls -lh data/raw/*.wav

# Run with explicit paths
./venv/bin/python src/data_prep/convert_labelstudio_export.py \
    --input data/labels/YOUR-EXPORT.json \
    --output data/labels \
    --data-root data/raw
```

### Missing first crack labels
- Re-listen to file in Label Studio
- Check if region was created but not labeled
- Add label and re-export

---

## Best Practices

### Annotation Quality
- ✅ Listen to full file first before annotating
- ✅ Use 0.5x speed for subtle crack sounds
- ✅ Mark every individual crack event you hear (1-3 seconds each)
- ✅ Use sparse sampling (3-5 segments) for pre-crack background
- ✅ Add notes for ambiguous sounds
- ✅ Be precise—zoom in to capture just the crack event
- ❌ Don't rush - precision matters for model training
- ❌ Don't annotate every second of pre-crack period
- ❌ Don't create overlapping regions
- ❌ Don't create 30-second chunks—focus on event detection

### Data Management
- ✅ Export after annotating each batch
- ✅ Keep timestamped backups of exports
- ✅ Version control annotation JSONs (git)
- ✅ Document any annotation decisions in notes
- ❌ Don't delete original exports
- ❌ Don't edit converted JSONs manually (re-export instead)

### Consistency
- ✅ Use same criteria across all files
- ✅ First crack = individual distinct popping sounds (1-3 seconds each)
- ✅ Negative samples = representative 5-second segments from non-crack periods
- ✅ Mark every crack event consistently
- ✅ Use sparse sampling for all non-crack periods
- ❌ Don't change strategy mid-annotation
- ❌ Don't mix event detection with phase-based annotation

---

## File Structure Reference

```
coffee-roasting/
├── data/
│   ├── raw/                          # Original WAV files
│   │   ├── roast-1-*.wav
│   │   ├── roast-2-*.wav
│   │   └── ...
│   ├── labels/                       # Annotation files
│   │   ├── labelstudio-export-*.json      # Backups
│   │   ├── project-1-at-*.json            # Exports
│   │   ├── roast-1-*.json                 # Converted (our format)
│   │   └── ...
│   └── processed/                    # Audio chunks (Task 2.6)
│       ├── first_crack/*.wav
│       └── no_first_crack/*.wav
├── src/data_prep/
│   └── convert_labelstudio_export.py # Conversion script
└── tools/label-studio/
    ├── LABEL_STUDIO_GUIDE.md         # Detailed Label Studio docs
    ├── label-studio-config.xml       # Labeling interface
    └── import-tasks.json             # Import helpers
```

---

## Quick Command Reference

```bash
# Start Label Studio
./venv/bin/label-studio start

# Stop Label Studio
# Ctrl+C in terminal, or:
pkill -f label-studio

# Convert export
./venv/bin/python src/data_prep/convert_labelstudio_export.py \
    --input data/labels/project-1-at-TIMESTAMP.json \
    --output data/labels

# View annotation stats
./venv/bin/python -c "
import json
from pathlib import Path
for f in sorted(Path('data/labels').glob('roast-*.json')):
    d = json.load(f.open())
    print(f'{f.name}: {len(d[\"annotations\"])} regions')
"

# Backup annotations
tar -czf annotations-backup-$(date +%Y%m%d).tar.gz data/labels/*.json
```

---

**Last Updated**: 2025-10-18  
**Version**: 1.0
