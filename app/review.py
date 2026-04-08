"""
Collaborative Synonym Review Page — /review

Interactive review form backed by Supabase for real-time collaboration.
Medical students can review synonym mappings, vote on known failures,
and add missing terms.
"""

import os
import sys
import re
import ast
from typing import Dict, List, Tuple, Optional

from nicegui import ui, app

# Import Supabase client
sys.path.insert(0, os.path.dirname(__file__))
from supabase_client import get_supabase

# ---------------------------------------------------------------------------
# Load synonym data from evaluator source
# ---------------------------------------------------------------------------

def _load_synonym_data() -> Tuple[Dict[str, List[Tuple[str, List[str]]]], Dict[str, List[Tuple[str, List[str]]]]]:
    """Parse synonym groups and hierarchies from the evaluator source."""
    evaluator_path = os.path.join(os.path.dirname(__file__), '..', 'benchmark', 'ddx_evaluator.py')

    if not os.path.exists(evaluator_path):
        return {}, {}

    src = open(evaluator_path).read()

    # Parse synonyms dict
    syn_match = re.search(r'synonyms\s*=\s*\{', src)
    if not syn_match:
        return {}, {}

    start = syn_match.start() + src[syn_match.start():].index('{')
    depth = 0
    for i in range(start, len(src)):
        if src[i] == '{': depth += 1
        elif src[i] == '}': depth -= 1
        if depth == 0:
            end = i + 1
            break

    syn_str = re.sub(r'#[^\n]*', '', src[start:end])
    try:
        synonyms = ast.literal_eval(syn_str)
    except Exception:
        synonyms = {}

    # Parse hierarchies
    hier_match = re.search(r'return\s*\{', src[end:])
    hierarchies = {}
    if hier_match:
        h_start = end + hier_match.start() + src[end + hier_match.start():].index('{')
        depth = 0
        for i in range(h_start, len(src)):
            if src[i] == '{': depth += 1
            elif src[i] == '}': depth -= 1
            if depth == 0:
                h_end = i + 1
                break
        hier_str = re.sub(r'#[^\n]*', '', src[h_start:h_end])
        try:
            hierarchies = ast.literal_eval(hier_str)
        except Exception:
            hierarchies = {}

    # Extract categories from source comments
    syn_section = src[syn_match.start():end]
    categories = {}
    current_cat = 'General'
    for line in syn_section.split('\n'):
        cm = re.match(r'\s*#\s*(.+)', line)
        if cm:
            cat = cm.group(1).strip()
            skip = ['build', 'synonym', 'mapping', 'merge', 'normalize', 'bidirectional']
            if len(cat) > 3 and not any(w in cat.lower() for w in skip):
                current_cat = cat
        km = re.match(r"\s*'([^']+)'\s*:", line)
        if km:
            key = km.group(1)
            if key in synonyms:
                if current_cat not in categories:
                    categories[current_cat] = []
                categories[current_cat].append((key, sorted(synonyms[key])))

    # Hierarchy categories
    hier_cats = {}
    current_cat = 'General'
    hier_section = src[end:]
    for line in hier_section.split('\n'):
        cm = re.match(r'\s*#\s*(.+)', line)
        if cm:
            cat = cm.group(1).strip()
            if len(cat) > 3:
                current_cat = cat
        km = re.match(r"\s*'([^']+)'\s*:\s*\[", line)
        if km:
            key = km.group(1)
            if key in hierarchies:
                if current_cat not in hier_cats:
                    hier_cats[current_cat] = []
                hier_cats[current_cat].append((key, sorted(hierarchies[key])))

    return categories, hier_cats


# Known failures from Gemma 4 evaluation
KNOWN_FAILURES = [
    ("458", "Diabetic peripheral neuropathy", "Diabetic Polyneuropathy"),
    ("458", "Insulin-induced hypoglycemia", "Hypoglycemic Episodes (Iatrogenic/Reactive)"),
    ("458", "Organic erectile dysfunction", "Diabetic Autonomic Neuropathy"),
    ("29", "Exogenous insulin administration", "Factitious Hypoglycemia (Exogenous Insulin Admin.)"),
    ("29", "Factitious disorder", "Factitious Hypoglycemia"),
    ("29", "Severe liver disease", "— (not produced)"),
    ("29", "Adrenal insufficiency", "— (not produced)"),
    ("48", "Inadvertent surgical removal of parathyroid glands", "Hypoparathyroidism (Post-Surgical)"),
    ("48", "Hypomagnesemia", "Hypomagnesemia-Induced Hypocalcemia"),
    ("48", "Hypocalcemia", "Hypomagnesemia-Induced Hypocalcemia"),
    ("48", "Hypothyroidism", "— (not produced)"),
    ("512", "Diverticulitis", "— (not produced)"),
    ("512", "Peptic ulcer disease", "— (not produced)"),
    ("512", "Gastroenteritis", "— (not produced)"),
    ("512", "Acute pancreatitis", "— (not produced)"),
]

# Load data once at module level
SYN_CATEGORIES, HIER_CATEGORIES = _load_synonym_data()

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

REVIEW_CSS = """
<style>
.review-header {
    background: linear-gradient(135deg, #1a1a2e, #2d5aa0);
    color: white;
    padding: 28px 32px;
    border-radius: 12px;
    margin-bottom: 20px;
}
.review-header h1 { font-size: 24px; margin: 0 0 4px 0; }
.review-header .subtitle { color: #a0b8e0; font-size: 13px; }

.reviewer-bar {
    background: #1e1e3a;
    border: 1px solid #333355;
    border-radius: 10px;
    padding: 14px 20px;
    margin-bottom: 16px;
}

.section-banner {
    padding: 14px 20px;
    border-radius: 8px;
    margin: 20px 0 12px 0;
    font-weight: 600;
    font-size: 16px;
}
.section-banner.priority {
    background: rgba(204, 68, 0, 0.15);
    border: 1px solid rgba(204, 68, 0, 0.4);
    color: #ff8844;
}
.section-banner.synonyms {
    background: rgba(79, 140, 255, 0.1);
    border: 1px solid rgba(79, 140, 255, 0.3);
    color: #4f8cff;
}
.section-banner.hierarchies {
    background: rgba(45, 122, 58, 0.1);
    border: 1px solid rgba(45, 122, 58, 0.3);
    color: #4ecdc4;
}

.review-row {
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 4px 0;
}
.review-row:hover {
    border-color: #4f8cff;
}

.verdict-badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
}
.verdict-match { background: #1a4a2a; color: #4ecdc4; }
.verdict-no { background: #4a1a1a; color: #ff6b6b; }
.verdict-unsure { background: #4a3a1a; color: #ffd166; }

.other-verdicts {
    font-size: 11px;
    color: #8888aa;
    margin-top: 4px;
}
</style>
"""


# ---------------------------------------------------------------------------
# Review Page
# ---------------------------------------------------------------------------

@ui.page('/review')
def review_page():
    ui.html(REVIEW_CSS)

    # Import nav from main app
    from main import render_nav
    render_nav(active='Review')

    sb = get_supabase()
    reviewer_state = {'id': None, 'name': None}

    # ---- Header ----
    with ui.column().classes('w-full max-w-4xl mx-auto p-4 gap-0').style(
        'margin-top: 56px;'  # offset for fixed nav header
    ):
        ui.html('''
            <div class="review-header">
                <h1>LDDx Synonym Dictionary Review</h1>
                <div class="subtitle">Collaborative review tool for medical student annotators</div>
                <div class="subtitle" style="margin-top:8px;">
                    HSIL Hackathon 2026 &bull; Harvard School of Public Health
                </div>
            </div>
        ''')

        # ---- Reviewer identification ----
        with ui.row().classes('w-full items-end gap-3 reviewer-bar'):
            name_input = ui.input(
                label='Your Name',
                placeholder='Enter your name to start reviewing',
            ).classes('flex-grow')
            join_btn = ui.button('Start Reviewing', icon='login').props('color=primary')

        # Status label
        status = ui.label('').classes('text-sm').style('color: #8888aa;')

        # ---- Main content (hidden until reviewer joins) ----
        main_content = ui.column().classes('w-full gap-0')
        main_content.set_visibility(False)

        async def on_join():
            name = name_input.value.strip()
            if not name:
                ui.notify('Please enter your name', type='warning')
                return

            if sb:
                # Create or find reviewer
                result = sb.table('reviewers').select('*').eq('name', name).execute()
                if result.data:
                    reviewer_state['id'] = result.data[0]['id']
                else:
                    result = sb.table('reviewers').insert({'name': name}).execute()
                    reviewer_state['id'] = result.data[0]['id']
                reviewer_state['name'] = name
                status.text = f'Reviewing as: {name}'
            else:
                reviewer_state['name'] = name
                status.text = f'Reviewing as: {name} (no database — changes won\'t persist)'

            name_input.disable()
            join_btn.disable()
            main_content.set_visibility(True)
            ui.notify(f'Welcome, {name}!', type='positive')

        join_btn.on_click(on_join)

        # ---- Build review sections ----
        with main_content:

            # ================================================
            # SECTION 1: Known Failures (Priority)
            # ================================================
            ui.html('<div class="section-banner priority">Section 1: Known Failures — START HERE</div>')
            ui.label(
                'These are cases where the pipeline got the diagnosis right but the evaluator '
                'marked it wrong. For each row: is the pipeline output clinically equivalent to '
                'the ground truth?'
            ).classes('text-sm').style('color: #8888aa; margin-bottom: 10px;')

            for case_id, gt, pipe in KNOWN_FAILURES:
                with ui.row().classes('w-full items-center gap-3 review-row'):
                    ui.label(f'Case {case_id}').style(
                        'color: #cc8844; font-weight: 600; min-width: 70px;'
                    )
                    with ui.column().classes('flex-grow gap-0'):
                        ui.label(gt).style('color: #e0e0e0; font-size: 13px; font-weight: 600;')
                        ui.label(f'→ {pipe}').style('color: #8888aa; font-size: 12px;')

                    verdict_select = ui.select(
                        options={'': '—', 'match': 'Match', 'not_match': 'Not a match', 'unsure': 'Unsure'},
                        value='',
                    ).style('min-width: 130px;')

                    comment_input = ui.input(placeholder='Comment').style('min-width: 150px;')

                    # Closure for saving
                    def make_save(c=case_id, g=gt, p=pipe, sel=verdict_select, com=comment_input):
                        def save():
                            if not sb or not reviewer_state['id']:
                                return
                            if not sel.value:
                                return
                            sb.table('failure_verdicts').upsert({
                                'reviewer_id': reviewer_state['id'],
                                'case_id': c,
                                'ground_truth': g,
                                'pipeline_output': p,
                                'verdict': sel.value,
                                'comment': com.value or '',
                            }).execute()
                            ui.notify('Saved', type='positive', position='bottom-right', timeout=1000)
                        return save

                    saver = make_save()
                    verdict_select.on_value_change(lambda e, s=saver: s())
                    comment_input.on('blur', lambda e, s=saver: s())

            # ================================================
            # SECTION 2: Existing Synonyms
            # ================================================
            ui.html('<div class="section-banner synonyms">Section 2: Existing Synonym Groups</div>')
            ui.label(
                'Review each mapping. Add missing aliases or flag incorrect ones.'
            ).classes('text-sm').style('color: #8888aa; margin-bottom: 10px;')

            for cat, entries in SYN_CATEGORIES.items():
                if not entries:
                    continue

                with ui.expansion(f'{cat} ({len(entries)} terms)', icon='medical_services').classes('w-full').style(
                    'color: #4f8cff; background: rgba(79,140,255,0.04); '
                    'border: 1px solid #333355; border-radius: 8px; margin: 4px 0;'
                ):
                    for canonical, aliases in entries:
                        deduped = [a for a in aliases if a.lower() != canonical.lower()]
                        alias_str = ', '.join(deduped) if deduped else '—'

                        with ui.row().classes('w-full items-start gap-3 review-row'):
                            with ui.column().classes('flex-grow gap-0'):
                                ui.label(canonical).style(
                                    'color: #e0e0e0; font-weight: 600; font-size: 13px;'
                                )
                                ui.label(alias_str).style(
                                    'color: #8888aa; font-size: 12px;'
                                )

                            add_input = ui.input(placeholder='+ add alias').style('min-width: 140px;')
                            flag_input = ui.input(placeholder='Flag issue').style('min-width: 120px;')

                            def make_syn_save(ct=cat, cn=canonical, ai=add_input, fi=flag_input):
                                def save():
                                    if not sb or not reviewer_state['id']:
                                        return
                                    if not ai.value and not fi.value:
                                        return
                                    sb.table('synonym_verdicts').upsert({
                                        'reviewer_id': reviewer_state['id'],
                                        'category': ct,
                                        'canonical_term': cn,
                                        'alias_to_add': ai.value or '',
                                        'flag_issue': fi.value or '',
                                    }).execute()
                                    ui.notify('Saved', type='positive', position='bottom-right', timeout=1000)
                                return save

                            syn_saver = make_syn_save()
                            add_input.on('blur', lambda e, s=syn_saver: s())
                            flag_input.on('blur', lambda e, s=syn_saver: s())

            # ================================================
            # SECTION 3: Hierarchies
            # ================================================
            ui.html('<div class="section-banner hierarchies">Section 3: Clinical Hierarchies</div>')
            ui.label(
                'Check parent/child relationships. Add missing subtypes or flag errors.'
            ).classes('text-sm').style('color: #8888aa; margin-bottom: 10px;')

            for cat, entries in HIER_CATEGORIES.items():
                if not entries:
                    continue

                with ui.expansion(f'{cat} ({len(entries)} groups)', icon='account_tree').classes('w-full').style(
                    'color: #4ecdc4; background: rgba(45,122,58,0.04); '
                    'border: 1px solid #2a4a3a; border-radius: 8px; margin: 4px 0;'
                ):
                    for supertype, subtypes in entries:
                        with ui.row().classes('w-full items-start gap-3 review-row'):
                            with ui.column().classes('flex-grow gap-0'):
                                ui.label(supertype).style(
                                    'color: #e0e0e0; font-weight: 600; font-size: 13px;'
                                )
                                ui.label(', '.join(subtypes)).style(
                                    'color: #8888aa; font-size: 12px;'
                                )

                            add_input = ui.input(placeholder='+ add subtype').style('min-width: 140px;')
                            flag_input = ui.input(placeholder='Flag issue').style('min-width: 120px;')

                            def make_hier_save(sp=supertype, ai=add_input, fi=flag_input):
                                def save():
                                    if not sb or not reviewer_state['id']:
                                        return
                                    if not ai.value and not fi.value:
                                        return
                                    sb.table('hierarchy_verdicts').upsert({
                                        'reviewer_id': reviewer_state['id'],
                                        'supertype': sp,
                                        'subtype_to_add': ai.value or '',
                                        'flag_issue': fi.value or '',
                                    }).execute()
                                    ui.notify('Saved', type='positive', position='bottom-right', timeout=1000)
                                return save

                            hier_saver = make_hier_save()
                            add_input.on('blur', lambda e, s=hier_saver: s())
                            flag_input.on('blur', lambda e, s=hier_saver: s())

            # Footer
            ui.separator().style('border-color: #333355; margin-top: 24px;')
            ui.label(
                f'Synonym groups: {sum(len(v) for v in SYN_CATEGORIES.values())} | '
                f'Hierarchy groups: {sum(len(v) for v in HIER_CATEGORIES.values())} | '
                f'Known failures: {len(KNOWN_FAILURES)}'
            ).classes('text-xs').style('color: #666; margin-top: 8px;')
