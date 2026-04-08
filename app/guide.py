"""
User Guide Page — /guide

Platform documentation and getting started guide.
"""

from nicegui import ui


GUIDE_SECTIONS = [
    {
        "title": "Getting Started",
        "icon": "rocket_launch",
        "content": """
**Local-DDx** is a multi-agent AI system for collaborative differential diagnosis. It uses
*Social Chain of Thought* — multiple AI specialist agents debate diagnoses through structured
rounds to reach a consensus.

**Quick start:**
1. Go to **Pipeline** to run a diagnostic case
2. Enter clinical details (and optionally upload an image)
3. Watch the AI specialists debate in real-time
4. Review the final ranked diagnoses

Your past cases are saved in **History**, and you can contribute to improving the system
through **Synonym Review**.
"""
    },
    {
        "title": "Running a Diagnosis",
        "icon": "play_circle",
        "content": """
1. Navigate to the **Pipeline** page
2. **Select a backend:**
   - *RunPod (Cloud)* — default for the web app, uses Gemma 4 on a cloud GPU
   - *MLX* — for local use on Apple Silicon Macs
   - *Ollama* — for local use with Ollama models
3. **Enter your case** in the text area, or click an example case to load one
4. **Upload an image** (optional) — X-rays, CT scans, MRI, histology slides
5. **Choose pipeline mode:**
   - *Quick (3 rounds)* — faster, good for demos
   - *Full (7 rounds)* — complete diagnostic process with voting
6. Click **Run Diagnosis** and watch the specialists work

The live feed shows each agent's response streaming in real-time with round banners
marking transitions between phases.
"""
    },
    {
        "title": "The 7-Round Pipeline",
        "icon": "format_list_numbered",
        "content": """
| Round | Name | What happens |
|-------|------|-------------|
| 1 | **Specialized Ranking** | Each agent rates their specialty's relevance to the case |
| 2 | **Symptom Management** | Immediate triage and stabilization priorities |
| 3 | **Team Differentials** | Each agent independently proposes 3-5 diagnoses with evidence |
| 4 | **Master List** | All diagnoses consolidated and deduplicated |
| 5 | **Refinement & Debate** | 3 sub-rounds: Initial positions, Direct challenges, Final positions |
| 6 | **Preferential Voting** | Borda count voting weighted by credibility scores |
| 7 | **Can't Miss** | Safety check for critical diagnoses that cannot be missed |

**Quick mode** runs rounds 3, 5, and 7 only.
"""
    },
    {
        "title": "Understanding the Results",
        "icon": "analytics",
        "content": """
After a run completes, check the tabs:

- **Live Feed** — Full streaming transcript of the agent discussion
- **Diagnoses** — Final ranked diagnoses with Borda count scores
- **Team** — The specialist agents and their roles (Conservative vs Innovative)
- **Rounds** — Collapsible view of each round's responses (full content, not truncated)
- **Credibility** — Agent credibility scores (Insight, Synthesis, Action, Valence)

**Credibility scoring** uses the "Dr. Reed" methodology:
- *Insight* = diagnostic quality (diagnoses x 3 + evidence x 2)
- *Synthesis* = diagnostic breadth (diagnoses x 4)
- *Action* = actionability of the first diagnosis
- *Professional Valence* = multiplier based on reasoning quality (0.6x to 1.2x)
"""
    },
    {
        "title": "Diagnostic Imaging",
        "icon": "image",
        "content": """
The pipeline supports multimodal input via **Gemma 4**, which can analyze medical images.

**How it works:**
1. Upload an image in the Pipeline page (drag & drop or click)
2. The AI analyzes the image and generates a clinical description
3. This description is appended to your case text
4. All specialist agents can then reference the imaging findings

**Supported formats:** JPEG, PNG, DICOM (converted), any standard image format up to 10MB.

**Note:** Image analysis only works with the RunPod (Cloud) backend.
"""
    },
    {
        "title": "Case History",
        "icon": "history",
        "content": """
Every completed pipeline run is automatically saved to the cloud.

On the **History** page you can:
- Browse all past cases with previews and top diagnoses
- Click any case to see the full detail
- Expand individual rounds and agent responses
- Download cases as JSON for further analysis

Cases are sorted by date, most recent first.
"""
    },
    {
        "title": "Synonym Review (For Medical Students)",
        "icon": "rate_review",
        "content": """
The **Synonym Review** tool is a collaborative annotation platform where medical students
help improve our diagnostic evaluation system.

**Why this matters:** Our AI might say "Diabetic Polyneuropathy" while the ground truth says
"Diabetic peripheral neuropathy." These are the same thing, but without synonym mappings,
the evaluator marks it wrong.

**How to participate:**
1. Go to the **Review** page
2. **Create a classroom** (get a shareable code) or **join** one with a code
3. Work through three sections:
   - *Diagnostic Match Review* — decide if pipeline output matches ground truth
   - *Synonym Dictionary* — add missing aliases for medical terms
   - *Clinical Hierarchies* — verify parent/child relationships (e.g., STEMI is a subtype of MI)
4. Your classmates can see your submissions via the "Refresh Others" button

The **Compiled View** aggregates all submissions with consensus counts.
"""
    },
    {
        "title": "The Assistant",
        "icon": "chat",
        "content": """
The blue chat bubble in the bottom-right corner is the **LDDx Assistant**. It's powered by
the same Gemma 4 AI model and can help you with:

- How the platform works
- Navigating between pages
- Understanding medical terminology
- Explaining the pipeline rounds
- Troubleshooting issues

Just click the blue bubble and ask a question. The assistant has knowledge about all
features of the platform.
"""
    },
]


@ui.page('/guide')
def guide_page():
    from main import render_nav
    render_nav(active='Guide')

    with ui.column().classes('w-full max-w-4xl mx-auto p-4 gap-4').style(
        'margin-top: 56px; background: #0f0f23; min-height: calc(100vh - 56px);'
    ):
        ui.label('User Guide').classes('text-2xl font-bold').style('color: #4f8cff;')
        ui.label(
            'Everything you need to know about the Local-DDx platform.'
        ).style('color: #8888aa; font-size: 14px; margin-bottom: 8px;')

        for section in GUIDE_SECTIONS:
            with ui.expansion(
                section["title"], icon=section["icon"]
            ).classes('w-full').style(
                'color: #4f8cff; background: rgba(79,140,255,0.04); '
                'border: 1px solid #333355; border-radius: 8px; margin: 4px 0;'
            ):
                ui.markdown(section["content"]).style(
                    'color: #c0c0d0; font-size: 14px; '
                    'overflow-wrap: break-word;'
                )

        ui.separator().style('border-color: #333355; margin-top: 16px;')
        ui.label(
            'Need more help? Click the blue chat bubble in the bottom-right corner.'
        ).style('color: #555577; font-size: 12px; margin-top: 4px;')
