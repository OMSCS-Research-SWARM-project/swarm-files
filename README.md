# Malware Analysis Agent (SWARM)

This repository contains the student-facing CrewAI package lives in `src/malware_analysis_agent/`.



## Installation

Ensure you have Python >=3.10 <3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling.

First, if you haven't already, install uv:
```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

```bash
uv sync
```


## Customizing the Agent

Students may customize only the `role`, `goal`, and `backstory` fields for the existing agents in `src/malware_analysis_agent/config/agents.yaml`. The YAML validator rejects extra agents and extra fields such as `verbose`, `tools`, `llm`, or `allow_delegation`.

CrewAI will populate a RAG db based on the .txt knowledge files in the `knowledge/` directory. It will only pick up files with .txt extensions.

Students **must not edit** the following:
- `src/malware_analysis_agent/config/tasks.yaml`
- Any Python source files (e.g., `crew.py`, `main.py`, `schema.py`, `preamble.py`)
- The internal preamble in `preamble.py`

### Setup

1. Copy the `.env.[azure|openai].example` file to `.env`.
2. Add the relevant api keys, models, and endpoint variables as per openai or azure configuration.
3. Add your knowledge files (plain text `.txt`) under the `knowledge/` directory.

### LLM Output Token Parameter

Different models require different parameter names for the output token limit. Use the `LLM_OUTPUT_TOKEN_PARAM` environment variable to specify the correct one for your provider.

- Use `max_completion_tokens` for Azure/OpenAI GPT-5 or o-series style deployments.
- Use `max_tokens` for Anthropic Claude and many older OpenAI-compatible/Gemini-through-LiteLLM models.

If `LLM_OUTPUT_TOKEN_PARAM` is missing or invalid, the agent will fail with a clear error explaining the allowed values.


### Azure / Foundry LLM with OpenAI Embeddings

This project can use an Azure AI Foundry / Azure OpenAI deployment for the main CrewAI LLM while continuing to use regular OpenAI for embeddings.

Use this `.env` shape for the tested Azure + OpenAI embeddings setup:

```env
# Main CrewAI LLM - Azure AI Foundry / Azure OpenAI
MODEL=azure/<your-azure-deployment-name>
LLM_OUTPUT_TOKEN_PARAM=max_completion_tokens
AZURE_API_KEY=<your-azure-api-key>
AZURE_API_BASE=https://<your-azure-endpoint>/
AZURE_API_VERSION=<your-azure-api-version>

# OpenAI embeddings
OPENAI_API_KEY=<your-openai-api-key>
EMBEDDER_PROVIDER=openai
EMBEDDER_MODEL=text-embedding-3-small
CHROMA_OPENAI_API_KEY=<your-openai-api-key>
```

Example tested shape:

```env
# Main CrewAI LLM - Azure AI Foundry / Azure OpenAI
MODEL=azure/PUT_ENDPOINT_INFO_HERE-gpt-5-mini
AZURE_API_KEY=REDACTED
AZURE_API_BASE=https://eastus2.api.cognitive.microsoft.com/
AZURE_API_VERSION=2025-04-01-preview

# OpenAI embeddings
OPENAI_API_KEY=sk-proj-REDACTED
EMBEDDER_PROVIDER=openai
EMBEDDER_MODEL=text-embedding-3-small
CHROMA_OPENAI_API_KEY=sk-proj-REDACTED
```


## Running the Project

### 1. Run the Agent Locally

To run the student AI agent against a specific events file, use the following command structure from the root folder:

```bash
uv run run_crew -- --events <path_to_events.json> --output <path_to_output.json>
```

*Note: The `--` is required to pass arguments through `uv` to the project entrypoint.*

#### Local Knowledge Storage and Fingerprinting

This project uses a local fingerprint to manage CrewAI's default knowledge storage. On each local run, the agent computes a hash of your `knowledge/**/*.txt` files and your embedding configuration.

- **Reusing Storage**: If the fingerprint matches the previous run, the agent reuses existing local storage to avoid redundant embedding costs.
- **Resetting Storage**: If the fingerprint changes (e.g., you added/edited knowledge files or changed your embedding model in `.env`), the agent automatically resets CrewAI's local knowledge storage before re-embedding.
- **Fingerprint File**: The current fingerprint is stored in `.knowledge.hash`. You should not edit this file manually. It is ignored by Git.


#### A. Run against Student Honeypot dataset
```bash
uv run run_crew -- \
  --events datasets/lab_run_mirai/events.json \
  --output tmp/lab_run_mirai_agent_output.json
```

#### B. Run against Student Realistic Sample dataset
```bash
uv run run_crew -- \
  --events datasets/realistic_sample/events.json \
  --output tmp/realistic_sample_agent_output.json
```

### 2. Verify Local Results

After running the agent, you can verify its accuracy against the labeled student datasets using the diagnostic script:

#### Verify Honeypot results
```bash
uv run python datasets/check_agent_output.py \
  --expected datasets/lab_run_mirai/expected_classifications.json \
  --agent-output tmp/lab_run_mirai_agent_output.json \
  --events datasets/lab_run_mirai/events.json
```

#### Verify Realistic Sample results
```bash
uv run python check_agent_output.py \
  --expected datasets/realistic_sample/expected_classifications.json \
  --agent-output tmp/realistic_sample_agent_output.json \
  --events datasets/realistic_sample/events.json
```

## Training the Agent Locally
Training is optional, but highly encouraged.
Training lets you provide interactive feedback to CrewAI for one selected public event. The result is written to a pickle file, normally named `trained_agents_data.pkl`.
This can be submitted to gradescope to enhance your agent's performance based on human labeling.

During later normal runs, CrewAI can use that file as additional prompt guidance.
Use this form:

```bash
uv run train <n_iterations> trained_agents_data.pkl -- --events <events.json> --event-id <id>
```

Example:

```bash
uv run train 3 trained_agents_data.pkl -- --events datasets/lab_run_mirai/events.json --event-id 12
```

Only event-based training is supported. Scenario-based training is intentionally unsupported.

## CrewAI Training File

CrewAI automatically loads trained suggestions from a file named `trained_agents_data.pkl` in the current working directory.

For this project, run commands from the repository root. If you want the agent to use trained CrewAI guidance, place the file here:

