# Self-Correcting Voice Agent System Guide

This guide will help you set up and use the Self-Correcting Voice Agent System.

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. (Optional) Create a `.env` file in the root directory with your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

Note: You can also enter your API key directly in the web interface if preferred.

## Running the System

There are two ways to run the system:

### Using the Web Interface

This is the recommended way to interact with the system as it provides visualizations and an easy-to-use interface.

```bash
python run_app.py
```

The web interface will be available at http://localhost:8501

### Using the Python API

For programmatic use or batch processing, you can use the system's Python API directly:

```python
from src.personas import persona_generator
from src.agent import debt_collection_agent
from src.testing import conversation_simulator
from src.metrics import performance_evaluator
from src.correction import script_improver

# Load the base script
script = debt_collection_agent.load_base_script()

# Generate test personas
personas = persona_generator.generate_personas(count=5)

# Simulate conversations
conversations = []
for persona in personas:
    conversation = conversation_simulator.simulate_conversation(
        agent_script=script,
        customer_persona=persona
    )
    conversations.append(conversation)

# Evaluate performance
metrics = performance_evaluator.evaluate_conversations(conversations)

# Generate improvement feedback
feedback = performance_evaluator.generate_improvement_feedback(conversations, metrics)

# Improve script
improved_script = script_improver.improve_script(script, feedback)
```

## System Components

The system consists of the following components:

1. **Persona Generator**: Creates diverse loan defaulter personalities for testing.
2. **Agent Script**: The debt collection script that guides the conversation flow.
3. **Conversation Simulator**: Simulates conversations between the agent and generated personas.
4. **Performance Evaluator**: Analyzes conversations and calculates performance metrics.
5. **Script Improver**: Automatically improves the script based on feedback.

## Performance Metrics

The system tracks the following key metrics:

- **Repetition Rate**: How often the agent repeats information unnecessarily (lower is better).
- **Negotiation Effectiveness**: How effectively the agent negotiates with customers (higher is better).
- **Resolution Rate**: How often conversations end with a clear resolution (higher is better).
- **Compliance Score**: How well the agent follows compliance guidelines (higher is better).

## Workflow

1. The system starts with a base debt collection script.
2. It generates test personas with different financial situations and communication styles.
3. It simulates conversations between the debt collection agent and these personas.
4. It evaluates the performance of the script using multiple metrics.
5. It generates improvement suggestions based on the evaluation.
6. It automatically improves the script based on these suggestions.
7. The process repeats until the script meets the desired quality thresholds.

## Extending the System

You can extend the system in various ways:

1. **Add New Sections**: Add new script sections by modifying the `debt_collection_agent.py` file.
2. **New Metrics**: Add new performance metrics in the `performance_evaluator.py` file.
3. **Voice Integration**: Add voice capabilities by integrating with speech-to-text and text-to-speech APIs.
4. **Custom Personas**: Create custom personas by adding them to the `_PREDEFINED_PERSONAS` list in `persona_generator.py`.

## Troubleshooting

- **API Key Issues**: If you see errors related to the OpenAI API, check that your API key is valid.
- **Installation Issues**: Make sure all requirements are installed correctly.
- **Streamlit Issues**: If the web interface doesn't start, check that Streamlit is installed correctly.

For more help, please open an issue on the GitHub repository. 