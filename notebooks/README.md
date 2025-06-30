# Notebooks Directory

This directory contains Jupyter notebooks for agent development and exploration:

- **01_basic_agent_example.ipynb** - Complete getting started guide with agent creation, conversation management, and interaction examples

## 🚀 Getting Started

The notebook provides step-by-step examples of:
- Setting up the agent infrastructure
- Creating different types of agents
- Starting conversations and sending messages
- Working with the agent service layer

## 🛠️ Prerequisites

Before using the notebooks:
1. Ensure you have set up your environment (see [../SETUP.md](../SETUP.md))
2. Set your `OPENAI_API_KEY` environment variable
3. Install the Jupyter kernel: `poetry run python -m ipykernel install --user --name agent-template`

## 📖 Usage

### VS Code
1. Open the notebook in VS Code
2. Select the `agent-template` kernel when prompted
3. Run cells sequentially

### Jupyter Lab
```bash
poetry run jupyter lab
```

### Jupyter Notebook
```bash
poetry run jupyter notebook notebooks/01_basic_agent_example.ipynb
```

## 🎯 What You'll Learn

- How to create and configure agents with different roles
- Managing conversation lifecycles
- Sending messages and handling responses
- Working with the clean architecture layers
- Best practices for agent development

## 🔄 Adding Your Own Notebooks

When creating new notebooks:
1. Follow the naming convention: `XX_descriptive_name.ipynb`
2. Add proper setup cells for imports and environment
3. Include clear markdown explanations
4. Test all code examples before committing
5. Update this README to include your new notebook

Perfect for:
- Rapid prototyping of agent behaviors
- Testing new agent configurations
- Exploring LLM integration patterns
- Learning the agent template architecture
- Creating documentation with runnable examples 