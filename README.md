# Self-Correcting Voice Agents

An AI-automated testing platform for voice agents that can self-correct their scripts based on testing results.

## Overview

The Self-Correcting Voice Agent System is a platform designed to automatically test and improve voice agent scripts through an iterative process. The system focuses on debt collection voice agents but can be adapted for other use cases.

Key features:
- Generate diverse loan defaulter personas for realistic testing
- Simulate conversations between the agent and these personas
- Evaluate performance using key metrics like repetition rate and negotiation effectiveness
- Automatically improve agent scripts based on testing results
- Iterate until quality thresholds are met

![System Workflow](https://mermaid.ink/img/pako:eNp1UstOwzAQ_BVrT0SKlFKEeooqVXAoEnABiZMVbLO4tmNHtotKlH-37YZHEZzW3p2Z9c5uBw1tChnkh4oeN8qRFtaRZRw9lYoK9NKxEsxGslFOG5JlrUHSM9bGTBg3WuvKGTI-LnkutG_2eXYZBgVX6kk2rGVWpbJ8q5-ZDYgw-tITnvmf3eT5aDxvMVnfgMZMCxaLBpkO0lryRhZk9EIYwHXNgHhDm4jf4XTWn8fTCafJJ7zRc2OYM2pzS_JZGY-iFKrClhlHAXWFvnEH7chqI_cWoRPh-dL3-Ci4EYUvsYbSd0GaLvDTH0KFkHWUJIzrRMZ5Tm-FsyhtpO1CDcfYl1xSLdkR-thdm6Tpzfwm3I4Fq70VvRGb_KVrlBUGtCKvfVZNr_MZcgg6VVq4OwehYM4hb-hZ-AZyP2zRPXSKtR1-tYACg1yQM1yC2OMKcr-5Aw49lP4V_QEp-72V)

## Features

- **Persona Generator**: Creates diverse loan defaulter personalities for testing
- **Automated Testing Framework**: Tests voice agents against generated personas
- **Performance Metrics**: Tracks key metrics like repetition rate and negotiation effectiveness
- **Self-Correction System**: Automatically improves agent scripts based on test results
- **Iteration Pipeline**: Continuously tests and improves until quality thresholds are met
- **Web Interface**: Visualize and control the testing and improvement process

## Project Structure

- `src/`: Core source code
  - `personas/`: Persona generation models
  - `testing/`: Testing framework
  - `metrics/`: Performance metrics calculation
  - `agent/`: Voice agent implementation
  - `correction/`: Self-correction system
- `config/`: Configuration files
- `data/`: Sample data and testing results
- `app/`: Web interface for testing and monitoring

## Getting Started

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Set up environment variables:
```
# Create a .env file with your OpenAI API key
OPENAI_API_KEY=your_openai_api_key
```

3. Run the application:
```
python run_app.py
```

## Web Interface

The web interface is available at http://localhost:8501 when running locally.

The interface provides:
- Test execution with configurable parameters
- Visualization of test results and metrics
- Script improvement based on feedback
- History tracking of improvements
- Detailed conversation logs

## Core Components

### 1. Persona Generator

The persona generator creates diverse and realistic personas of loan defaulters for testing:

```python
# Generate personas with different financial situations and communication styles
personas = persona_generator.generate_personas(count=5, use_api=True)
```

Each persona includes:
- Personal details (name, age, occupation)
- Financial information (income, debt amount)
- Reasons for defaulting
- Communication and negotiation style
- Objections they might raise

### 2. Debt Collection Agent

The agent component manages the script that guides the debt collection conversation:

```python
# Load the base script
script = debt_collection_agent.load_base_script()
```

The script is organized into sections, each with:
- Content for the agent to speak
- Decision points based on customer responses
- Transitions to other script sections

### 3. Conversation Simulator

The simulator conducts realistic conversations between the agent and customer personas:

```python
# Simulate a conversation
conversation = conversation_simulator.simulate_conversation(
    agent_script=script, 
    customer_persona=persona
)
```

### 4. Performance Evaluator

The evaluator analyzes conversations and provides quantitative metrics:

```python
# Evaluate conversations
metrics = performance_evaluator.evaluate_conversations(conversations)

# Generate improvement feedback
feedback = performance_evaluator.generate_improvement_feedback(conversations, metrics)
```

Key metrics include:
- Repetition rate (lower is better)
- Negotiation effectiveness (higher is better)
- Resolution rate (higher is better)
- Compliance score (higher is better)

### 5. Script Improver

The script improver automatically enhances the script based on testing feedback:

```python
# Improve the script
improved_script = script_improver.improve_script(current_script, feedback)
```

Improvements include:
- Updating existing sections to address issues
- Adding new sections to handle missing scenarios
- Refining language for better customer engagement

## How it Works

The system follows an iterative improvement cycle:

1. Start with a base debt collection script
2. Generate test personas with different characteristics
3. Simulate conversations between the agent and these personas
4. Evaluate the script's performance using metrics
5. Generate improvement suggestions based on the evaluation
6. Automatically improve the script based on these suggestions
7. Repeat steps 2-6 until quality thresholds are met

## For More Information

See the [GUIDE.md](GUIDE.md) file for detailed usage instructions and extended examples.

## License

This project is open-source and available under the MIT License. 