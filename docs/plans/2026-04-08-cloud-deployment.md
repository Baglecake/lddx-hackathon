# LDDx Cloud Deployment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy the full LDDx app (pipeline + collaborative synonym review) to Railway + Supabase with a custom domain.

**Architecture:** NiceGUI app runs on Railway (Docker). Inference handled by RunPod Serverless (vLLM with Qwen 2.5 or similar). Synonym review backed by Supabase Postgres with Realtime for live collaboration. Supabase Auth for reviewer identity. Custom domain via Squarespace DNS.

**Tech Stack:** NiceGUI, Railway (Docker), Supabase (Postgres + Realtime + Auth), RunPod Serverless (vLLM), Python 3.12

---

## Phase 1: Make the App Cloud-Ready (local changes, no accounts needed yet)

### Task 1: Environment Variable Configuration

**Files:**
- Modify: `app/main.py` (startup config)
- Create: `.env.example`

**Step 1: Add environment variable support to app startup**

In `app/main.py`, update the `main()` function:

```python
def main():
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '127.0.0.1')

    ui.run(
        title='Local-DDx',
        port=port,
        host=host,
        dark=True,
        reload=False,
        favicon='...',
    )
```

**Step 2: Create `.env.example`**

```
# App
PORT=8080
HOST=0.0.0.0

# Inference (RunPod Serverless)
INFERENCE_BACKEND=mlx          # mlx | ollama | runpod
INFERENCE_URL=http://localhost:11434
RUNPOD_API_KEY=
RUNPOD_ENDPOINT_ID=

# Supabase (for synonym review)
SUPABASE_URL=
SUPABASE_ANON_KEY=
```

**Step 3: Verify locally**

```bash
PORT=8080 HOST=127.0.0.1 python app/main.py
```
Expected: App starts normally on localhost:8080.

**Step 4: Commit**

```bash
git add app/main.py .env.example
git commit -m "feat: add environment variable config for cloud deployment"
```

---

### Task 2: RunPod Serverless Backend

**Files:**
- Modify: `pipeline/Modules/inference_backends.py`
- Modify: `app/main.py` (add RunPod as third backend option)

**Step 1: Add RunPodBackend class**

In `inference_backends.py`, add a new backend that calls RunPod's OpenAI-compatible vLLM endpoint:

```python
class RunPodBackend(InferenceBackend):
    """RunPod Serverless vLLM backend for cloud deployment."""

    def __init__(self, api_key: str = None, endpoint_id: str = None,
                 model_name: str = "default", **kwargs):
        self.api_key = api_key or os.environ.get('RUNPOD_API_KEY', '')
        self.endpoint_id = endpoint_id or os.environ.get('RUNPOD_ENDPOINT_ID', '')
        self.base_url = f"https://api.runpod.ai/v2/{self.endpoint_id}/openai/v1"
        self.model_name = model_name
        self.current_model = None

    def is_available(self) -> bool:
        return bool(self.api_key and self.endpoint_id)

    def load(self, model_name: str, **kwargs) -> bool:
        self.current_model = model_name
        return True

    def generate(self, prompt: str, config: SamplingConfig) -> str:
        return self.generate_chat(
            [{"role": "user", "content": prompt}], config
        )

    def generate_chat(self, messages, config: SamplingConfig) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.current_model or self.model_name,
            "messages": messages,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "max_tokens": config.max_tokens,
        }
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers, json=payload, timeout=300
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        return f"Error: {resp.status_code} {resp.text[:200]}"

    def generate_chat_stream(self, messages, config, token_callback=None):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.current_model or self.model_name,
            "messages": messages,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "max_tokens": config.max_tokens,
            "stream": True,
        }
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers, json=payload, timeout=300, stream=True,
        )
        chunks = []
        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode().removeprefix("data: ").strip()
            if line == "[DONE]":
                break
            data = json.loads(line)
            delta = data.get("choices", [{}])[0].get("delta", {})
            token = delta.get("content", "")
            if token:
                chunks.append(token)
                if token_callback:
                    token_callback(token)
        return "".join(chunks)

    def unload(self) -> None:
        self.current_model = None

    def get_info(self) -> Dict[str, Any]:
        return {"backend": "runpod", "endpoint_id": self.endpoint_id,
                "available": self.is_available()}
```

**Step 2: Wire into factory**

```python
elif backend_type == "runpod":
    return RunPodBackend(**kwargs)
```

**Step 3: Add RunPod toggle to app UI**

In `app/main.py`, update the backend toggle to include RunPod:

```python
backend_toggle = ui.toggle(
    {'ollama': 'Ollama', 'mlx': 'MLX (Apple Silicon)', 'runpod': 'RunPod (Cloud)'},
    value='ollama',
    on_change=on_backend_change,
)
```

And update `initialize_system` to handle RunPod config from env vars.

**Step 4: Test locally with RunPod** (after RunPod setup in Phase 2)

**Step 5: Commit**

```bash
git add pipeline/Modules/inference_backends.py app/main.py
git commit -m "feat: add RunPod serverless inference backend"
```

---

### Task 3: Dockerfile

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`

**Step 1: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Railway provides PORT env var
EXPOSE 8080

CMD ["python", "app/main.py"]
```

**Step 2: Create .dockerignore**

```
.git
.env
exports/
__pycache__
*.pyc
*.egg-info
.DS_Store
venv/
.venv/
docs/plans/
```

**Step 3: Test locally**

```bash
docker build -t lddx .
docker run -p 8080:8080 -e HOST=0.0.0.0 -e PORT=8080 -e INFERENCE_BACKEND=runpod lddx
```

**Step 4: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "feat: add Dockerfile for Railway deployment"
```

---

## Phase 2: Account Setup & Infrastructure (step-by-step walkthrough)

### Task 4: Supabase Project Setup

> **NOTE:** This is a walkthrough — no code changes, just account setup.

**Step 1: Create Supabase account**
- Go to https://supabase.com and sign up (GitHub auth is easiest)
- Click "New Project"
- Name: `lddx-hackathon`
- Region: pick closest to your users (US East recommended)
- Set a database password (save it somewhere safe)
- Wait for project to provision (~2 min)

**Step 2: Get your keys**
- Go to Settings > API
- Copy: `Project URL` (this is `SUPABASE_URL`)
- Copy: `anon public` key (this is `SUPABASE_ANON_KEY`)
- Save both — you'll need them for Railway env vars

**Step 3: Create database tables**

Go to SQL Editor in Supabase dashboard, paste and run:

```sql
-- Reviewers
CREATE TABLE reviewers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Section 1: Known failure verdicts
CREATE TABLE failure_verdicts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    reviewer_id UUID REFERENCES reviewers(id),
    case_id TEXT NOT NULL,
    ground_truth TEXT NOT NULL,
    pipeline_output TEXT NOT NULL,
    verdict TEXT CHECK (verdict IN ('match', 'not_match', 'unsure')),
    comment TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(reviewer_id, case_id, ground_truth)
);

-- Section 2: Synonym review verdicts
CREATE TABLE synonym_verdicts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    reviewer_id UUID REFERENCES reviewers(id),
    category TEXT NOT NULL,
    canonical_term TEXT NOT NULL,
    alias_to_add TEXT,
    flag_issue TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(reviewer_id, canonical_term)
);

-- Section 3: Hierarchy review verdicts
CREATE TABLE hierarchy_verdicts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    reviewer_id UUID REFERENCES reviewers(id),
    supertype TEXT NOT NULL,
    subtype_to_add TEXT,
    flag_issue TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(reviewer_id, supertype)
);

-- Enable Realtime on all tables
ALTER PUBLICATION supabase_realtime ADD TABLE failure_verdicts;
ALTER PUBLICATION supabase_realtime ADD TABLE synonym_verdicts;
ALTER PUBLICATION supabase_realtime ADD TABLE hierarchy_verdicts;

-- Row Level Security (allow authenticated + anon for now)
ALTER TABLE reviewers ENABLE ROW LEVEL SECURITY;
ALTER TABLE failure_verdicts ENABLE ROW LEVEL SECURITY;
ALTER TABLE synonym_verdicts ENABLE ROW LEVEL SECURITY;
ALTER TABLE hierarchy_verdicts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all" ON reviewers FOR ALL USING (true);
CREATE POLICY "Allow all" ON failure_verdicts FOR ALL USING (true);
CREATE POLICY "Allow all" ON synonym_verdicts FOR ALL USING (true);
CREATE POLICY "Allow all" ON hierarchy_verdicts FOR ALL USING (true);
```

**Step 4: Verify**
- Go to Table Editor — you should see 4 tables
- Go to Database > Replication — tables should show as enabled

---

### Task 5: RunPod Serverless Setup

> **NOTE:** Walkthrough for setting up a vLLM serverless endpoint.

**Step 1: Create RunPod account**
- Go to https://runpod.io and sign up
- Add billing (you'll need credits for GPU time)

**Step 2: Create a Serverless Endpoint**
- Go to Serverless > Endpoints > New Endpoint
- Template: choose "vLLM" (RunPod's official vLLM worker)
- Model: `Qwen/Qwen2.5-32B-Instruct` (or a smaller model to start — `Qwen/Qwen2.5-7B-Instruct` is cheaper for testing)
- GPU: A100 80GB (for 32B) or A40 (for 7B)
- Min Workers: 0 (scale to zero when idle — saves money)
- Max Workers: 1 (for hackathon demo)
- Idle Timeout: 5 min
- Click Deploy

**Step 3: Get your credentials**
- Copy the Endpoint ID from the endpoint page
- Go to Settings > API Keys > Create API Key
- Copy the API key

**Step 4: Test the endpoint**

```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/openai/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen2.5-7B-Instruct", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 50}'
```

Expected: JSON response with a completion.

> **Cost note:** RunPod serverless charges per second of GPU time. With min workers = 0, you only pay when the endpoint is active. Cold starts take ~30-60s. Budget ~$0.50-1.00/hr for A100.

---

### Task 6: Railway Project Setup

> **NOTE:** Walkthrough for deploying to Railway.

**Step 1: Create Railway account**
- Go to https://railway.com and sign up (GitHub auth recommended)
- Link your GitHub account

**Step 2: Create a new project**
- Click "New Project"
- Choose "Deploy from GitHub Repo"
- Select your `lddx-hackathon` repo
- Railway will detect the Dockerfile and start building

**Step 3: Add environment variables**

In the Railway dashboard, go to your service > Variables tab. Add:

```
HOST=0.0.0.0
INFERENCE_BACKEND=runpod
RUNPOD_API_KEY=<your key from Task 5>
RUNPOD_ENDPOINT_ID=<your endpoint ID from Task 5>
SUPABASE_URL=<your URL from Task 4>
SUPABASE_ANON_KEY=<your key from Task 4>
```

(Railway provides `PORT` automatically — don't add it manually)

**Step 4: Configure networking**
- Go to service Settings > Networking
- Click "Generate Domain" — you'll get a `*.up.railway.app` URL
- Test: visit the URL, you should see the LDDx app

**Step 5: Verify the deployment**
- App loads in browser
- Backend toggle shows "RunPod (Cloud)"
- Select RunPod, pick a model, run a case
- Check Railway logs for any errors

---

## Phase 3: Collaborative Synonym Review (Supabase integration)

### Task 7: Add Supabase Client to App

**Files:**
- Modify: `requirements.txt`
- Create: `app/supabase_client.py`

**Step 1: Add dependency**

Add to `requirements.txt`:
```
supabase>=2.0
```

**Step 2: Create Supabase client module**

```python
# app/supabase_client.py
import os
from supabase import create_client

def get_supabase():
    url = os.environ.get('SUPABASE_URL', '')
    key = os.environ.get('SUPABASE_ANON_KEY', '')
    if not url or not key:
        return None
    return create_client(url, key)
```

**Step 3: Commit**

```bash
git add requirements.txt app/supabase_client.py
git commit -m "feat: add Supabase client for synonym review backend"
```

---

### Task 8: Build Collaborative Synonym Review Page

**Files:**
- Modify: `app/main.py` (add new route `/review`)

**Step 1: Add `/review` page to NiceGUI**

Add a new page that:
- Prompts for reviewer name on first visit (stored in session)
- Loads synonym data from the evaluator's dictionary
- Renders the three sections with interactive form elements
- Saves verdicts to Supabase on change
- Shows live updates from other reviewers via Supabase Realtime

This is the largest single task — the page structure mirrors the HTML review form but with NiceGUI components backed by Supabase persistence.

Key NiceGUI components:
- `ui.select` for verdicts (match/not match/unsure)
- `ui.input` for comments and new aliases
- `ui.badge` showing how many reviewers have completed each row
- `ui.notify` when another reviewer submits a verdict

**Step 2: Test locally**

```bash
SUPABASE_URL=<url> SUPABASE_ANON_KEY=<key> python app/main.py
```

Visit `http://localhost:8080/review` — should show the form with live persistence.

**Step 3: Commit and push**

```bash
git add app/main.py
git commit -m "feat: add collaborative synonym review page with Supabase"
git push
```

Railway auto-deploys on push.

---

## Phase 4: Custom Domain

### Task 9: Connect Squarespace Domain to Railway

> **NOTE:** Walkthrough for DNS setup.

**Step 1: In Railway**
- Go to your service > Settings > Networking > Custom Domain
- Click "Add Custom Domain"
- Enter your domain (e.g., `lddx.yourdomain.com` or just `yourdomain.com`)
- Railway will show you a CNAME record to add

**Step 2: In Squarespace**
- Go to Squarespace > Domains > your domain > DNS Settings
- Add a CNAME record:
  - Host: `lddx` (or `@` for root domain)
  - Value: the `*.up.railway.app` value Railway gave you
- If using root domain, you may need an A record instead — Railway docs will specify

**Step 3: Wait for DNS propagation** (~5-30 min)

**Step 4: Verify**
- Visit your custom domain
- Should show the LDDx app with HTTPS (Railway provides SSL automatically)

**Step 5: Update Supabase CORS** (if needed)
- Go to Supabase > Settings > API > Additional Settings
- Add your custom domain to allowed origins

---

## Phase Summary

| Phase | Tasks | What you get |
|-------|-------|-------------|
| 1 | Tasks 1-3 | App is cloud-ready (env vars, RunPod backend, Dockerfile) |
| 2 | Tasks 4-6 | Accounts created, infrastructure provisioned |
| 3 | Tasks 7-8 | Collaborative synonym review with live persistence |
| 4 | Task 9 | Custom domain with HTTPS |

**Estimated time:**
- Phase 1: ~1 session (code changes)
- Phase 2: ~30 min (account setup, mostly clicking)
- Phase 3: ~1 session (Supabase integration)
- Phase 4: ~15 min (DNS setup)

---

## Pre-flight Checklist

Before starting, confirm you have:
- [ ] A GitHub account (for Railway)
- [ ] A credit card (for RunPod billing — small amounts for testing)
- [ ] Access to Squarespace DNS settings for your domain
- [ ] The repo pushed to GitHub (Railway deploys from there)
