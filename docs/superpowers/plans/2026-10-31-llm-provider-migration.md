# OpenAI-Compatible Incident Triage Migration Implementation Plan

> For agentic workers: use superpowers:subagent-driven-development. Implement each task, review it, then move to the next.

**Goal:** Run the existing starter workflow with signed-in Ollama `beam:cloud`, while changing providers through `.env` only.

**Architecture:** One `llm.py` factory returns `ChatOpenAI`. `app.py` and `specialists.py` use it. The graph, tools, policy, checkpointing, and incident data stay intact.

**Tech Stack:** Python 3.12, LangChain, LangGraph, langchain-openai, python-dotenv, unittest.

**Spec:** Approved user requirements in this chat, 2026-10-31.

## Global Constraints

- Starter repo only; the future multi-agent build is out of scope.
- Use `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` from `.env`.
- Initial local-login setup: `http://localhost:11434/v1`, `beam:cloud`, dummy key `ollama`.
- Keep all provider choices out of agent code.
- Preserve graph routes, tools, structured output, SQLite checkpointing, approval, and datasets.
- No real API keys in source or commits. Minimal dependencies and edits.

## Review Focus

- Missing configuration fails clearly before a model request.
- Shell environment values should take precedence over `.env` values.
- Local Ollama accepts the dummy key and routes cloud requests using its own sign-in.
- Structured analysis retains the dict keys used by policy and runbook code.
- Unsupported provider/model capabilities fail visibly; no silent fallback.

### Task 1: Shared model factory

**Files:** Create `llm.py`; modify `requirements.txt`; create `.env.example`; create `tests/test_llm.py`.

**Interface:** `build_model()` returns a `ChatOpenAI` configured from the three `LLM_*` values.

- [ ] Add a failing stdlib `unittest` for environment precedence and missing values.
- [ ] Implement the smallest `build_model()` with `load_dotenv()` and clear configuration errors.
- [ ] Replace `langchain-google-genai` with compatible pinned `langchain-openai`; add direct `python-dotenv` dependency.
- [ ] Add `.env.example` with the agreed Ollama values and a comment that the dummy key applies only to local Ollama.
- [ ] Run the focused tests and compilation; commit the task.

### Task 2: Migrate both consumers and preserve behavior

**Files:** Modify `app.py`, `specialists.py`; create `tests/test_workflow.py`.

**Interface:** Both model builders call `llm.build_model()`; `build_analyst()` still yields a dict matching `ANALYSIS_SCHEMA`.

- [ ] Add a failing offline workflow test using a stub analyst for low-risk publish and high-risk pause, approve, and reject paths.
- [ ] Replace the two Vertex constructors and Google-specific checks with the shared factory.
- [ ] Select one supported `with_structured_output` method for Ollama's OpenAI-compatible endpoint; preserve schema and output shape.
- [ ] Run focused tests and compilation; commit the task.

### Task 3: Setup docs and live verification

**Files:** Modify `README.md`; adjust only migration-related files if live checks reveal a defect.

- [ ] Document Windows and Unix setup, `ollama signin`, `.env` copy, Ollama local URL, and switching provider through the three variables.
- [ ] Remove obsolete Cloud Shell, Gemini, and Vertex setup/cost text; preserve starter-project scope.
- [ ] Run all offline tests.
- [ ] With the signed-in local Ollama server, check model response, structured output, tool call, and `app.py` start/resume behavior. Record exact results or an explicit blocker.
- [ ] Review git diff for secret exposure and unrelated changes; commit the task.
