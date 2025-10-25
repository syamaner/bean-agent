# Coffee Roasting

## Project Overview

This project aims to build a set of MCP server tools that will automate coffee roasting process in auto pilot mode using a Hottop KN8828B-2K+ roaster.

We will be implementing this solution in multiple phases and as we learn, some of the approaches will be adjusted.

Relevant Links
- [Hottop KN8828B-2K+ product page](https://www.hottopamericas.com/KN-8828B-2Kplus.html)
- [Hottop python client library - pyhottop](https://github.com/splitkeycoffee/pyhottop)
- [Huggingface Audio spectogram transformer](https://huggingface.co/docs/transformers/en/model_doc/audio-spectrogram-transformer)
- [Tutorial: Fine-Tune the Audio Spectrogram Transformer With 🤗 Transformers](https://towardsdatascience.com/fine-tune-the-audio-spectrogram-transformer-with-transformers-73333c9ef717/)

## Objectives

The project will build an agentic solution that handles the following.

- A roasting agent using a microphone to detect if first crack happened or not
    - No first crack
    - First crack detected
      - Included the timestamp first crack detected.
- An agent that reads and writes control data using `pyhottop` client library this agent runs on a device that has usb connection to the roaster.
  - Read
    - Chamber temperature
    - Bean temperature
    - Fan speed (% 0-100)
    - Heat rate (% 0-100)
  - Modify 
    - Fan speed (% 0-100)
    - Heat rate (% 0-100)
    - Stop the roast
    - Open the bean drop door and start cooling process
  - Orchestrator
    - Manages the roast process using an LLM
      - Gets the current readings and whether or not first crack happened
      - Adjusts the controls
      - Decides if the roast should be finished or not.
    - Key roast metrics:
      - Rate of temperature rise in past 60 seconds
        - This is going to be helpful in conjunction with current roast phase to control the fan and the heat to avoid too fast development or a stalled roast.
      - Development time
        - Percentage of time spent in First crack phase and before second crack phase.
        - This needs to be around 15%-20% of the whole roast.
            - For a light roast and based on this hardware, we want to complete roasting around 195°C is reached.
            - This is why it is important to adjust controls to stretch development time to be long enough to cover 15% - 20% of the development time.
        - This is why reducing heat and increasing fan in first crack is crucial to extend development time.
        - Roast time starts when beans are added (temperature reading will have a sudden drop)
        - The moment drop detected is the beginning of roasting time frame.
        - All times relative to this moment. 

### Implementation phases

1. Fine tuning an Audio Spectrogram Transformer with sample data.
  - This phase will begin with minimal data and as we build our fine tuning and evaluation framework, we will capture more data and improve our chosen metrics.
2. We will start building our roaster agent with MCP tools that will allow reading and updating the roaster as well as controlling the microphone to detect first crack or not.
3. We will hook these as MCP to an MCP client / orchestrator that will manage the roasting process

## Architecture
- An MCP tool that provides access to the Audio spectrogram transformer model that uses a microphone to detect first crack and return first crack started or not.
- An MCP tool that controls the roaster equipment using pyhottop
- Orchestrator will be a workflow engine such as n8n and uses an LLM in conjunction with these MCP tools.
  - Key roast metric will be part of the prompt for the llm as we do readings every few seconds using MCP tools.

### Hardware requirements
- [Hottop KN8828B-2K+ product page](https://www.hottopamericas.com/KN-8828B-2Kplus.html)
- A MacOs laptop with M3 arm cpu.
  - This is where all components will run when we have the project finished.
  - This laptop should also be the hardware where we fine tune
- A USB Microphone for the laptop where the roast will happen
- A USB connection from the laptop to hottop roaster. 

### Audio Requirements
- Sample rate: 44.1kHz (recommended for compatibility)
- Format: WAV (uncompressed) 
- Bit depth: 16-bit minimum
- Channels: Mono sufficient
- Recording duration: Full roast cycle (10-15 minutes)

### Model Performance Targets (enhanced by warp)
- First crack detection accuracy: >95%
- Detection latency: <2 seconds
- False positive rate: <5%

## Prerequisites (enhanced by warp)
- Python 3.11+ (M3 Max compatibility)
- PyTorch with MPS support
- Transformers (Hugging Face)
- librosa for audio processing
- ~50GB free disk space for training
 

## Development

### Phase 1

This is our current focus. I have 4 wav recordings of roast sessions and I will need to preprocess these for fine tuning a suitable Huggingface Audio spectrogram transformer.

Use these as starting points to brainstorm approaches:
- [Huggingface Audio spectrogram transformer](https://huggingface.co/docs/transformers/en/model_doc/audio-spectrogram-transformer)
- [Tutorial: Fine-Tune the Audio Spectrogram Transformer With 🤗 Transformers](https://towardsdatascience.com/fine-tune-the-audio-spectrogram-transformer-with-transformers-73333c9ef717/)

What we do here will be reusable as we collect more data, we will keep fine tuning for improving the model accuracy and performance.

Let's start with fine tuning approach using the resources proposed previously.

We will approach it as following:

- Manual dataset preparation
  - Help me to split data to sensible chunks and provide me starting labelling files (formats) and directory structure and I will do that manually
    - Suggest me most suitable Audio sampling requirements (sample rate, format for microphone input)
  - Propose a code directory structure for
    - Data 
      - Labelled data. The scripts should to train / test / eval data split. But ensure each split has balanced samples for no first crack and first crack samples based on labels.
    - Training and evaluation code
  - Help me implement and test the code using manually prepared dataset.
- All the scripts to have an easy to use fine tuning pipeline and the evaluation / test scripts
  - We should see how native Mac M3 processor works but we can also consider to run these on a linux machine with Nvidia RTX-4090 as well if needed. Ideally we do it using existing resources.
- As we verify code works let's automate the dataset preparation
- Propose open source tools that can help semi automating the data preparation:
    - A UI showing the audio and ability to select a time range and play
    - A Label for the selected range and then being able to expose these in one go in the expected dataset format to feed our fine tuning pipeline.
- If no such tool, let's build one.
    - This is what code directory structure matters.

We will worry about Phase 2 and 3 later.


### Phase 2:

We will build MCP tools. We can skip this phase for now. 


### Phase 3:

The end to end orchestration. For now we can skip this phase.


## Features

The final deliverable will allow the following:

- User gives the command to start the roaster to the agent
  - Heat 100%
- Agent keeps displaying current temperature
- User then adds the beans to roaster when the machine is heated
- Agent detects roast has started and uses the tools to observe the Key roast metrics
  - Agent evaluates the metrics and makes decision to alter roast process by controlling the machine.
  - When goal is reached (development time 15%-20% and bean temperature < 200 degrees celsius) roast is completed and beans are ejected
- We will also have a feature to export roast data for future evaluation. 