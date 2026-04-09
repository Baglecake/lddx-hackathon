#!/usr/bin/env python3
"""
Local-DDx — NiceGUI Web Interface
Multi-agent collaborative differential diagnosis with Social Chain of Thought.
"""

import asyncio
import os
import sys
import threading
import queue
from datetime import datetime
from typing import Optional, Dict, Any, List

import requests
from nicegui import ui, app

# ---------------------------------------------------------------------------
# Pipeline imports
# ---------------------------------------------------------------------------
PIPELINE_MODULES = os.path.join(os.path.dirname(__file__), '..', 'pipeline', 'Modules')
sys.path.insert(0, PIPELINE_MODULES)

from ddx_runner import DDxSystem
from ddx_core import ModelConfig, OllamaModelManager, DynamicAgentGenerator
from ddx_sliding_context import TranscriptManager
from inference_backends import MLXBackend, RunPodBackend

# ---------------------------------------------------------------------------
# Per-session state (keyed by user ID — no globals shared across users)
# ---------------------------------------------------------------------------

_sessions: Dict[str, Dict[str, Any]] = {}
_sessions_lock = threading.Lock()


def _get_session(user_id: str) -> Dict[str, Any]:
    """Get or create a per-user session store."""
    with _sessions_lock:
        if user_id not in _sessions:
            _sessions[user_id] = {
                'ddx_system': None,
                'last_result': None,
                'current_models': {},
            }
        return _sessions[user_id]
mlx_backend: Optional[MLXBackend] = None

# ---------------------------------------------------------------------------
# Ollama helpers
# ---------------------------------------------------------------------------

def get_ollama_models(base_url: str = "http://localhost:11434") -> List[str]:
    """Query Ollama for available models."""
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=5)
        if resp.status_code == 200:
            return sorted(m['name'] for m in resp.json().get('models', []))
    except Exception:
        pass
    return ["qwen2.5:32b-instruct-q8_0", "llama3.1:8b", "mistral-nemo:12b"]


def get_mlx_models() -> List[str]:
    """Query locally cached MLX models."""
    try:
        backend = MLXBackend()
        if backend.is_available():
            return backend.get_available_models()
    except Exception:
        pass
    return []


def get_runpod_models() -> List[str]:
    """Query RunPod endpoint for available models."""
    try:
        backend = RunPodBackend()
        if backend.is_available():
            return backend.get_available_models()
    except Exception:
        pass
    return []


def prioritized_models(models: List[str]) -> List[str]:
    """Put common models at the top of the list."""
    priority = ["qwen2.5:32b-instruct-q8_0", "mistral-nemo:12b", "llama3.1:8b"]
    top = [p for p in priority if p in models]
    rest = [m for m in models if m not in top]
    return top + rest

# ---------------------------------------------------------------------------
# System initialization
# ---------------------------------------------------------------------------

def initialize_system(user_id: str, conservative: str, innovative: str, url: str, backend: str = "ollama") -> str:
    """Initialize or reinitialize the DDx system for a specific user session."""
    sess = _get_session(user_id)

    cache_key = {
        'conservative': conservative, 'innovative': innovative,
        'url': url, 'backend': backend,
    }
    if sess['ddx_system'] and sess['current_models'] == cache_key:
        return "ready"

    system = DDxSystem()

    configs = {
        'conservative_model': ModelConfig(
            name='Conservative', model_name=conservative,
            temperature=0.3, top_p=0.7, max_tokens=1024, role='conservative',
        ),
        'innovative_model': ModelConfig(
            name='Innovative', model_name=innovative,
            temperature=0.8, top_p=0.95, max_tokens=1024, role='innovative',
        ),
    }

    backend_kwargs = {}
    if backend == "ollama":
        backend_kwargs['base_url'] = url

    system.model_manager = OllamaModelManager(
        configs, backend_type=backend, **backend_kwargs
    )

    if not system.model_manager.initialize():
        return "error"

    for model_id in system.model_manager.get_available_models():
        system.model_manager.load_model(model_id)

    system.transcript = TranscriptManager()
    system.agent_generator = DynamicAgentGenerator(
        system.model_manager, system.transcript
    )

    sess['ddx_system'] = system
    sess['current_models'] = cache_key
    return "ready"

# ---------------------------------------------------------------------------
# Example cases
# ---------------------------------------------------------------------------

EXAMPLES = {
    "STEMI": (
        "A 58-year-old male with history of type 2 diabetes and hypertension presents "
        "with crushing substernal chest pain radiating to his left arm that began 90 "
        "minutes ago. He is diaphoretic and anxious.\n\n"
        "Vitals: BP 165/95, HR 92, RR 22, SpO2 96% on room air\n"
        "ECG: ST elevation in leads V1-V4 with reciprocal changes in II, III, aVF\n"
        "Labs: Troponin I elevated at 2.4 ng/mL (normal <0.04)\n\n"
        "Physical exam: JVP not elevated, lungs clear, no murmurs, no edema."
    ),
    "Pulmonary Embolism": (
        "A 42-year-old female presents with sudden onset dyspnea and pleuritic chest "
        "pain. She returned from a 12-hour flight 3 days ago and has been less mobile "
        "than usual. She takes oral contraceptives.\n\n"
        "Vitals: BP 110/70, HR 112, RR 24, SpO2 91% on room air\n"
        "ECG: Sinus tachycardia, S1Q3T3 pattern\n"
        "D-dimer: Elevated at 2.4 mg/L (normal <0.5)\n\n"
        "Physical exam: Right calf tender with mild swelling, tachypneic, clear lungs."
    ),
    "Cholesterol Embolism": (
        "A 61-year-old man presents two weeks after emergency cardiac catheterization "
        "with decreased urinary output and malaise. Examination shows mottled, "
        "reticulated purplish discoloration of the feet (livedo reticularis).\n\n"
        "Labs: Creatinine 4.2 mg/dL (baseline 1.1), eosinophilia (11%), low complement\n"
        "Urinalysis: Mild proteinuria, eosinophiluria\n"
        "Renal biopsy: Intravascular spindle-shaped vacuoles (cholesterol clefts)\n\n"
        "History: Recent cardiac catheterization, chronic hypertension, smoking history."
    ),
}

# ---------------------------------------------------------------------------
# CSS / theming
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
:root {
    --primary: #4f8cff;
    --surface: #1a1a2e;
    --surface-light: #222244;
    --accent: #ff6b6b;
    --text: #e0e0e0;
    --text-dim: #8888aa;
    --success: #4ecdc4;
    --warning: #ffd166;
    --border: #333355;
}

.dark-card {
    background: var(--surface-light);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
}

.agent-response {
    background: rgba(79, 140, 255, 0.06);
    border-left: 3px solid var(--primary);
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 8px 0;
}

.agent-name {
    color: var(--primary);
    font-weight: 600;
}

.confidence-high { color: var(--success); }
.confidence-med { color: var(--warning); }
.confidence-low { color: var(--accent); }

.round-header {
    color: var(--primary);
    border-bottom: 1px solid var(--border);
    padding-bottom: 6px;
    margin-top: 16px;
}

.diagnosis-rank {
    background: linear-gradient(135deg, var(--surface-light), var(--surface));
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
    display: flex;
    align-items: center;
    gap: 12px;
}

.rank-badge {
    background: var(--primary);
    color: white;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
    flex-shrink: 0;
}

.score-bar {
    height: 4px;
    background: var(--border);
    border-radius: 2px;
    overflow: hidden;
    margin-top: 4px;
}
.score-fill {
    height: 100%;
    background: var(--primary);
    border-radius: 2px;
}

.agent-bubble {
    background: rgba(79, 140, 255, 0.04);
    border-left: 3px solid var(--primary);
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 10px 0;
}

.agent-bubble .agent-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.agent-bubble .agent-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
    color: white;
    flex-shrink: 0;
}

.agent-bubble .streaming-content {
    color: #c8c8e0;
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.streaming-cursor::after {
    content: '◊';
    color: #60a5fa;
    animation: pulseSubtle 1.2s ease-in-out infinite;
    margin-left: 2px;
}

@keyframes pulseSubtle {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

.round-divider {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 8px 0;
    color: var(--text-dim);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.round-divider::before,
.round-divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

.round-header-banner {
    background: linear-gradient(135deg, rgba(79, 140, 255, 0.20), rgba(79, 140, 255, 0.08));
    border: 2px solid rgba(79, 140, 255, 0.5);
    border-radius: 10px;
    padding: 18px 22px;
    margin: 32px 0 16px 0;
    display: flex;
    align-items: center;
    gap: 14px;
}

.round-header-banner .round-number {
    background: var(--primary);
    color: white;
    border-radius: 50%;
    width: 38px;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 18px;
    flex-shrink: 0;
}

.round-header-banner .round-title {
    color: #ffffff;
    font-weight: 700;
    font-size: 20px;
}

.round-header-banner .round-desc {
    color: var(--text-dim);
    font-size: 13px;
    margin-left: auto;
    font-style: italic;
}

/* Keep agent markdown headings smaller than round banners */
.agent-bubble h1, .agent-bubble h2, .agent-bubble h3 {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #a0a0c0 !important;
    margin: 10px 0 4px 0 !important;
}

.agent-bubble h4, .agent-bubble h5, .agent-bubble h6 {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #9090b0 !important;
    margin: 8px 0 4px 0 !important;
}

.status-running {
    color: var(--warning);
    animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
</style>
"""

# ---------------------------------------------------------------------------
# Shared nav header
# ---------------------------------------------------------------------------

def render_nav(active: str = ''):
    """Render the shared navigation header and floating assistant widget."""
    from auth import get_current_user

    user = get_current_user()

    with ui.header().classes('items-center justify-between px-6 py-3').style(
        'background: #12122a; border-bottom: 1px solid #333355;'
    ):
        with ui.row().classes('items-center gap-6'):
            ui.link('Local-DDx', '/').classes('text-xl font-bold no-underline').style(
                'color: #4f8cff;'
            )
            for label, href in [('Dashboard', '/dashboard'), ('Pipeline', '/pipeline'), ('History', '/history'), ('Review', '/review'), ('Guide', '/guide')]:
                style = 'color: #ffffff; font-weight: 600;' if active == label else 'color: #8888aa;'
                ui.link(label, href).classes('text-sm no-underline').style(style)

        # Auth section (right side)
        with ui.row().classes('items-center gap-3'):
            if user:
                ui.label(user['email']).classes('text-xs').style('color: #8888aa;')

                def logout():
                    app.storage.user.clear()
                    ui.navigate.to('/')

                ui.button('Logout', icon='logout', on_click=logout).props(
                    'flat dense size=sm'
                ).style('color: #8888aa;')
            else:
                ui.link('Sign in', '/login').classes('text-sm no-underline').style('color: #8888aa;')

    # Floating assistant chat bubble (on every page)
    from assistant import render_assistant_widget
    render_assistant_widget()


# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------

@ui.page('/')
def landing():
    render_nav()
    with ui.column().classes('w-full items-center justify-center').style(
        'min-height: calc(100vh - 56px); background: #0f0f23;'
    ):
        with ui.column().classes('items-center gap-6 max-w-2xl p-8'):
            ui.label('Local-DDx').classes('text-4xl font-bold').style('color: #4f8cff;')
            ui.label('Multi-Agent Collaborative Differential Diagnosis').style(
                'color: #8888aa; font-size: 16px; text-align: center;'
            )
            ui.label('Social Chain of Thought Pipeline').style(
                'color: #666688; font-size: 14px; text-align: center; margin-top: -8px;'
            )
            ui.separator().style('border-color: #333355; width: 200px; margin: 12px 0;')
            ui.label(
                'HSIL Hackathon 2026 — Harvard School of Public Health'
            ).style('color: #555577; font-size: 13px; text-align: center;')

            with ui.row().classes('gap-4 mt-4 justify-center flex-wrap'):
                ui.button('Run Pipeline', icon='play_arrow', on_click=lambda: ui.navigate.to('/pipeline')).props(
                    'size=lg color=primary'
                )
                ui.button('Case History', icon='history', on_click=lambda: ui.navigate.to('/history')).props(
                    'size=lg flat'
                ).style('color: #ffd166;')
                ui.button('Synonym Review', icon='rate_review', on_click=lambda: ui.navigate.to('/review')).props(
                    'size=lg flat'
                ).style('color: #4ecdc4;')


# ---------------------------------------------------------------------------
# Pipeline page
# ---------------------------------------------------------------------------

@ui.page('/pipeline')
def pipeline_page():
    # Auth guard
    from auth import require_auth
    user = require_auth()
    if not user:
        return

    # Inject custom CSS
    ui.html(CUSTOM_CSS)
    render_nav(active='Pipeline')

    # -- State for this page --
    default_backend = os.environ.get('INFERENCE_BACKEND', 'ollama')
    ollama_url = {'value': os.environ.get('INFERENCE_URL', 'http://localhost:11434')}
    active_backend = {'value': default_backend}
    ollama_models_cache = {'value': prioritized_models(get_ollama_models(ollama_url['value']))}
    mlx_models_cache = {'value': get_mlx_models()}
    runpod_models_cache = {'value': get_runpod_models()}

    # Set initial model list based on default backend
    if default_backend == 'mlx':
        models_list = {'value': list(mlx_models_cache['value'])}
    elif default_backend == 'runpod':
        models_list = {'value': list(runpod_models_cache['value'])}
    else:
        models_list = {'value': list(ollama_models_cache['value'])}
    running = {'value': False}

    # Status label in the page (not header)
    status_label = ui.label('Ready').classes('text-sm').style(
        'color: #8888aa; position: fixed; top: 14px; right: 24px; z-index: 100;'
    )

    # ============================
    # Main layout
    # ============================
    with ui.row().classes('w-full gap-0').style(
        'height: calc(100vh - 56px); background: #0f0f23; flex-wrap: nowrap;'
    ):
        # ========================
        # LEFT PANEL — Controls
        # ========================
        with ui.scroll_area().style(
            'width: 380px; min-width: 380px; background: #14142b; '
            'border-right: 1px solid #333355; height: 100%;'
        ):
          with ui.column().classes('p-5 gap-4'):
            # -- Backend Selection --
            ui.label('Backend').classes('text-sm font-semibold').style('color: #8888aa; letter-spacing: 0.05em;')

            def on_backend_change(e):
                active_backend['value'] = e.value
                if e.value == 'mlx':
                    models = mlx_models_cache['value']
                    url_input.disable()
                elif e.value == 'runpod':
                    models = runpod_models_cache['value']
                    url_input.disable()
                else:
                    models = ollama_models_cache['value']
                    url_input.enable()
                models_list['value'] = models
                conservative_select.options = models
                innovative_select.options = models
                if models:
                    conservative_select.value = models[0]
                    innovative_select.value = models[0]
                else:
                    conservative_select.value = ''
                    innovative_select.value = ''
                conservative_select.update()
                innovative_select.update()

            backend_toggle = ui.toggle(
                {'ollama': 'Ollama', 'mlx': 'MLX (Apple Silicon)', 'runpod': 'RunPod (Cloud)'},
                value=default_backend,
                on_change=on_backend_change,
            ).classes('w-full')

            ui.separator().style('border-color: #333355;')

            # -- Model Selection --
            ui.label('Models').classes('text-sm font-semibold').style('color: #8888aa; letter-spacing: 0.05em;')

            conservative_select = ui.select(
                options=models_list['value'],
                value=models_list['value'][0] if models_list['value'] else '',
                label='Conservative (T=0.3)',
            ).classes('w-full')

            innovative_select = ui.select(
                options=models_list['value'],
                value=models_list['value'][0] if models_list['value'] else '',
                label='Innovative (T=0.8)',
            ).classes('w-full')

            with ui.row().classes('w-full items-end gap-2'):
                url_input = ui.input(
                    label='Ollama URL',
                    value=ollama_url['value'],
                ).classes('flex-grow')

                def refresh_models():
                    ollama_url['value'] = url_input.value
                    if active_backend['value'] == 'mlx':
                        models = get_mlx_models()
                        mlx_models_cache['value'] = models
                    elif active_backend['value'] == 'runpod':
                        models = get_runpod_models()
                        runpod_models_cache['value'] = models
                    else:
                        models = prioritized_models(get_ollama_models(url_input.value))
                        ollama_models_cache['value'] = models
                    models_list['value'] = models
                    conservative_select.options = models
                    innovative_select.options = models
                    if models:
                        conservative_select.value = models[0]
                        innovative_select.value = models[0]
                    conservative_select.update()
                    innovative_select.update()
                    backend_label = active_backend['value'].upper()
                    ui.notify(f'{backend_label}: {len(models)} models found', type='positive')

                ui.button(icon='refresh', on_click=refresh_models).props('flat dense')

            ui.separator().style('border-color: #333355;')

            # -- Pipeline Mode --
            ui.label('Pipeline').classes('text-sm font-semibold').style('color: #8888aa; letter-spacing: 0.05em;')
            mode_toggle = ui.toggle(
                {
                    'quick': 'Quick (3 rounds)',
                    'full': 'Full (7 rounds)',
                },
                value='full',
            ).classes('w-full')

            ui.separator().style('border-color: #333355;')

            # -- Case Input --
            ui.label('Clinical Case').classes('text-sm font-semibold').style('color: #8888aa; letter-spacing: 0.05em;')
            case_input = ui.textarea(
                placeholder='Enter clinical case presentation...',
            ).classes('w-full').style('min-height: 180px;')

            # -- Image Upload (optional) --
            ui.label('Diagnostic Image (optional)').classes('text-sm font-semibold').style(
                'color: #8888aa; letter-spacing: 0.05em; margin-top: 8px;'
            )
            uploaded_image = {'data': None, 'name': None}
            image_label = ui.label('No image uploaded').classes('text-xs').style('color: #555577;')

            async def handle_upload(e):
                if e.content:
                    import base64
                    content = e.content.read()
                    b64 = base64.b64encode(content).decode()
                    uploaded_image['data'] = f"data:image/png;base64,{b64}"
                    uploaded_image['name'] = e.name
                    image_label.text = f'Uploaded: {e.name} ({len(content) // 1024}KB)'
                    image_label.style('color: #4ecdc4;')

            ui.upload(
                on_upload=handle_upload,
                auto_upload=True,
                max_file_size=10_000_000,
            ).props('accept="image/*" flat dense').classes('w-full').style('max-height: 40px;')

            # -- Example Cases --
            with ui.expansion('Example Cases', icon='description').classes('w-full').style('color: #8888aa;'):
                for name, text in EXAMPLES.items():
                    def load_example(t=text):
                        case_input.value = t
                    ui.button(name, on_click=load_example).props('flat dense no-caps').classes('w-full justify-start')

            ui.separator().style('border-color: #333355;')

            # -- Run Button --
            run_button = ui.button(
                'Run Diagnosis', icon='play_arrow',
            ).classes('w-full').props('size=lg color=primary')

            export_button = ui.button(
                'Export Results', icon='download',
            ).classes('w-full').props('flat size=md')

        # ========================
        # RIGHT PANEL — Results
        # ========================
        with ui.column().classes('flex-grow p-5 gap-0').style(
            'background: #0f0f23; height: 100%; overflow: hidden; min-width: 0;'
        ):
            # Tabs
            with ui.tabs().classes('w-full').style(
                'background: transparent; border-bottom: 1px solid #333355;'
            ) as tabs:
                tab_live = ui.tab('Live Feed', icon='stream')
                tab_dx = ui.tab('Diagnoses', icon='medical_services')
                tab_team = ui.tab('Team', icon='groups')
                tab_rounds = ui.tab('Rounds', icon='format_list_numbered')
                tab_cred = ui.tab('Credibility', icon='star')

            with ui.tab_panels(tabs, value=tab_live).classes('w-full').style(
                'background: transparent; overflow-y: auto; '
                'flex: 1 1 0; min-height: 0;'
            ):
                # -- Live Feed --
                with ui.tab_panel(tab_live):
                    live_feed = ui.scroll_area().classes('w-full').style(
                        'min-height: 500px; max-height: calc(100vh - 160px);'
                    )
                    with live_feed:
                        live_container = ui.column().classes('w-full gap-0 p-2')

                # -- Diagnoses --
                with ui.tab_panel(tab_dx):
                    dx_container = ui.column().classes('w-full gap-2')

                # -- Team --
                with ui.tab_panel(tab_team):
                    team_container = ui.column().classes('w-full gap-2')

                # -- Rounds --
                with ui.tab_panel(tab_rounds):
                    rounds_container = ui.column().classes('w-full gap-2')

                # -- Credibility --
                with ui.tab_panel(tab_cred):
                    cred_container = ui.column().classes('w-full gap-2')

    # ============================
    # Run Diagnosis Logic
    # ============================

    # Agent color palette (consistent per agent name)
    AGENT_COLORS = [
        '#4f8cff', '#ff6b6b', '#4ecdc4', '#ffd166', '#a78bfa',
        '#f472b6', '#34d399', '#fb923c', '#60a5fa', '#c084fc',
    ]

    def get_agent_color(name: str) -> str:
        return AGENT_COLORS[hash(name) % len(AGENT_COLORS)]

    async def handle_run():
        sess = _get_session(user['id'])

        if running['value']:
            ui.notify('Diagnosis already running', type='warning')
            return

        case_text = case_input.value
        if not case_text or not case_text.strip():
            ui.notify('Enter a clinical case first', type='warning')
            return

        running['value'] = True
        run_button.disable()
        status_label.text = 'Initializing...'

        # Clear previous results
        live_container.clear()
        dx_container.clear()
        team_container.clear()
        rounds_container.clear()
        cred_container.clear()

        conservative = conservative_select.value
        innovative = innovative_select.value
        url = url_input.value
        backend = active_backend['value']

        # Status message in live feed
        with live_container:
            init_label = ui.label(
                f'Initializing {backend.upper()} backend...'
            ).classes('text-sm').style('color: #8888aa; padding: 8px;')

        # Initialize in background thread (per-user session)
        init_result = await asyncio.to_thread(initialize_system, user['id'], conservative, innovative, url, backend)

        if init_result == 'error':
            status_label.text = 'Error'
            error_hint = 'Is Ollama running?' if backend == 'ollama' else 'Is the MLX model downloaded?'
            init_label.text = f'Error: Failed to initialize. {error_hint}'
            init_label.style('color: #ff6b6b;')
            ui.notify(f'Failed to initialize {backend.upper()} backend', type='negative')
            running['value'] = False
            run_button.enable()
            return

        init_label.text = f'{backend.upper()} ready.'
        status_label.text = 'Processing...'

        # If image uploaded, get AI description and append to case text
        if uploaded_image['data'] and backend == 'runpod':
            init_label.text = 'Analyzing uploaded image...'
            try:
                import requests as req_lib
                inference_url = os.environ.get('INFERENCE_URL', '')
                api_key = os.environ.get('RUNPOD_API_KEY', '')
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"

                image_prompt = [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": uploaded_image['data']}},
                        {"type": "text", "text": (
                            "You are a radiologist/pathologist. Describe this diagnostic image in detail. "
                            "Include: modality (X-ray, CT, MRI, histology, etc.), anatomical region, "
                            "key findings, and any abnormalities. Be specific and clinical."
                        )}
                    ]
                }]

                resp = await asyncio.to_thread(
                    lambda: req_lib.post(
                        f"{inference_url}/chat/completions",
                        headers=headers,
                        json={
                            "model": os.environ.get('RUNPOD_MODEL', 'google/gemma-4-26b-a4b-it'),
                            "messages": image_prompt,
                            "max_tokens": 512,
                            "temperature": 0.3,
                        },
                        timeout=120,
                    )
                )

                if resp.status_code == 200:
                    image_desc = resp.json()["choices"][0]["message"]["content"]
                    case_text = (
                        f"{case_text}\n\n"
                        f"--- DIAGNOSTIC IMAGING ---\n"
                        f"Image: {uploaded_image['name']}\n"
                        f"AI Image Analysis:\n{image_desc}"
                    )
                    init_label.text = 'Image analyzed. Generating specialist team...'
                else:
                    init_label.text = f'Image analysis failed ({resp.status_code}), proceeding without it.'
            except Exception as e:
                init_label.text = f'Image analysis error: {str(e)[:80]}. Proceeding without it.'

        status_label.text = 'Analyzing case...'

        # Analyze case
        ddx_system = sess['ddx_system']
        try:
            analysis = await asyncio.to_thread(
                ddx_system.analyze_case, case_text, "demo_case", 5
            )
        except Exception as e:
            init_label.text = f'Error: Case analysis failed — {e}'
            init_label.style('color: #ff6b6b;')
            status_label.text = 'Error'
            running['value'] = False
            run_button.enable()
            return

        if not analysis.get('success'):
            init_label.text = f'Error: {analysis.get("error", "Unknown error")}'
            init_label.style('color: #ff6b6b;')
            status_label.text = 'Error'
            running['value'] = False
            run_button.enable()
            return

        # Show team in Team tab
        specialists = analysis.get('specialists', [])
        with team_container:
            for spec in specialists:
                role_color = '#4f8cff' if 'conservative' in spec.get('model', '') else '#ff6b6b'
                role_label = 'Conservative' if 'conservative' in spec.get('model', '') else 'Innovative'
                with ui.row().classes('w-full items-center gap-3 p-3').style(
                    f'background: #1a1a2e; border-left: 3px solid {role_color}; border-radius: 0 8px 8px 0;'
                ):
                    ui.label(spec['name']).classes('font-semibold').style(f'color: {role_color};')
                    ui.label(spec['specialty']).style('color: #8888aa;')
                    ui.badge(role_label).props(
                        f'color={"blue" if role_label == "Conservative" else "red"}'
                    )

        # Update init label with team info
        team_names = ', '.join(s['name'] for s in specialists)
        init_label.text = f'Team assembled: {team_names}'
        status_label.text = 'Running pipeline...'

        # ---- Streaming pipeline ----
        # Queue carries three event types:
        #   ('TOKEN', agent_name, token_text)
        #   ('PROGRESS', msg, response_or_none)
        #   ('DONE', result, None)
        event_queue = queue.Queue()

        def progress_callback(msg, response=None):
            event_queue.put(('PROGRESS', msg, response))

        def token_callback(agent_name, token_text):
            event_queue.put(('TOKEN', agent_name, token_text))

        mode = mode_toggle.value
        result_container = [None]

        def run_pipeline():
            try:
                if mode == 'full':
                    result_container[0] = ddx_system.run_full_diagnosis(
                        callback=progress_callback, token_callback=token_callback,
                    )
                else:
                    result_container[0] = ddx_system.run_quick_diagnosis(
                        callback=progress_callback, token_callback=token_callback,
                    )
            except Exception as e:
                result_container[0] = {'error': str(e)}
            finally:
                event_queue.put(('DONE', None, None))

        thread = threading.Thread(target=run_pipeline, daemon=True)
        thread.start()

        # Round metadata for display
        ROUND_INFO = {
            'specialized_ranking': ('1', 'Specialized Ranking', 'Agents rank their specialty relevance'),
            'symptom_management': ('2', 'Symptom Management', 'Immediate triage priorities'),
            'team_differentials': ('3', 'Team Differentials', 'Independent diagnosis generation'),
            'master_list': ('4', 'Master List', 'Consolidating all diagnoses'),
            'refinement': ('5', 'Refinement & Debate', 'Structured adversarial debate'),
            'voting': ('6', 'Preferential Voting', 'Borda count consensus'),
            'cant_miss': ('7', "Can't Miss", 'Critical diagnosis safety check'),
        }
        shown_rounds: set = set()

        # Track active agent bubbles: {agent_name: (container_col, content_label)}
        agent_bubbles: Dict[str, Any] = {}
        agent_count = 0

        def ensure_bubble(agent_name: str):
            """Create a bubble for an agent if it doesn't exist yet."""
            if agent_name in agent_bubbles:
                return agent_bubbles[agent_name]

            color = get_agent_color(agent_name)
            # Extract meaningful initials: skip "Dr." prefix, use first+last
            name_parts = [w for w in agent_name.split() if w.lower().rstrip('.') != 'dr']
            initials = (name_parts[0][0] + name_parts[-1][0]).upper() if len(name_parts) >= 2 else agent_name[0].upper()

            with live_container:
                bubble = ui.column().classes('w-full agent-bubble').style(
                    f'border-left-color: {color};'
                )
                with bubble:
                    with ui.row().classes('agent-header'):
                        ui.html(
                            f'<div class="agent-avatar" style="background:{color};">'
                            f'{initials}</div>'
                        )
                        ui.label(agent_name).classes('font-semibold').style(
                            f'color: {color}; font-size: 14px;'
                        )
                    content_el = ui.markdown('').classes('streaming-content')
                    cursor_el = ui.html(
                        '<span class="streaming-cursor"></span>'
                    )

            agent_bubbles[agent_name] = {
                'bubble': bubble,
                'content_el': content_el,
                'cursor_el': cursor_el,
                'text': '',
            }
            return agent_bubbles[agent_name]

        def finalize_bubble(agent_name: str, response):
            """Remove streaming cursor and add confidence badge."""
            if agent_name not in agent_bubbles:
                return
            info = agent_bubbles[agent_name]
            # Final markdown render (no cursor)
            info['content_el'].set_content(info['text'])
            info['cursor_el'].set_visibility(False)

            if response:
                conf = response.confidence_score
                time_s = response.response_time
                conf_color = '#4ecdc4' if conf >= 0.7 else '#ffd166' if conf >= 0.4 else '#ff6b6b'
                with info['bubble']:
                    with ui.row().classes('items-center gap-2').style('margin-top: 6px;'):
                        ui.badge(f'{conf:.0%}').style(
                            f'background: {conf_color}; color: #1a1a2e;'
                        )
                        ui.label(f'{time_s:.1f}s').classes('text-xs').style('color: #8888aa;')

            # Remove from active bubbles so next appearance creates a new one
            del agent_bubbles[agent_name]

        # Poll the event queue
        while True:
            # Drain all available events in a batch for efficiency
            events = []
            try:
                events.append(event_queue.get_nowait())
                # Grab more if available
                while not event_queue.empty():
                    events.append(event_queue.get_nowait())
            except queue.Empty:
                await asyncio.sleep(0.15)
                continue

            done = False
            for event_type, val1, val2 in events:
                if event_type == 'DONE':
                    done = True
                    break

                elif event_type == 'TOKEN':
                    agent_name, token_text = val1, val2
                    info = ensure_bubble(agent_name)
                    info['text'] += token_text
                    # Update markdown content (renders live)
                    info['content_el'].set_content(info['text'])

                elif event_type == 'PROGRESS':
                    msg, response = val1, val2
                    if response is not None:
                        agent_count += 1
                        finalize_bubble(response.agent_name, response)
                        status_label.text = f'Running... {agent_count} responses'
                    elif msg.startswith('ROUND_START:'):
                        round_key = msg.split(':')[1]
                        if round_key not in shown_rounds:
                            shown_rounds.add(round_key)
                            num, title, desc = ROUND_INFO.get(
                                round_key, ('?', round_key.replace('_', ' ').title(), '')
                            )
                            with live_container:
                                with ui.row().classes('w-full items-center gap-3').style(
                                    'background: linear-gradient(135deg, rgba(79,140,255,0.20), rgba(79,140,255,0.08));'
                                    'border: 2px solid rgba(79,140,255,0.5);'
                                    'border-radius: 10px; padding: 18px 22px; margin: 32px 0 14px 0;'
                                ):
                                    ui.html(
                                        f'<div style="background:#4f8cff;color:white;border-radius:50%;'
                                        f'width:38px;height:38px;display:flex;align-items:center;'
                                        f'justify-content:center;font-weight:800;font-size:18px;'
                                        f'flex-shrink:0;">{num}</div>'
                                    )
                                    ui.label(title).style(
                                        'color: #ffffff; font-weight: 700; font-size: 20px;'
                                    )
                                    ui.label(desc).style(
                                        'color: #8888aa; font-size: 13px; margin-left: auto; font-style: italic;'
                                    )
                    elif msg.startswith('ROUND_COMPLETE:'):
                        round_name = msg.split(':')[1].replace('_', ' ').title()
                        with live_container:
                            ui.separator().style('border-color: #333355; margin: 8px 0;')

            # Auto-scroll
            live_feed.scroll_to(percent=1.0)

            if done:
                break

        thread.join(timeout=300)
        result = result_container[0]
        sess['last_result'] = result

        if result and 'error' not in result:
            duration = result.get('total_duration', 0)
            status_label.text = f'Complete — {duration:.1f}s, {agent_count} responses'
            with live_container:
                ui.html('<div class="round-divider">Pipeline Complete</div>')

            # Populate diagnoses tab
            with dx_container:
                voting = result.get('voting_result')
                if voting:
                    ranked = voting.get('ranked', [])
                    max_score = ranked[0][1] if ranked else 1
                    for i, (diag, score) in enumerate(ranked[:6], 1):
                        pct = (score / max_score * 100) if max_score > 0 else 0
                        with ui.row().classes('w-full items-center gap-3 p-3').style(
                            'background: #1a1a2e; border: 1px solid #333355; border-radius: 8px;'
                        ):
                            ui.html(
                                f'<div style="background:#4f8cff;color:white;border-radius:50%;'
                                f'width:28px;height:28px;display:flex;align-items:center;'
                                f'justify-content:center;font-weight:700;font-size:14px;">{i}</div>'
                            )
                            with ui.column().classes('flex-grow gap-0'):
                                ui.label(diag).classes('font-semibold').style('color: #e0e0e0;')
                                ui.html(
                                    f'<div style="height:4px;background:#333355;border-radius:2px;'
                                    f'overflow:hidden;margin-top:4px;">'
                                    f'<div style="height:100%;width:{pct}%;background:#4f8cff;'
                                    f'border-radius:2px;"></div></div>'
                                )
                            ui.label(f'{score:.1f}').style('color: #4f8cff; font-weight: 600;')
                elif result.get('final_diagnoses'):
                    for i, diag in enumerate(result['final_diagnoses'][:6], 1):
                        name = diag[0] if isinstance(diag, tuple) else diag
                        ui.label(f'{i}. {name}').style('color: #e0e0e0;')

            # Populate rounds tab — collapsible per-round, per-agent
            with rounds_container:
                for round_name, round_data in result.get('rounds', {}).items():
                    responses = round_data.get('responses', [])
                    dur = round_data.get('duration', 0)
                    num, title, desc = ROUND_INFO.get(
                        round_name, ('?', round_name.replace('_', ' ').title(), '')
                    )

                    with ui.expansion(
                        f'Round {num}: {title} — {len(responses)} responses, {dur:.1f}s',
                        icon='expand_more',
                    ).classes('w-full').style(
                        'color: #4f8cff; background: rgba(79,140,255,0.04); '
                        'border: 1px solid #333355; border-radius: 8px; margin: 4px 0; '
                        'overflow: hidden;'
                    ):
                        if desc:
                            ui.label(desc).classes('text-xs').style(
                                'color: #8888aa; margin-bottom: 8px;'
                            )
                        for resp in responses:
                            agent = resp.get('agent_name', 'Unknown')
                            specialty = resp.get('specialty', '')
                            conf = resp.get('confidence_score', 0)
                            time_s = resp.get('response_time', 0)
                            content = resp.get('content', '')
                            color = get_agent_color(agent)
                            conf_color = '#4ecdc4' if conf >= 0.7 else '#ffd166' if conf >= 0.4 else '#ff6b6b'

                            header_text = f'{agent} ({specialty})'
                            with ui.expansion(header_text, icon='person').classes('w-full').style(
                                f'border-left: 3px solid {color}; background: rgba(79,140,255,0.03); '
                                f'border-radius: 0 6px 6px 0; margin: 2px 0; '
                                f'overflow: hidden;'
                            ):
                                with ui.row().classes('items-center gap-2').style('margin-bottom: 6px;'):
                                    ui.badge(f'{conf:.0%}').style(
                                        f'background: {conf_color}; color: #1a1a2e;'
                                    )
                                    ui.label(f'{time_s:.1f}s').classes('text-xs').style('color: #8888aa;')
                                ui.markdown(content).style(
                                    'color: #c0c0d0; font-size: 13px; '
                                    'overflow-wrap: break-word; word-break: break-word; '
                                    'max-width: 100%; overflow-x: hidden;'
                                )

            # Populate credibility tab
            with cred_container:
                cred = result.get('credibility_scores', {})
                if cred:
                    sorted_cred = sorted(cred.items(), key=lambda x: x[1].get('final_score', 0), reverse=True)
                    with ui.row().classes('w-full font-semibold gap-0').style('color: #8888aa; font-size: 13px;'):
                        ui.label('Agent').classes('flex-grow')
                        ui.label('Final').style('width: 60px; text-align: right;')
                        ui.label('Base').style('width: 60px; text-align: right;')
                        ui.label('Valence').style('width: 70px; text-align: right;')
                    for agent_name, scores in sorted_cred:
                        final = scores.get('final_score', 0)
                        base = scores.get('base_score', 0)
                        valence = scores.get('valence', 1.0)
                        with ui.row().classes('w-full items-center gap-0 py-2').style(
                            'border-bottom: 1px solid #222244;'
                        ):
                            ui.label(agent_name).classes('flex-grow').style('color: #e0e0e0;')
                            ui.label(f'{final:.1f}').style('width: 60px; text-align: right; color: #4f8cff; font-weight: 600;')
                            ui.label(f'{base:.1f}').style('width: 60px; text-align: right; color: #8888aa;')
                            ui.label(f'{valence:.1f}x').style('width: 70px; text-align: right; color: #8888aa;')
                else:
                    ui.label('Credibility scores not available').style('color: #8888aa;')

            ui.notify('Diagnosis complete', type='positive')

            # Save to Supabase history (with user_id for RLS)
            try:
                from supabase_client import get_supabase
                sb = get_supabase()
                if sb and user:
                    import json
                    sb.table('case_runs').insert({
                        'user_id': user['id'],
                        'case_name': 'demo_case',
                        'patient_info': case_text,
                        'specialists': json.loads(json.dumps(
                            analysis.get('specialists', []), default=str
                        )),
                        'pipeline_mode': mode,
                        'backend': backend,
                        'model_name': conservative,
                        'result': json.loads(json.dumps(result, default=str)),
                        'duration_seconds': result.get('total_duration', 0),
                    }).execute()
            except Exception as e:
                print(f"Failed to save to history: {e}")

        else:
            error_msg = result.get('error', 'Unknown error') if result else 'Pipeline failed'
            status_label.text = 'Error'
            with live_container:
                ui.label(f'Error: {error_msg}').style('color: #ff6b6b; padding: 8px;')
            ui.notify(f'Error: {error_msg}', type='negative')

        running['value'] = False
        run_button.enable()

    # -- Export handler --
    async def handle_export():
        sess = _get_session(user['id'])
        if sess['ddx_system'] is None or sess['last_result'] is None:
            ui.notify('No results to export', type='warning')
            return

        export_dir = os.path.join(os.path.dirname(__file__), '..', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, f'lddx_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')

        try:
            sess['ddx_system'].export_results(filepath)
            ui.notify(f'Exported to {filepath}', type='positive')
        except Exception as e:
            ui.notify(f'Export failed: {e}', type='negative')

    run_button.on_click(handle_run)
    export_button.on_click(handle_export)


# ---------------------------------------------------------------------------
# Review page (collaborative synonym review)
# ---------------------------------------------------------------------------
import auth  # noqa: F401 — registers /login and /signup routes
import dashboard  # noqa: F401 — registers the /dashboard route
import review  # noqa: F401 — registers the /review route
import history  # noqa: F401 — registers the /history route
import guide  # noqa: F401 — registers the /guide route

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print('=' * 50)
    print('Local-DDx — Starting web interface')
    print('=' * 50)

    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '127.0.0.1')

    models = get_ollama_models()
    print(f'Ollama models found: {len(models)}')
    for m in models[:5]:
        print(f'  - {m}')

    print(f'Starting on {host}:{port}')

    ui.run(
        title='Local-DDx',
        port=port,
        host=host,
        dark=True,
        reload=False,
        favicon='🩺',
        storage_secret=os.environ.get('STORAGE_SECRET', 'lddx-dev-secret-change-me'),
    )


if __name__ in {'__main__', '__mp_main__'}:
    main()
