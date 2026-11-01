# LangGraph Incident Triage: Starter Repo

Starting code for the NextWork Project **Build a Multi-Agent Incident Triage System with LangGraph**.

`app.py` is the finished single-analyst incident workflow from the NextWork Project [Build a Resumable LangGraph Workflow](https://nextwork.ai/projects/f94db9b2-1157-404b-a559-83e8752f2f86). Its workflow is preserved. One model call analyzes an incident, a deterministic policy decides whether a human must approve, `interrupt()` pauses the run, and `SqliteSaver` lets a new process resume it. You don't need to have done that Project first: this repo gives you the same starting point either way.

In this Project you turn that single analyst into a team: a router, specialist agents that investigate in parallel, recovery when one of them crashes, and an approval gate for each team that owns a fix. The setup code for the specialists and the status page is already here, so you spend your time on the agents and the graph.

## What's in the repo

| Path | What it is |
|---|---|
| `app.py` | The starting workflow: `start` and `resume` commands, one analyst, one approval gate |
| `specialists.py` | Setup code for the specialist agents: the shared model connection, a fixture loader, and one tool each for logs, deploys, and metrics. You add the agents themselves in the Project |
| `status_page.py` | The web page for the Secret Mission: HTML, styling, and a small local server. You write the part that reads an incident's saved state |
| `pyproject.toml`, `uv.lock`, `.python-version` | Project dependencies, locked versions, and Python 3.11 selection |
| `data/alerts.json` | Two alerts to triage: `INC-2041` (checkout errors) and `INC-2042` (search latency) |
| `data/logs.jsonl` | Application logs from the services involved, one JSON object per line |
| `data/deploys.json` | Recent deploys, with the service, owning team, time, and change |
| `data/metrics.json` | Metric time series per service |
| `data/services.json` | Service catalog: owning team, on-call handle, and dependencies |

The data is made up and small on purpose. Your agents read it through tools, so runs are cheap and the answers can be checked.

## Set up

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and [Ollama](https://ollama.com/download). uv uses the project's Python 3.11 selection and downloads Python if needed. Keep Ollama running (use `ollama serve` if needed), then sign in for the cloud model:

```bash
ollama signin
```

From this repository, sync the locked dependencies and copy the environment template. uv creates the virtual environment automatically.

Windows PowerShell:

```powershell
uv sync --locked
Copy-Item .env.example .env
```

macOS / Linux:

```bash
uv sync --locked
cp .env.example .env
```

The ignored `.env` defaults to the signed-in local Ollama server:

```dotenv
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=beam:cloud
LLM_API_KEY=ollama
```

`ollama` is a dummy key for this local endpoint; cloud authentication comes from `ollama signin`. The cloud model needs an internet connection and available account access.

To switch to another OpenAI-compatible provider, change these same three variables to its base URL, model, and API key. The model must support tool calling for incident analysis and specialist tools. Existing environment variables override `.env`. Keep real credentials out of version control.

## Check that it runs

```bash
uv run --locked python app.py start --thread smoke-001 --incident "Production checkout API returns HTTP 500 for 1 in 6 requests after a config deploy."
uv run --locked python app.py resume --thread smoke-001 --decision approve
```

The first command should print `WORKFLOW PAUSED` and an approval payload. The second resumes the saved workflow and publishes `runbooks/smoke-001.md`. Checkpoints are stored in `incident_checkpoints.db` in the current directory. The `LangChainBetaWarning` about the v3 streaming protocol is expected.

Run the offline tests without a model connection:

```bash
uv run --locked python -m unittest discover -s tests -v
```

## Branches

- `main` is the starting point for the Project. Clone it and follow the Project's steps from here.
- `solution` is the finished build. Use it to check your work if you get stuck; follow that branch's setup and test instructions.
