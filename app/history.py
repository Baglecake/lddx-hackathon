"""
Case History Page — /history

Browse and review past pipeline runs stored in Supabase.
"""

import os
import sys
import json
from datetime import datetime

from nicegui import ui

sys.path.insert(0, os.path.dirname(__file__))
from supabase_client import get_supabase


@ui.page('/history')
def history_page():
    from main import render_nav
    render_nav(active='History')

    sb = get_supabase()

    with ui.column().classes('w-full max-w-5xl mx-auto p-4 gap-4').style(
        'margin-top: 56px; background: #0f0f23; min-height: calc(100vh - 56px);'
    ):
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('Case History').classes('text-2xl font-bold').style('color: #4f8cff;')
            refresh_btn = ui.button('Refresh', icon='refresh').props('flat').style('color: #8888aa;')

        ui.label(
            'Browse past pipeline runs. Click on a case to see the full transcript.'
        ).style('color: #8888aa; font-size: 13px; margin-bottom: 12px;')

        # Container for case list
        case_list = ui.column().classes('w-full gap-2')

        # Detail view (hidden until a case is selected)
        detail_view = ui.column().classes('w-full gap-2')
        detail_view.set_visibility(False)

        def load_cases():
            case_list.clear()
            detail_view.set_visibility(False)

            if not sb:
                with case_list:
                    ui.label('Database not connected').style('color: #ff6b6b;')
                return

            result = sb.table('case_runs').select('*').order(
                'created_at', desc=True
            ).limit(50).execute()

            if not result.data:
                with case_list:
                    ui.label('No cases run yet. Go to the Pipeline to run your first case!').style(
                        'color: #8888aa;'
                    )
                return

            with case_list:
                for run in result.data:
                    run_id = run['id']
                    patient_info = run.get('patient_info', '')
                    preview = patient_info[:150] + '...' if len(patient_info) > 150 else patient_info
                    mode = run.get('pipeline_mode', '?')
                    backend = run.get('backend', '?')
                    model = run.get('model_name', '?')
                    duration = run.get('duration_seconds', 0)
                    created = run.get('created_at', '')

                    # Parse timestamp
                    try:
                        dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        time_str = dt.strftime('%b %d, %Y %I:%M %p')
                    except Exception:
                        time_str = created[:19] if created else '?'

                    # Get final diagnoses from result
                    res = run.get('result', {})
                    voting = res.get('voting_result', {})
                    if voting and voting.get('ranked'):
                        top_dx = [d[0] if isinstance(d, list) else d for d in voting['ranked'][:3]]
                    elif res.get('final_diagnoses'):
                        top_dx = res['final_diagnoses'][:3]
                    else:
                        top_dx = []

                    # Specialists
                    specialists = run.get('specialists', [])
                    spec_names = [s.get('name', '?') for s in specialists] if specialists else []

                    with ui.card().classes('w-full cursor-pointer').style(
                        'background: #1a1a2e; border: 1px solid #2a2a4a; '
                        'border-radius: 8px; padding: 0;'
                    ).on('click', lambda r=run: show_detail(r)):
                        with ui.column().classes('w-full gap-1 p-4'):
                            with ui.row().classes('w-full items-center justify-between'):
                                ui.label(time_str).style(
                                    'color: #4f8cff; font-weight: 600; font-size: 14px;'
                                )
                                with ui.row().classes('gap-2'):
                                    ui.badge(mode).props('color=primary outline')
                                    ui.badge(f'{duration:.0f}s').props('color=grey outline')

                            ui.label(preview).style(
                                'color: #c0c0d0; font-size: 12px; margin-top: 4px;'
                            )

                            if top_dx:
                                with ui.row().classes('gap-1 flex-wrap').style('margin-top: 6px;'):
                                    for i, dx in enumerate(top_dx, 1):
                                        dx_name = dx if isinstance(dx, str) else str(dx)
                                        ui.html(
                                            f'<span style="background:#1a2a3a;color:#60a5fa;'
                                            f'padding:2px 8px;border-radius:10px;font-size:11px;'
                                            f'font-weight:600;">{i}. {dx_name[:50]}</span>'
                                        )

                            if spec_names:
                                ui.label(
                                    f'Team: {", ".join(spec_names)}'
                                ).style('color: #555577; font-size: 11px; margin-top: 4px;')

        def show_detail(run):
            case_list.set_visibility(False)
            detail_view.clear()
            detail_view.set_visibility(True)

            res = run.get('result', {})
            patient_info = run.get('patient_info', '')
            specialists = run.get('specialists', [])
            mode = run.get('pipeline_mode', '?')
            duration = run.get('duration_seconds', 0)
            model = run.get('model_name', '?')
            backend = run.get('backend', '?')

            with detail_view:
                # Back button
                ui.button('Back to List', icon='arrow_back',
                          on_click=lambda: go_back()).props('flat').style('color: #8888aa;')

                # Case info
                with ui.card().classes('w-full').style(
                    'background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px;'
                ):
                    with ui.column().classes('w-full gap-2 p-4'):
                        ui.label('Case Presentation').style(
                            'color: #4f8cff; font-weight: 700; font-size: 16px;'
                        )
                        ui.label(patient_info).style(
                            'color: #c0c0d0; font-size: 13px; white-space: pre-wrap;'
                        )
                        with ui.row().classes('gap-3').style('margin-top: 8px;'):
                            ui.badge(f'Mode: {mode}').props('color=primary outline')
                            ui.badge(f'Backend: {backend}').props('color=grey outline')
                            ui.badge(f'Model: {model}').props('color=grey outline')
                            ui.badge(f'Duration: {duration:.0f}s').props('color=grey outline')

                # Team
                if specialists:
                    with ui.card().classes('w-full').style(
                        'background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px;'
                    ):
                        with ui.column().classes('w-full gap-1 p-4'):
                            ui.label('Specialist Team').style(
                                'color: #4f8cff; font-weight: 700; font-size: 16px;'
                            )
                            for spec in specialists:
                                name = spec.get('name', '?')
                                specialty = spec.get('specialty', '')
                                with ui.row().classes('items-center gap-2'):
                                    ui.label(name).style('color: #e0e0e0; font-weight: 600; font-size: 13px;')
                                    ui.label(f'({specialty})').style('color: #8888aa; font-size: 12px;')

                # Final Diagnoses
                voting = res.get('voting_result', {})
                if voting and voting.get('ranked'):
                    with ui.card().classes('w-full').style(
                        'background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px;'
                    ):
                        with ui.column().classes('w-full gap-2 p-4'):
                            ui.label('Final Diagnoses').style(
                                'color: #4f8cff; font-weight: 700; font-size: 16px;'
                            )
                            ranked = voting['ranked']
                            max_score = ranked[0][1] if ranked and isinstance(ranked[0], list) else 1
                            for i, item in enumerate(ranked[:6], 1):
                                if isinstance(item, list) and len(item) >= 2:
                                    dx, score = item[0], item[1]
                                else:
                                    dx, score = str(item), 0
                                pct = (score / max_score * 100) if max_score > 0 else 0
                                with ui.row().classes('w-full items-center gap-3'):
                                    ui.html(
                                        f'<div style="background:#4f8cff;color:white;border-radius:50%;'
                                        f'width:24px;height:24px;display:flex;align-items:center;'
                                        f'justify-content:center;font-weight:700;font-size:12px;'
                                        f'flex-shrink:0;">{i}</div>'
                                    )
                                    with ui.column().classes('flex-grow gap-0'):
                                        ui.label(dx).style('color: #e0e0e0; font-size: 13px; font-weight: 600;')
                                        ui.html(
                                            f'<div style="height:3px;background:#333355;border-radius:2px;'
                                            f'overflow:hidden;margin-top:3px;width:100%;">'
                                            f'<div style="height:100%;width:{pct}%;background:#4f8cff;'
                                            f'border-radius:2px;"></div></div>'
                                        )
                                    ui.label(f'{score:.0f}').style(
                                        'color: #4f8cff; font-weight: 600; font-size: 12px; min-width: 40px; text-align: right;'
                                    )

                # Rounds detail
                rounds = res.get('rounds', {})
                if rounds:
                    with ui.card().classes('w-full').style(
                        'background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px;'
                    ):
                        with ui.column().classes('w-full gap-1 p-4'):
                            ui.label('Round Transcripts').style(
                                'color: #4f8cff; font-weight: 700; font-size: 16px;'
                            )
                            for round_name, round_data in rounds.items():
                                responses = round_data.get('responses', [])
                                dur = round_data.get('duration', 0)
                                title = round_name.replace('_', ' ').title()

                                with ui.expansion(
                                    f'{title} — {len(responses)} responses, {dur:.1f}s',
                                    icon='expand_more',
                                ).classes('w-full').style(
                                    'color: #4f8cff; background: rgba(79,140,255,0.04); '
                                    'border: 1px solid #333355; border-radius: 6px; margin: 2px 0; '
                                    'overflow: hidden;'
                                ):
                                    for resp in responses:
                                        agent = resp.get('agent_name', '?')
                                        specialty = resp.get('specialty', '')
                                        conf = resp.get('confidence_score', 0)
                                        content = resp.get('content', '')

                                        with ui.expansion(
                                            f'{agent} ({specialty})', icon='person'
                                        ).classes('w-full').style(
                                            'border-left: 3px solid #4f8cff; '
                                            'background: rgba(79,140,255,0.03); '
                                            'border-radius: 0 6px 6px 0; margin: 2px 0; '
                                            'overflow: hidden;'
                                        ):
                                            conf_color = '#4ecdc4' if conf >= 0.7 else '#ffd166' if conf >= 0.4 else '#ff6b6b'
                                            with ui.row().classes('items-center gap-2').style('margin-bottom: 6px;'):
                                                ui.badge(f'{conf:.0%}').style(
                                                    f'background: {conf_color}; color: #1a1a2e;'
                                                )
                                            ui.markdown(content).style(
                                                'color: #c0c0d0; font-size: 13px; '
                                                'overflow-wrap: break-word; word-break: break-word; '
                                                'max-width: 100%; overflow-x: hidden;'
                                            )

                # Download
                ui.separator().style('border-color: #333355; margin-top: 12px;')

                def download_case(r=run):
                    content = json.dumps(r, indent=2, default=str)
                    ui.download(
                        content.encode(),
                        f'lddx_case_{r.get("created_at", "")[:10]}.json',
                        'application/json',
                    )

                ui.button('Download JSON', icon='download',
                          on_click=download_case).props('flat').style('color: #4f8cff;')

        def go_back():
            detail_view.set_visibility(False)
            case_list.set_visibility(True)

        # Initial load
        load_cases()
        refresh_btn.on_click(load_cases)
