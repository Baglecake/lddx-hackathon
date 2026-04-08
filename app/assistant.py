"""
LDDx Assistant — Floating chat widget on every page.

A knowledge-grounded AI assistant that helps users navigate
the platform and understand medical terminology.
Appears as a chat bubble in the bottom-right corner.
"""

import os
import sys
import asyncio
import requests as req_lib

from nicegui import ui

sys.path.insert(0, os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Knowledge chunks for RAG-style retrieval
# ---------------------------------------------------------------------------

KNOWLEDGE_CHUNKS = [
    {
        "title": "Getting Started",
        "keywords": ["start", "begin", "how", "what", "overview", "about", "intro"],
        "content": (
            "Local-DDx is a multi-agent AI system for collaborative differential diagnosis. "
            "It uses 'Social Chain of Thought' where multiple AI specialist agents debate "
            "diagnoses through structured rounds. The app runs at www.lddx.ca and has several "
            "pages: Pipeline (run diagnoses), History (review past cases), Review (synonym "
            "dictionary collaboration), and this Assistant."
        ),
    },
    {
        "title": "Pipeline — Running a Diagnosis",
        "keywords": ["pipeline", "run", "diagnos", "case", "patient", "start diagnosis"],
        "content": (
            "To run a diagnosis: 1) Go to the Pipeline page. 2) Select a backend (RunPod Cloud "
            "for the web version, MLX or Ollama for local). 3) Enter a clinical case in the text "
            "area or load an example case. 4) Optionally upload a diagnostic image. 5) Choose "
            "Quick (3 rounds) or Full (7 rounds) mode. 6) Click 'Run Diagnosis'. You'll see "
            "specialist agents streaming their responses in real-time."
        ),
    },
    {
        "title": "The 7-Round Pipeline",
        "keywords": ["round", "7 round", "full", "pipeline", "process", "how work", "stages"],
        "content": (
            "The full pipeline has 7 rounds: "
            "1) Specialized Ranking — agents rate their specialty's relevance. "
            "2) Symptom Management — immediate triage priorities. "
            "3) Team Differentials — each agent independently proposes diagnoses. "
            "4) Master List — consolidation of all diagnoses. "
            "5) Refinement & Debate — 3 sub-rounds of adversarial debate where agents "
            "challenge each other's reasoning. "
            "6) Preferential Voting — Borda count weighted by credibility scores. "
            "7) Can't Miss — safety check for critical diagnoses. "
            "Quick mode runs only rounds 3, 5, and 7."
        ),
    },
    {
        "title": "Specialist Agents",
        "keywords": ["agent", "specialist", "team", "doctor", "conservative", "innovative"],
        "content": (
            "The pipeline dynamically generates 4-6 specialist agents based on the case. "
            "Each agent has a name, medical specialty, persona, and reasoning style. "
            "Agents alternate between 'Conservative' (temperature 0.3, cautious reasoning) "
            "and 'Innovative' (temperature 0.8, creative/lateral thinking). The team is "
            "proposed by the AI itself based on the clinical presentation."
        ),
    },
    {
        "title": "Diagnostic Imaging",
        "keywords": ["image", "imaging", "upload", "x-ray", "ct", "mri", "scan", "photo", "picture"],
        "content": (
            "You can upload diagnostic images (X-rays, CT scans, MRIs, histology slides) "
            "alongside your clinical case. The AI (Gemma 4) will analyze the image first, "
            "then include its findings in the case description so all specialist agents can "
            "reference the imaging results. This works when using the RunPod (Cloud) backend. "
            "The image upload is optional — the pipeline works fine with text only."
        ),
    },
    {
        "title": "Case History",
        "keywords": ["history", "past", "previous", "save", "record", "old case"],
        "content": (
            "Every completed pipeline run is automatically saved. Go to the History page to "
            "browse past cases. Click on any case to see the full detail: case presentation, "
            "specialist team, final diagnoses with scores, and complete round transcripts. "
            "You can expand individual rounds and agent responses. Cases can be downloaded as JSON."
        ),
    },
    {
        "title": "Synonym Review — Overview",
        "keywords": ["review", "synonym", "classroom", "collaborate", "dictionary"],
        "content": (
            "The Synonym Review tool lets medical students collaboratively review and improve "
            "the diagnostic evaluation dictionary. The evaluator uses synonym mappings to "
            "determine if the pipeline's diagnosis matches the ground truth. Students join "
            "a classroom (via a shareable code), then review three sections: diagnostic match "
            "review, synonym groups, and clinical hierarchies."
        ),
    },
    {
        "title": "Synonym Review — Section 1 (Diagnostic Match)",
        "keywords": ["match", "mismatch", "failure", "evaluator", "ground truth", "section 1"],
        "content": (
            "Section 1 shows cases where the pipeline produced a correct diagnosis but the "
            "automated evaluator couldn't match it to the ground truth. For each pair, students "
            "decide: Match (same condition, different wording — add as synonym), Not a match "
            "(genuinely different diagnoses), or Unsure (needs discussion). Items are sorted "
            "by frequency — the most impactful terms appear first."
        ),
    },
    {
        "title": "Synonym Review — Classrooms",
        "keywords": ["classroom", "join", "create", "code", "team", "group"],
        "content": (
            "To start reviewing, you need to join or create a classroom. Create a classroom "
            "to get a 6-character code (like 'ABC123') that you can share with your team. "
            "Everyone in the same classroom sees each other's reviews. Click 'Refresh Others' "
            "to see teammates' recent submissions."
        ),
    },
    {
        "title": "Models and Backends",
        "keywords": ["model", "gemma", "qwen", "mlx", "ollama", "runpod", "backend", "gpu"],
        "content": (
            "The app supports three inference backends: "
            "1) Ollama — runs models locally via Ollama server. "
            "2) MLX (Apple Silicon) — runs models natively on Mac M-series chips. "
            "3) RunPod (Cloud) — sends requests to a GPU server running Gemma 4. "
            "The default cloud model is google/gemma-4-26b-a4b-it, a Mixture-of-Experts "
            "model with 26B total parameters but only 4B active per token."
        ),
    },
    {
        "title": "Credibility Scores",
        "keywords": ["credibility", "score", "quality", "valence", "Dr. Reed"],
        "content": (
            "Each agent receives a credibility score based on their contributions. The score "
            "uses the 'Dr. Reed' methodology: Insight (diagnostic quality), Synthesis "
            "(diagnostic breadth), and Action (actionability). These are weighted and "
            "multiplied by a Professional Valence factor. Higher credibility agents have "
            "more influence in the voting round."
        ),
    },
    {
        "title": "Voting and Consensus",
        "keywords": ["vote", "voting", "borda", "consensus", "final", "ranking"],
        "content": (
            "In the voting round, each agent casts a preferential vote for their top 3 "
            "diagnoses. Votes are tallied using Borda count (3 points for 1st, 2 for 2nd, "
            "1 for 3rd) weighted by each agent's credibility score. The final ranking "
            "represents the team's consensus diagnosis."
        ),
    },
]


def _get_relevant_knowledge(query: str, max_chunks: int = 3) -> str:
    """Retrieve relevant knowledge chunks based on keyword matching."""
    query_lower = query.lower()
    scored = []
    for chunk in KNOWLEDGE_CHUNKS:
        score = sum(1 for kw in chunk["keywords"] if kw in query_lower)
        # Bonus for title match
        if any(word in chunk["title"].lower() for word in query_lower.split()):
            score += 2
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: -x[0])
    top = scored[:max_chunks]

    if not top:
        # Return general overview if no match
        return KNOWLEDGE_CHUNKS[0]["content"]

    return "\n\n".join(f"[{c['title']}]\n{c['content']}" for _, c in top)


SYSTEM_PROMPT = """You are the LDDx Assistant, a helpful guide for the Local-DDx diagnostic platform at www.lddx.ca.

Use the following knowledge to answer the user's question:

{knowledge}

Guidelines:
- Be concise — 2-3 sentences when possible
- If asked about medical terminology, explain clearly for a medical student audience
- Guide users to the right page when relevant
- Do NOT provide actual medical advice or diagnoses
- If you don't know something about the platform, say so honestly"""


def _chat_completion(user_message: str, history: list, max_tokens: int = 512) -> str:
    """Call the Gemma 4 model on RunPod."""
    knowledge = _get_relevant_knowledge(user_message)
    system = SYSTEM_PROMPT.format(knowledge=knowledge)

    messages = [{"role": "system", "content": system}]
    # Include last few messages for context
    messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_message})

    url = os.environ.get('INFERENCE_URL', '')
    if not url:
        return "I'm not connected to a model right now. Please check the server configuration."

    api_key = os.environ.get('RUNPOD_API_KEY', '')
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = req_lib.post(
            f"{url}/chat/completions",
            headers=headers,
            json={
                "model": os.environ.get('RUNPOD_MODEL', 'google/gemma-4-26b-a4b-it'),
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.5,
            },
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        return f"Sorry, I got an error ({resp.status_code}). The model server may be loading."
    except Exception as e:
        return f"Sorry, I couldn't reach the model server."


# ---------------------------------------------------------------------------
# Floating widget — call this from every page
# ---------------------------------------------------------------------------

def render_assistant_widget():
    """Render the floating chat bubble widget. Call from any page."""

    # State
    chat_state = {'open': False, 'history': []}

    # Floating container
    with ui.element('div').classes('fixed bottom-6 right-6 z-50'):

        # Chat panel (hidden by default)
        chat_panel = ui.card().classes('absolute bottom-16 right-0').style(
            'width: 380px; max-height: 500px; background: #14142b; '
            'border: 1px solid #333355; border-radius: 12px; '
            'display: flex; flex-direction: column; overflow: hidden;'
        )
        chat_panel.set_visibility(False)

        with chat_panel:
            # Header
            with ui.row().classes('w-full items-center justify-between p-3').style(
                'border-bottom: 1px solid #333355; flex-shrink: 0;'
            ):
                with ui.row().classes('items-center gap-2'):
                    ui.html(
                        '<div style="background:#4f8cff;color:white;border-radius:50%;'
                        'width:28px;height:28px;display:flex;align-items:center;'
                        'justify-content:center;font-size:14px;">?</div>'
                    )
                    with ui.column().classes('gap-0'):
                        ui.label('LDDx Assistant').style('color: #4f8cff; font-weight: 600; font-size: 13px;')
                        ui.label('Powered by Gemma 4').style('color: #555577; font-size: 10px;')

                def clear_chat():
                    chat_state['history'] = []
                    messages_container.clear()
                    with messages_container:
                        _add_assistant_msg(
                            "Hi! I can help you navigate the platform, explain how the pipeline works, "
                            "or clarify medical terminology. What would you like to know?"
                        )

                ui.button(icon='delete_outline', on_click=clear_chat).props(
                    'flat dense round size=sm'
                ).style('color: #555577;')

            # Messages area
            messages_scroll = ui.scroll_area().style(
                'flex-grow: 1; max-height: 350px;'
            )
            with messages_scroll:
                messages_container = ui.column().classes('w-full gap-2 p-3')
                with messages_container:
                    _add_assistant_msg(
                        "Hi! I can help you navigate the platform, explain how the pipeline works, "
                        "or clarify medical terminology. What would you like to know?"
                    )

            # Input area
            with ui.row().classes('w-full items-center gap-2 p-2').style(
                'border-top: 1px solid #333355; flex-shrink: 0;'
            ):
                msg_input = ui.input(placeholder='Ask a question...').classes('flex-grow').props(
                    'outlined dense'
                ).style('font-size: 13px;')

                async def send():
                    user_msg = msg_input.value.strip()
                    if not user_msg:
                        return
                    msg_input.value = ''

                    # Show user message
                    with messages_container:
                        ui.label(user_msg).style(
                            'background: #2d5aa0; color: white; padding: 8px 12px; '
                            'border-radius: 10px 10px 2px 10px; font-size: 13px; '
                            'align-self: flex-end; max-width: 85%; margin-left: auto;'
                        )

                    messages_scroll.scroll_to(percent=1.0)

                    # Show thinking
                    with messages_container:
                        thinking = ui.label('Thinking...').style(
                            'color: #555577; font-size: 12px; font-style: italic;'
                        )

                    # Get response
                    response = await asyncio.to_thread(
                        _chat_completion, user_msg, chat_state['history']
                    )

                    # Update history
                    chat_state['history'].append({"role": "user", "content": user_msg})
                    chat_state['history'].append({"role": "assistant", "content": response})

                    # Remove thinking, show response
                    messages_container.remove(thinking)
                    with messages_container:
                        _add_assistant_msg(response)

                    messages_scroll.scroll_to(percent=1.0)

                ui.button(icon='send', on_click=send).props(
                    'flat dense round size=sm'
                ).style('color: #4f8cff;')
                msg_input.on('keydown.enter', send)

        # Toggle button
        def toggle():
            chat_state['open'] = not chat_state['open']
            chat_panel.set_visibility(chat_state['open'])

        ui.button(icon='chat', on_click=toggle).props('fab').style(
            'background: #4f8cff; color: white;'
        )


def _add_assistant_msg(text: str):
    """Add an assistant message bubble."""
    with ui.row().classes('w-full gap-2'):
        ui.html(
            '<div style="background:#4f8cff;color:white;border-radius:50%;'
            'width:24px;height:24px;display:flex;align-items:center;'
            'justify-content:center;font-size:11px;flex-shrink:0;margin-top:2px;">A</div>'
        )
        ui.markdown(text).style(
            'color: #c0c0d0; font-size: 13px; max-width: 85%; '
            'overflow-wrap: break-word;'
        )
