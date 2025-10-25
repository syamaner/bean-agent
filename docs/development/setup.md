# Development Guide

## Python Environment Setup

This project uses Python 3.11+ and requires proper virtual environment management to ensure consistent dependencies across development and production environments.

### Initial Setup

1. **Create Virtual Environment**
   ```bash
   python3.11 -m venv venv
   ```

2. **Activate Virtual Environment**
   ```bash
   # On macOS/Linux
   source venv/bin/activate
   
   # Your prompt should now show (venv) prefix
   ```

3. **Install Dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Daily Workflow

**IMPORTANT**: Always activate the virtual environment before running any Python scripts or commands.

```bash
# At the start of each session
source venv/bin/activate

# Verify you're using the correct Python
which python  # Should show: /Users/.../coffee-roasting/venv/bin/python

# Run your scripts
python src/training/train.py
python src/inference/first_crack_detector.py --microphone
```

### Managing Dependencies

#### Adding New Dependencies

When you install a new package:

```bash
# Activate environment first
source venv/bin/activate

# Install the package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt
```

#### Updating Existing Dependencies

```bash
# Activate environment first
source venv/bin/activate

# Update a specific package
pip install --upgrade package-name

# Or update all packages
pip list --outdated
pip install --upgrade package-name1 package-name2

# Update requirements.txt
pip freeze > requirements.txt
```

#### Installing from requirements.txt

After pulling changes or switching branches:

```bash
# Activate environment first
source venv/bin/activate

# Install/update all dependencies
pip install -r requirements.txt
```

### Verifying Your Environment

```bash
# Check Python version
python --version  # Should show 3.11.x

# Check installed packages
pip list

# Verify PyTorch MPS support (for M3 Mac)
python -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
```

### Common Issues

#### Wrong Python Version
```bash
# Check which Python is being used
which python
python --version

# If not using venv Python, activate the environment
source venv/bin/activate
```

#### Missing Dependencies
```bash
# Reinstall all dependencies
source venv/bin/activate
pip install -r requirements.txt
```

#### Module Not Found Errors
```bash
# Verify you're in the correct environment
which python

# Reinstall the specific package
pip install package-name

# Or reinstall everything
pip install -r requirements.txt
```

## Project Structure

```
coffee-roasting/
├── venv/                    # Virtual environment (not in git)
├── requirements.txt         # Python dependencies
├── src/
│   ├── data/               # Data loading and preprocessing
│   ├── models/             # Model definitions
│   ├── training/           # Training scripts
│   ├── inference/          # Inference and detection
│   └── utils/              # Utility functions
├── data/
│   ├── raw/                # Raw audio recordings
│   ├── processed/          # Processed datasets
│   └── annotations/        # Manual annotations
├── experiments/            # Training experiments and results
├── tools/
│   ├── mcp/                # MCP servers (Phase 2)
│   └── annotation/         # Annotation tools
├── tests/                  # Unit and integration tests
└── docs/                   # Documentation
```

## Running Scripts

### Training

```bash
source venv/bin/activate
python src/training/train.py --config experiments/configs/default.yaml
```

### Inference

```bash
# File-based inference
source venv/bin/activate
python src/inference/first_crack_detector.py \
    --audio data/raw/roast1.wav \
    --checkpoint experiments/final_model/model.pt

# Live microphone inference
source venv/bin/activate
python src/inference/first_crack_detector.py \
    --microphone \
    --checkpoint experiments/final_model/model.pt
```

### Testing

```bash
source venv/bin/activate
python -m pytest tests/
```

## Best Practices

### 1. Always Use Virtual Environment
- ✅ `source venv/bin/activate` before running scripts
- ❌ Never run scripts with system Python

### 2. Keep requirements.txt Updated
- Update after installing new packages
- Commit changes to version control
- Review dependencies periodically

### 3. Document Environment Issues
- If you encounter environment-specific issues, document them
- Add solutions to this guide

### 4. Use Consistent Python Version
- Project requires Python 3.11+
- Check version: `python --version`
- M3 Mac optimization requires 3.11+

### 5. Clean Environment
```bash
# If things get messy, recreate environment
deactivate
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## IDE Configuration

### VS Code
Add to `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.terminal.activateEnvironment": true
}
```

### PyCharm
1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment
3. Select: `/path/to/coffee-roasting/venv/bin/python`

## MCP Server Development (Phase 2)

When developing MCP servers, each server may have its own requirements:

```bash
# Audio detection server
source venv/bin/activate
cd tools/mcp/audio_server
pip install -r requirements.txt

# Roaster control server
cd tools/mcp/roaster_server
pip install -r requirements.txt
```

## Troubleshooting

### Import Errors
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:<PROJECT_ROOT>"
```

**Note**: Replace `<PROJECT_ROOT>` with your actual project path.

### PyTorch MPS Issues
```bash
# Verify MPS support
python -c "import torch; print(torch.backends.mps.is_available())"

# If false, reinstall PyTorch
pip uninstall torch torchaudio
pip install torch torchaudio
```

### Dependency Conflicts
```bash
# Check for conflicts
pip check

# Resolve by updating conflicting packages
pip install --upgrade package-name
```
