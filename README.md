# ocragent

Official Python SDK for [OCR Agent](https://ocr.nxtwaveai.com) — extract structured data from documents using AI.

## Installation

```bash
pip install nxtwaveai-ocr
```

## Quick Start

```python
from ocragent import OcrAgent

client = OcrAgent(api_key="sk_...")

# List your agents
agents = client.agents.list()

# Extract a document
with open("invoice.pdf", "rb") as f:
    result = client.extract(agent_id=agents[0]["id"], file=f)

print(result["data"])
# {"invoice_number": "INV-001", "total_amount": 4250, "due_date": "2025-04-15"}
```

## API

### `OcrAgent(api_key, ...)`

| Parameter | Default | Description |
|---|---|---|
| `api_key` | required | Your API key (`sk_...`) |
| `base_url` | production URL | Override the API base URL |
| `max_retries` | `3` | Retries on 429/5xx |
| `timeout` | `30.0` | Request timeout (seconds) |

### `client.agents`

```python
# Manage existing agents
client.agents.list()
client.agents.get(agent_id)
client.agents.get_schema(agent_id)
client.agents.update_schema(agent_id, fields=[...])
client.agents.set_status(agent_id, "active" | "paused")
client.agents.delete(agent_id)
client.agents.results(agent_id, period="30d", page=1, limit=20)
client.agents.export_results(agent_id, format="csv")   # returns bytes
client.agents.stats(agent_id)

# Create a new agent (auto-confirms AI field suggestions)
with open("invoice.jpg", "rb") as f:
    agent = client.agents.create(f, doc_type_hint="invoice")
print(agent["agent_id"])

# Or use the 3-step wizard for more control:
with open("invoice.jpg", "rb") as f:
    session = client.agents.create_session(f, doc_type_hint="invoice")
status = client.agents.get_session(session["session_id"])
# status["questions"] has AI-suggested field names
answers = {q["key"]: q["suggested_value"] for q in status["questions"]}
result = client.agents.finalize_session(session["session_id"], answers)
print(result["agent_id"])
```

### `client.extract`

```python
# Single document
client.extract(agent_id, file, file_back=None, callback_url=None)

# Multiple documents
client.extract.batch(agent_id, files=[f1, f2, f3])

# Pre-upload an image
client.extract.upload_image(file)
```

### `client.jobs`

```python
client.jobs.list(status=None, page=1, limit=20)
client.jobs.get(job_id)
client.jobs.result(job_id)
client.jobs.download(job_id, format="json")  # returns bytes
client.jobs.delete(job_id)
```

### Error Handling

```python
from ocragent.errors import OcrAgentError, AuthError, RateLimitError, PlanLimitError, AgentPausedError

try:
    result = client.extract.single(agent_id="...", file=f)
except AuthError:
    # 401 — invalid or expired API key
    print("Invalid API key")
except PlanLimitError as e:
    # 402/422 — monthly doc cap, agent slot limit, or key credit cap reached
    print("Plan limit reached:", e.message)
except AgentPausedError:
    # 422 — agent is paused
    print("Agent is paused — resume it first")
except RateLimitError as e:
    # 429 — too many requests
    print(f"Rate limited. Retry after {e.retry_after}s")
except OcrAgentError as e:
    print(e.status, e.code, e.message)
```

### Context manager

```python
with OcrAgent(api_key="sk_...") as client:
    agents = client.agents.list()
```

## License

MIT © [NxtwaveAI](https://nxtwaveai.com)
