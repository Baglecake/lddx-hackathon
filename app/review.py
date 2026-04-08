"""
Collaborative Synonym Review — /review

Classroom-based collaborative review tool backed by Supabase.
Students join a classroom, review synonym mappings together,
and see each other's contributions in real-time.
"""

import os
import sys
import re
import ast
import random
import string
from typing import Dict, List, Tuple

from nicegui import ui, app

sys.path.insert(0, os.path.dirname(__file__))
from supabase_client import get_supabase


# ---------------------------------------------------------------------------
# Category name cleanup map
# ---------------------------------------------------------------------------

CATEGORY_RENAMES = {
    'Cardiovascular': 'Cardiovascular',
    'Cardiovascular (extended)': 'Cardiovascular',
    'Renal': 'Renal / Nephrology',
    'Respiratory': 'Respiratory / Pulmonary',
    'Endocrine': 'Endocrine / Metabolic',
    'Hematology': 'Hematology / Oncology',
    'Rheumatology': 'Rheumatology',
    'Infectious': 'Infectious Disease',
    'Infectious Disease': 'Infectious Disease',
    'Neurology': 'Neurology',
    'Neurology / Spine': 'Neurology',
    'Gastroenterology': 'Gastroenterology / GI',
    'Movement Disorders / Psychiatry': 'Psychiatry / Neurology',
    'Headache': 'Neurology',
    'Hypertension subtypes': 'Cardiovascular',
    'Urological': 'Urology',
    'Neonatal': 'Neonatal / Pediatric',
    'Neonatal / Blood group': 'Neonatal / Pediatric',
    'Thyroid': 'Endocrine / Metabolic',
    'Oncology / Hematology (extended)': 'Hematology / Oncology',
    'Other': 'General / Other',
    'Vascular / Erectile': 'Cardiovascular',
    'Epidural / Obstetric': 'Obstetrics / Anesthesia',
    'Neuromuscular': 'Neurology',
    'Overdose / Intoxication': 'Toxicology / Emergency',
    'Microbiology / Infectious synonyms': 'Infectious Disease',
    'Toxicology / Poisoning': 'Toxicology / Emergency',
    'Surgical / Post-operative': 'Surgery / Post-operative',
    'Reproductive / Gynecological': 'Obstetrics / Gynecology',
    'Vestibular / ENT': 'ENT / Otolaryngology',
    'GI / Abdominal': 'Gastroenterology / GI',
    'Psychiatric': 'Psychiatry / Neurology',
    'Psychiatric (additional)': 'Psychiatry / Neurology',
    'Prostate': 'Urology',
    'GI specifics': 'Gastroenterology / GI',
    'Musculoskeletal': 'Musculoskeletal / Orthopedic',
    'Hearing': 'ENT / Otolaryngology',
    'Neck / Lymph': 'General / Other',
    'Fracture matching': 'Musculoskeletal / Orthopedic',
    'Infection categorical': 'Infectious Disease',
    'Hepatitis': 'Gastroenterology / GI',
    'Obesity subtypes (GT uses these)': 'Endocrine / Metabolic',
    'Tuberculosis variants': 'Infectious Disease',
    'Urinary': 'Urology',
    'Pediatric / Congenital': 'Neonatal / Pediatric',
    'Seizures': 'Neurology',
    'Cardiac / Ischemia': 'Cardiovascular',
    'Polyps': 'Gastroenterology / GI',
}

# Merge categories with the same clean name
def _clean_categories(raw_cats):
    merged = {}
    for raw_name, entries in raw_cats.items():
        clean = CATEGORY_RENAMES.get(raw_name, raw_name)
        # Skip entries that are clearly code comments not medical categories
        if any(w in clean.lower() for w in ['round ', 'zero-recall', 'additions', 'fixes', 'remaining']):
            clean = 'General / Other'
        if clean not in merged:
            merged[clean] = []
        merged[clean].extend(entries)
    # Sort by category name
    return dict(sorted(merged.items()))


# ---------------------------------------------------------------------------
# Load synonym data from evaluator source
# ---------------------------------------------------------------------------

def _load_synonym_data():
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
        if depth == 0: end = i + 1; break

    try:
        synonyms = ast.literal_eval(re.sub(r'#[^\n]*', '', src[start:end]))
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
            if depth == 0: h_end = i + 1; break
        try:
            hierarchies = ast.literal_eval(re.sub(r'#[^\n]*', '', src[h_start:h_end]))
        except Exception:
            hierarchies = {}

    # Extract raw categories from source comments
    syn_section = src[syn_match.start():end]
    raw_categories = {}
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
                if current_cat not in raw_categories:
                    raw_categories[current_cat] = []
                raw_categories[current_cat].append((key, sorted(synonyms[key])))

    # Hierarchy categories
    raw_hier = {}
    current_cat = 'General'
    for line in src[end:].split('\n'):
        cm = re.match(r'\s*#\s*(.+)', line)
        if cm:
            cat = cm.group(1).strip()
            if len(cat) > 3: current_cat = cat
        km = re.match(r"\s*'([^']+)'\s*:\s*\[", line)
        if km:
            key = km.group(1)
            if key in hierarchies:
                if current_cat not in raw_hier:
                    raw_hier[current_cat] = []
                raw_hier[current_cat].append((key, sorted(hierarchies[key])))

    return _clean_categories(raw_categories), _clean_categories(raw_hier)


def _load_mismatches():
    """Load evaluator mismatches from JSON file."""
    mismatch_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'review_mismatches.json')
    if not os.path.exists(mismatch_path):
        return []
    import json
    with open(mismatch_path) as f:
        data = json.load(f)
    return data.get('items', [])

REVIEW_MISMATCHES = _load_mismatches()
SYN_CATEGORIES, HIER_CATEGORIES = _load_synonym_data()


def _generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

REVIEW_CSS = """
<style>
.review-page { background: #0f0f23; min-height: calc(100vh - 56px); }

.section-banner {
    padding: 16px 22px; border-radius: 8px; margin: 24px 0 8px 0;
    font-weight: 700; font-size: 18px;
}
.section-banner.priority {
    background: rgba(204, 68, 0, 0.15);
    border: 2px solid rgba(204, 68, 0, 0.4); color: #ff8844;
}
.section-banner.synonyms {
    background: rgba(79, 140, 255, 0.1);
    border: 2px solid rgba(79, 140, 255, 0.3); color: #4f8cff;
}
.section-banner.hierarchies {
    background: rgba(45, 122, 58, 0.1);
    border: 2px solid rgba(45, 122, 58, 0.3); color: #4ecdc4;
}
.section-desc {
    color: #8888aa; font-size: 13px; line-height: 1.5;
    padding: 0 4px; margin-bottom: 12px;
}

.review-row {
    background: #1a1a2e; border: 1px solid #2a2a4a;
    border-radius: 6px; padding: 10px 14px; margin: 4px 0;
}
.review-row:hover { border-color: #4f8cff; }

.others-pill {
    display: inline-block; padding: 1px 7px; border-radius: 10px;
    font-size: 10px; font-weight: 600; margin: 1px;
}
.others-match { background: #1a3a2a; color: #4ecdc4; }
.others-no { background: #3a1a1a; color: #ff6b6b; }
.others-unsure { background: #3a2a1a; color: #ffd166; }
.others-added { background: #1a2a3a; color: #60a5fa; }

.classroom-box {
    background: linear-gradient(135deg, #1a1a2e, #1e2848);
    border: 1px solid #333355; border-radius: 12px;
    padding: 24px 28px; margin-bottom: 20px;
}
</style>
"""


# ---------------------------------------------------------------------------
# Helper: fetch others' verdicts for a classroom
# ---------------------------------------------------------------------------

def _fetch_others(sb, classroom_id, reviewer_id, table, key_field, key_value):
    """Fetch other reviewers' submissions for a specific row."""
    if not sb or not classroom_id:
        return []
    try:
        result = sb.table(table).select(
            '*, reviewers(name)'
        ).eq('classroom_id', classroom_id).eq(
            key_field, key_value
        ).neq('reviewer_id', reviewer_id).execute()
        return result.data or []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Review Page
# ---------------------------------------------------------------------------

@ui.page('/review')
def review_page():
    ui.html(REVIEW_CSS)
    from main import render_nav
    render_nav(active='Review')

    sb = get_supabase()
    state = {'reviewer_id': None, 'name': None, 'classroom_id': None, 'classroom_name': None}

    with ui.column().classes('w-full max-w-4xl mx-auto p-4 gap-0 review-page'):

        # ============================================================
        # CLASSROOM JOIN/CREATE
        # ============================================================
        with ui.column().classes('w-full gap-4 classroom-box') as classroom_box:
            ui.label('Synonym Dictionary Review').classes('text-2xl font-bold').style('color: #4f8cff;')
            ui.label(
                'Join an existing classroom or create a new one. '
                'Everyone in the same classroom sees each other\'s reviews in real-time.'
            ).style('color: #8888aa; font-size: 13px;')

            ui.separator().style('border-color: #333355;')

            name_input = ui.input(label='Your Name', placeholder='e.g. Jane Smith').classes('w-full')

            with ui.tabs().classes('w-full') as tabs:
                join_tab = ui.tab('Join Classroom')
                create_tab = ui.tab('Create Classroom')

            with ui.tab_panels(tabs, value=join_tab).classes('w-full'):
                with ui.tab_panel(join_tab):
                    code_input = ui.input(label='Classroom Code', placeholder='e.g. ABC123').classes('w-full')
                    join_btn = ui.button('Join', icon='login').props('color=primary').classes('w-full')

                with ui.tab_panel(create_tab):
                    classroom_name_input = ui.input(
                        label='Classroom Name', placeholder='e.g. HSIL Hackathon Team'
                    ).classes('w-full')
                    create_btn = ui.button('Create & Join', icon='add').props('color=primary').classes('w-full')

        # Status
        status_label = ui.label('').classes('text-sm').style('color: #8888aa;')

        # Main review content — hidden until joined
        main_content = ui.column().classes('w-full gap-0')
        main_content.set_visibility(False)

        async def do_join():
            name = name_input.value.strip()
            code = code_input.value.strip().upper()
            if not name:
                ui.notify('Enter your name', type='warning'); return
            if not code:
                ui.notify('Enter a classroom code', type='warning'); return
            if not sb:
                ui.notify('Database not connected', type='negative'); return

            # Find classroom
            cr = sb.table('classrooms').select('*').eq('join_code', code).execute()
            if not cr.data:
                ui.notify(f'No classroom with code "{code}"', type='negative'); return

            state['classroom_id'] = cr.data[0]['id']
            state['classroom_name'] = cr.data[0]['name']

            # Create/find reviewer
            rr = sb.table('reviewers').select('*').eq('name', name).eq(
                'classroom_id', state['classroom_id']
            ).execute()
            if rr.data:
                state['reviewer_id'] = rr.data[0]['id']
            else:
                rr = sb.table('reviewers').insert({
                    'name': name, 'classroom_id': state['classroom_id']
                }).execute()
                state['reviewer_id'] = rr.data[0]['id']

            state['name'] = name
            classroom_box.set_visibility(False)
            status_label.text = f'{name} — {state["classroom_name"]} ({code})'
            main_content.set_visibility(True)
            _load_others_and_show()
            ui.notify(f'Joined {state["classroom_name"]}!', type='positive')

        async def do_create():
            name = name_input.value.strip()
            cname = classroom_name_input.value.strip()
            if not name:
                ui.notify('Enter your name', type='warning'); return
            if not cname:
                ui.notify('Enter a classroom name', type='warning'); return
            if not sb:
                ui.notify('Database not connected', type='negative'); return

            code = _generate_code()

            # Create reviewer first (without classroom)
            rr = sb.table('reviewers').insert({'name': name}).execute()
            state['reviewer_id'] = rr.data[0]['id']

            # Create classroom
            cr = sb.table('classrooms').insert({
                'name': cname, 'join_code': code, 'created_by': state['reviewer_id']
            }).execute()
            state['classroom_id'] = cr.data[0]['id']
            state['classroom_name'] = cname

            # Link reviewer to classroom
            sb.table('reviewers').update({
                'classroom_id': state['classroom_id']
            }).eq('id', state['reviewer_id']).execute()

            state['name'] = name
            classroom_box.set_visibility(False)
            status_label.text = f'{name} — {cname} (Code: {code})'
            main_content.set_visibility(True)
            ui.notify(f'Created classroom "{cname}" — share code: {code}', type='positive', timeout=10000)

        join_btn.on_click(do_join)
        create_btn.on_click(do_create)

        # ============================================================
        # REVIEW SECTIONS (inside main_content)
        # ============================================================

        # Containers for "others" badges (populated after join)
        others_containers = {}

        def _load_others_and_show():
            """Load and display other reviewers' verdicts."""
            if not sb or not state['classroom_id']:
                return

            # Failure verdicts
            for case_id, gt, pipe in KNOWN_FAILURES:
                key = f'fail_{case_id}_{gt}'
                if key in others_containers:
                    others = _fetch_others(
                        sb, state['classroom_id'], state['reviewer_id'],
                        'failure_verdicts', 'ground_truth', gt
                    )
                    container = others_containers[key]
                    container.clear()
                    with container:
                        for o in others:
                            rname = o.get('reviewers', {}).get('name', '?') if isinstance(o.get('reviewers'), dict) else '?'
                            v = o.get('verdict', '')
                            css = 'others-match' if v == 'match' else 'others-no' if v == 'not_match' else 'others-unsure'
                            vlabel = 'Match' if v == 'match' else 'No' if v == 'not_match' else '?'
                            ui.html(f'<span class="others-pill {css}">{rname}: {vlabel}</span>')

            # Synonym additions
            for cat, entries in SYN_CATEGORIES.items():
                for canonical, _ in entries:
                    key = f'syn_{canonical}'
                    if key in others_containers:
                        others = _fetch_others(
                            sb, state['classroom_id'], state['reviewer_id'],
                            'synonym_verdicts', 'canonical_term', canonical
                        )
                        container = others_containers[key]
                        container.clear()
                        with container:
                            for o in others:
                                rname = o.get('reviewers', {}).get('name', '?') if isinstance(o.get('reviewers'), dict) else '?'
                                added = o.get('alias_to_add', '')
                                flag = o.get('flag_issue', '')
                                if added:
                                    ui.html(f'<span class="others-pill others-added">{rname}: +{added}</span>')
                                if flag:
                                    ui.html(f'<span class="others-pill others-unsure">{rname}: {flag}</span>')

        with main_content:

            # Link to compiled view
            with ui.row().classes('w-full justify-end gap-2').style('margin-bottom: 8px;'):
                ui.button('View Compiled Dictionary', icon='summarize',
                          on_click=lambda: ui.navigate.to('/review/compiled')).props('flat size=sm').style('color: #4ecdc4;')
                ui.button('Refresh Others', icon='refresh',
                          on_click=_load_others_and_show).props('flat size=sm').style('color: #8888aa;')

            # ============================
            # SECTION 1: Evaluator Mismatches
            # ============================
            ui.html('<div class="section-banner priority">1. Diagnostic Match Review (Start Here)</div>')
            ui.html(f'''<div class="section-desc">
                Our AI pipeline produced diagnoses that the automated evaluator couldn't match
                to the ground truth. There are <b>{len(REVIEW_MISMATCHES)} unmatched terms</b>
                across {sum(m["case_count"] for m in REVIEW_MISMATCHES)} case instances.<br><br>
                <b>Your job:</b> For each term, decide if the pipeline's output is
                <b>clinically equivalent</b> to the ground truth, or if a synonym should be added.<br><br>
                <b>Match</b> = same condition, just different wording (add as synonym)<br>
                <b>Not a match</b> = genuinely different diagnoses (pipeline got it wrong)<br>
                <b>Unsure</b> = needs group discussion<br><br>
                Items are grouped by frequency — the most impactful terms are at the top.
            </div>''')

            # Sort by case count (most impactful first)
            sorted_mismatches = sorted(REVIEW_MISMATCHES, key=lambda x: -x['case_count'])

            # Show in batches via expansion panels to avoid overwhelming
            batch_size = 50
            for batch_start in range(0, len(sorted_mismatches), batch_size):
                batch = sorted_mismatches[batch_start:batch_start + batch_size]
                batch_end = min(batch_start + batch_size, len(sorted_mismatches))
                label = f'Items {batch_start + 1}–{batch_end} of {len(sorted_mismatches)}'

                with ui.expansion(label, icon='checklist').classes('w-full').style(
                    'color: #ff8844; background: rgba(204,68,0,0.04); '
                    'border: 1px solid rgba(204,68,0,0.2); border-radius: 8px; margin: 4px 0;'
                ) as batch_panel:
                    if batch_start == 0:
                        batch_panel.open()

                    for item in batch:
                        gt = item['ground_truth']
                        pipe_examples = ', '.join(item['pipeline_examples'][:2]) or '—'
                        sources = ', '.join(item['sources'])
                        cases = ', '.join(item['example_cases'][:3])
                        count = item['case_count']
                        key = f'fail_{gt}'

                        with ui.column().classes('w-full gap-1 review-row'):
                            with ui.row().classes('w-full items-center gap-3'):
                                ui.label(f'{count}x').style(
                                    'color: #cc8844; font-weight: 700; min-width: 35px; font-size: 12px;'
                                )
                                with ui.column().classes('flex-grow gap-0'):
                                    ui.label(gt).style(
                                        'color: #e0e0e0; font-size: 13px; font-weight: 600;'
                                    )
                                    ui.label(f'Pipeline said: {pipe_examples}').style(
                                        'color: #8888aa; font-size: 11px;'
                                    )
                                    ui.label(f'Cases: {cases} | Model: {sources}').style(
                                        'color: #555577; font-size: 10px;'
                                    )

                                verdict_select = ui.select(
                                    options={'': '—', 'match': 'Match', 'not_match': 'Not a match', 'unsure': 'Unsure'},
                                    value='',
                                ).style('min-width: 130px;')
                                comment_input = ui.input(placeholder='Synonym to add / comment').style(
                                    'min-width: 160px;'
                                )

                            others_containers[key] = ui.row().classes('w-full gap-1 flex-wrap').style('min-height: 0;')

                            def make_save(g=gt, pe=pipe_examples, sel=verdict_select, com=comment_input):
                                def save():
                                    if not sb or not state['reviewer_id'] or not sel.value:
                                        return
                                    sb.table('failure_verdicts').upsert({
                                        'reviewer_id': state['reviewer_id'],
                                        'classroom_id': state['classroom_id'],
                                        'case_id': 'multi', 'ground_truth': g,
                                        'pipeline_output': pe, 'verdict': sel.value,
                                        'comment': com.value or '',
                                    }).execute()
                                    ui.notify('Saved', type='positive', position='bottom-right', timeout=800)
                                return save

                            saver = make_save()
                            verdict_select.on_value_change(lambda e, s=saver: s())
                            comment_input.on('blur', lambda e, s=saver: s())

            # ============================
            # SECTION 2: Synonym Review
            # ============================
            ui.html('<div class="section-banner synonyms">2. Synonym Dictionary Review</div>')
            ui.html('''<div class="section-desc">
                The evaluator uses these synonym mappings to match pipeline output to ground truth.
                Each row shows a <b>canonical diagnosis</b> (from the ground truth dataset) and
                its currently accepted <b>aliases</b> (terms our AI might use instead).<br><br>
                <b>Your tasks:</b><br>
                &bull; If you know an alternative name for a condition that's missing, type it in "add alias"<br>
                &bull; If an existing alias is wrong (different condition), flag it<br>
                &bull; Skip entries you're not sure about — focus on your areas of knowledge
            </div>''')

            for cat, entries in SYN_CATEGORIES.items():
                if not entries:
                    continue
                with ui.expansion(f'{cat} ({len(entries)} terms)', icon='medical_services').classes('w-full').style(
                    'color: #4f8cff; background: rgba(79,140,255,0.04); '
                    'border: 1px solid #333355; border-radius: 8px; margin: 4px 0;'
                ):
                    for canonical, aliases in entries:
                        key = f'syn_{canonical}'
                        deduped = [a for a in aliases if a.lower() != canonical.lower()]
                        alias_str = ', '.join(deduped) if deduped else '—'

                        with ui.column().classes('w-full gap-1 review-row'):
                            ui.label(canonical).style(
                                'color: #e0e0e0; font-weight: 600; font-size: 13px;'
                            )
                            ui.label(f'Aliases: {alias_str}').style(
                                'color: #666688; font-size: 11px; '
                                'overflow-wrap: break-word; word-break: break-word;'
                            )
                            with ui.row().classes('w-full gap-3').style('margin-top: 4px;'):
                                add_input = ui.input(placeholder='+ add alias').classes('flex-grow')
                                flag_input = ui.input(placeholder='Flag issue').classes('flex-grow')

                            others_containers[key] = ui.row().classes('w-full gap-1 flex-wrap').style('min-height: 0;')

                            def make_syn_save(ct=cat, cn=canonical, ai=add_input, fi=flag_input):
                                def save():
                                    if not sb or not state['reviewer_id']:
                                        return
                                    if not ai.value and not fi.value:
                                        return
                                    sb.table('synonym_verdicts').upsert({
                                        'reviewer_id': state['reviewer_id'],
                                        'classroom_id': state['classroom_id'],
                                        'category': ct, 'canonical_term': cn,
                                        'alias_to_add': ai.value or '',
                                        'flag_issue': fi.value or '',
                                    }).execute()
                                    ui.notify('Saved', type='positive', position='bottom-right', timeout=800)
                                return save

                            syn_saver = make_syn_save()
                            add_input.on('blur', lambda e, s=syn_saver: s())
                            flag_input.on('blur', lambda e, s=syn_saver: s())

            # ============================
            # SECTION 3: Hierarchies
            # ============================
            ui.html('<div class="section-banner hierarchies">3. Clinical Hierarchy Review</div>')
            ui.html('''<div class="section-desc">
                These define parent/child relationships between diagnoses. For example,
                "STEMI" is a subtype of "Myocardial Infarction" — if the pipeline says STEMI
                and the ground truth says MI, the hierarchy tells the evaluator it's a partial match.<br><br>
                <b>Your tasks:</b><br>
                &bull; If a subtype is missing, add it<br>
                &bull; If a subtype is listed under the wrong parent, flag it<br>
                &bull; Focus on relationships you're confident about
            </div>''')

            for cat, entries in HIER_CATEGORIES.items():
                if not entries:
                    continue
                with ui.expansion(f'{cat} ({len(entries)} groups)', icon='account_tree').classes('w-full').style(
                    'color: #4ecdc4; background: rgba(45,122,58,0.04); '
                    'border: 1px solid #2a4a3a; border-radius: 8px; margin: 4px 0;'
                ):
                    for supertype, subtypes in entries:
                        with ui.column().classes('w-full gap-1 review-row'):
                            with ui.row().classes('w-full items-start gap-3'):
                                with ui.column().classes('flex-grow gap-0'):
                                    ui.label(supertype).style(
                                        'color: #e0e0e0; font-weight: 600; font-size: 13px;'
                                    )
                                    ui.label(f'Subtypes: {", ".join(subtypes)}').style(
                                        'color: #666688; font-size: 11px;'
                                    )
                                add_input = ui.input(placeholder='+ add subtype').style('min-width: 140px;')
                                flag_input = ui.input(placeholder='Flag issue').style('min-width: 120px;')

                            def make_hier_save(sp=supertype, ai=add_input, fi=flag_input):
                                def save():
                                    if not sb or not state['reviewer_id']:
                                        return
                                    if not ai.value and not fi.value:
                                        return
                                    sb.table('hierarchy_verdicts').upsert({
                                        'reviewer_id': state['reviewer_id'],
                                        'classroom_id': state['classroom_id'],
                                        'supertype': sp,
                                        'subtype_to_add': ai.value or '',
                                        'flag_issue': fi.value or '',
                                    }).execute()
                                    ui.notify('Saved', type='positive', position='bottom-right', timeout=800)
                                return save

                            hier_saver = make_hier_save()
                            add_input.on('blur', lambda e, s=hier_saver: s())
                            flag_input.on('blur', lambda e, s=hier_saver: s())

            # Footer
            ui.separator().style('border-color: #333355; margin-top: 24px;')
            ui.label(
                f'Evaluator mismatches: {len(REVIEW_MISMATCHES)} | '
                f'Synonym groups: {sum(len(v) for v in SYN_CATEGORIES.values())} | '
                f'Hierarchy groups: {sum(len(v) for v in HIER_CATEGORIES.values())}'
            ).classes('text-xs').style('color: #555; margin-top: 8px;')


# ---------------------------------------------------------------------------
# Compiled View — /review/compiled
# ---------------------------------------------------------------------------

@ui.page('/review/compiled')
def compiled_page():
    from main import render_nav
    render_nav(active='Review')

    sb = get_supabase()

    with ui.column().classes('w-full max-w-4xl mx-auto p-4 gap-4').style(
        'margin-top: 56px; background: #0f0f23; min-height: calc(100vh - 56px);'
    ):
        ui.label('Compiled Synonym Dictionary').classes('text-2xl font-bold').style('color: #4f8cff;')
        ui.label(
            'Aggregated view of all reviewer submissions. Shows consensus across classrooms.'
        ).style('color: #8888aa; font-size: 13px; margin-bottom: 12px;')

        if not sb:
            ui.label('Database not connected').style('color: #ff6b6b;')
            return

        # Fetch all data
        failures = sb.table('failure_verdicts').select('*, reviewers(name)').execute().data or []
        syn_adds = sb.table('synonym_verdicts').select('*, reviewers(name)').execute().data or []
        hier_adds = sb.table('hierarchy_verdicts').select('*, reviewers(name)').execute().data or []

        # ---- Failure Verdicts Summary ----
        ui.html('<div class="section-banner priority" style="font-size:16px;">Diagnostic Match Verdicts</div>')

        # Group by ground_truth
        from collections import defaultdict
        fail_groups = defaultdict(list)
        for f in failures:
            fail_groups[f['ground_truth']].append(f)

        if fail_groups:
            with ui.column().classes('w-full gap-2'):
                for gt, verdicts in sorted(fail_groups.items()):
                    matches = sum(1 for v in verdicts if v['verdict'] == 'match')
                    nos = sum(1 for v in verdicts if v['verdict'] == 'not_match')
                    unsures = sum(1 for v in verdicts if v['verdict'] == 'unsure')
                    total = len(verdicts)
                    pipe = verdicts[0].get('pipeline_output', '')

                    with ui.row().classes('w-full items-center gap-3 review-row'):
                        with ui.column().classes('flex-grow gap-0'):
                            ui.label(gt).style('color: #e0e0e0; font-weight: 600; font-size: 13px;')
                            ui.label(f'→ {pipe}').style('color: #8888aa; font-size: 12px;')
                        if matches:
                            ui.html(f'<span class="others-pill others-match">{matches}/{total} Match</span>')
                        if nos:
                            ui.html(f'<span class="others-pill others-no">{nos}/{total} No</span>')
                        if unsures:
                            ui.html(f'<span class="others-pill others-unsure">{unsures}/{total} Unsure</span>')
        else:
            ui.label('No verdicts submitted yet').style('color: #666;')

        # ---- Synonym Additions ----
        ui.html('<div class="section-banner synonyms" style="font-size:16px;">New Synonym Suggestions</div>')

        additions = [s for s in syn_adds if s.get('alias_to_add')]
        flags = [s for s in syn_adds if s.get('flag_issue')]

        if additions:
            with ui.column().classes('w-full gap-1'):
                for s in additions:
                    rname = s.get('reviewers', {}).get('name', '?') if isinstance(s.get('reviewers'), dict) else '?'
                    ui.html(
                        f'<div class="review-row" style="padding:8px 12px;">'
                        f'<b style="color:#e0e0e0;">{s["canonical_term"]}</b> '
                        f'<span style="color:#60a5fa;">+ {s["alias_to_add"]}</span> '
                        f'<span style="color:#666; font-size:11px;">— {rname}</span></div>'
                    )
        else:
            ui.label('No aliases suggested yet').style('color: #666;')

        if flags:
            ui.label('Flagged Issues:').style('color: #ffd166; font-weight: 600; margin-top: 12px;')
            for s in flags:
                rname = s.get('reviewers', {}).get('name', '?') if isinstance(s.get('reviewers'), dict) else '?'
                ui.html(
                    f'<div class="review-row" style="padding:8px 12px;">'
                    f'<b style="color:#e0e0e0;">{s["canonical_term"]}</b> '
                    f'<span style="color:#ffd166;">{s["flag_issue"]}</span> '
                    f'<span style="color:#666; font-size:11px;">— {rname}</span></div>'
                )

        # ---- Hierarchy Additions ----
        ui.html('<div class="section-banner hierarchies" style="font-size:16px;">New Hierarchy Suggestions</div>')

        h_additions = [h for h in hier_adds if h.get('subtype_to_add')]
        if h_additions:
            for h in h_additions:
                rname = h.get('reviewers', {}).get('name', '?') if isinstance(h.get('reviewers'), dict) else '?'
                ui.html(
                    f'<div class="review-row" style="padding:8px 12px;">'
                    f'<b style="color:#e0e0e0;">{h["supertype"]}</b> '
                    f'<span style="color:#4ecdc4;">+ {h["subtype_to_add"]}</span> '
                    f'<span style="color:#666; font-size:11px;">— {rname}</span></div>'
                )
        else:
            ui.label('No subtypes suggested yet').style('color: #666;')

        # ---- Download ----
        ui.separator().style('border-color: #333355; margin-top: 20px;')

        import json

        def download_json():
            data = {
                'failure_verdicts': failures,
                'synonym_additions': syn_adds,
                'hierarchy_additions': hier_adds,
                'exported_at': __import__('datetime').datetime.now().isoformat(),
            }
            content = json.dumps(data, indent=2, default=str)
            ui.download(content.encode(), 'synonym_review_compiled.json', 'application/json')

        with ui.row().classes('gap-3'):
            ui.button('Download JSON', icon='download', on_click=download_json).props('flat').style('color: #4f8cff;')
            ui.button('Back to Review', icon='arrow_back',
                      on_click=lambda: ui.navigate.to('/review')).props('flat').style('color: #8888aa;')
