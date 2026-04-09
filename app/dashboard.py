"""
User Dashboard — /dashboard

Shows the user's classrooms and recent case history at a glance.
"""

import os
import sys
from datetime import datetime

from nicegui import ui, app

sys.path.insert(0, os.path.dirname(__file__))
from supabase_client import get_supabase


@ui.page('/dashboard')
def dashboard_page():
    from auth import require_auth
    user = require_auth()
    if not user:
        return

    from main import render_nav
    render_nav(active='Dashboard')

    sb = get_supabase()

    with ui.column().classes('w-full max-w-4xl mx-auto p-4 gap-4').style(
        'margin-top: 56px; background: #0f0f23; min-height: calc(100vh - 56px);'
    ):
        ui.label(f'Welcome back').classes('text-2xl font-bold').style('color: #4f8cff;')
        ui.label(user['email']).style('color: #8888aa; font-size: 14px; margin-top: -8px;')

        # ============================================================
        # My Classrooms
        # ============================================================
        with ui.card().classes('w-full').style(
            'background: #1a1a2e; border: 1px solid #333355; border-radius: 10px;'
        ):
            with ui.column().classes('w-full gap-3 p-4'):
                with ui.row().classes('w-full items-center justify-between'):
                    ui.label('My Classrooms').style(
                        'color: #4ecdc4; font-weight: 700; font-size: 16px;'
                    )
                    ui.button('Join / Create', icon='add',
                              on_click=lambda: ui.navigate.to('/review')).props(
                        'flat size=sm'
                    ).style('color: #4ecdc4;')

                classrooms_container = ui.column().classes('w-full gap-2')

                def load_classrooms():
                    classrooms_container.clear()
                    if not sb:
                        return

                    # Find classrooms this user's reviewers belong to
                    # Check by email prefix and also by any name stored in review_session
                    search_names = {user['email'].split('@')[0]}
                    saved = app.storage.user.get('review_session')
                    if saved and saved.get('name'):
                        search_names.add(saved['name'])

                    seen_ids = set()
                    classrooms = []

                    for sname in search_names:
                        reviewers = sb.table('reviewers').select(
                            'id, classroom_id, classrooms!reviewers_classroom_id_fkey(id, name, join_code, created_at)'
                        ).eq('name', sname).execute()

                        for r in (reviewers.data or []):
                            cr = r.get('classrooms')
                            if cr and isinstance(cr, dict) and cr.get('id') not in seen_ids:
                                seen_ids.add(cr['id'])
                                cr['_reviewer_id'] = r['id']
                                cr['_reviewer_name'] = sname
                                # Count members
                                try:
                                    mc = sb.table('reviewers').select('id', count='exact').eq(
                                        'classroom_id', cr['id']
                                    ).execute()
                                    cr['member_count'] = mc.count if mc.count else 0
                                except Exception:
                                    cr['member_count'] = 0
                                classrooms.append(cr)

                    if not classrooms:
                        with classrooms_container:
                            ui.label(
                                'No classrooms yet. Join or create one from the Review page.'
                            ).style('color: #666; font-size: 13px;')
                        return

                    with classrooms_container:
                        for cr in classrooms:
                            with ui.row().classes('w-full items-center gap-3 p-3').style(
                                'background: rgba(78, 205, 196, 0.06); '
                                'border: 1px solid rgba(78, 205, 196, 0.2); '
                                'border-radius: 8px;'
                            ):
                                ui.html(
                                    '<div style="background:#4ecdc4;color:#1a1a2e;border-radius:50%;'
                                    'width:32px;height:32px;display:flex;align-items:center;'
                                    'justify-content:center;font-weight:700;font-size:14px;'
                                    f'flex-shrink:0;">{cr["member_count"]}</div>'
                                )
                                with ui.column().classes('flex-grow gap-0'):
                                    ui.label(cr['name']).style(
                                        'color: #e0e0e0; font-weight: 600; font-size: 14px;'
                                    )
                                    with ui.row().classes('gap-2'):
                                        ui.label(f'Code: {cr["join_code"]}').style(
                                            'color: #8888aa; font-size: 12px;'
                                        )
                                        ui.label(
                                            f'{cr["member_count"]} member{"s" if cr["member_count"] != 1 else ""}'
                                        ).style('color: #666; font-size: 12px;')

                                def _enter(c=cr):
                                    # Set session so /review auto-joins this classroom
                                    app.storage.user['review_session'] = {
                                        'reviewer_id': c['_reviewer_id'],
                                        'name': c['_reviewer_name'],
                                        'classroom_id': c['id'],
                                        'classroom_name': c['name'],
                                    }
                                    ui.navigate.to('/review')

                                ui.button('Enter', on_click=_enter).props(
                                    'flat size=sm'
                                ).style('color: #4ecdc4;')

                load_classrooms()

        # ============================================================
        # Recent Cases
        # ============================================================
        with ui.card().classes('w-full').style(
            'background: #1a1a2e; border: 1px solid #333355; border-radius: 10px;'
        ):
            with ui.column().classes('w-full gap-3 p-4'):
                with ui.row().classes('w-full items-center justify-between'):
                    ui.label('Recent Cases').style(
                        'color: #ffd166; font-weight: 700; font-size: 16px;'
                    )
                    ui.button('View All', icon='history',
                              on_click=lambda: ui.navigate.to('/history')).props(
                        'flat size=sm'
                    ).style('color: #ffd166;')

                cases_container = ui.column().classes('w-full gap-2')

                def load_cases():
                    cases_container.clear()
                    if not sb:
                        return

                    result = sb.table('case_runs').select('*').eq(
                        'user_id', user['id']
                    ).order('created_at', desc=True).limit(5).execute()

                    if not result.data:
                        with cases_container:
                            ui.label(
                                'No cases yet. Run your first diagnosis from the Pipeline.'
                            ).style('color: #666; font-size: 13px;')
                        return

                    with cases_container:
                        for run in result.data:
                            patient = run.get('patient_info', '')
                            preview = patient[:120] + '...' if len(patient) > 120 else patient
                            mode = run.get('pipeline_mode', '?')
                            duration = run.get('duration_seconds', 0)
                            created = run.get('created_at', '')

                            try:
                                dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                                time_str = dt.strftime('%b %d, %I:%M %p')
                            except Exception:
                                time_str = created[:16] if created else '?'

                            # Top diagnosis
                            res = run.get('result', {})
                            voting = res.get('voting_result', {})
                            top_dx = ''
                            if voting and voting.get('ranked'):
                                item = voting['ranked'][0]
                                top_dx = item[0] if isinstance(item, list) else str(item)

                            with ui.row().classes('w-full items-center gap-3 p-3').style(
                                'background: rgba(255, 209, 102, 0.04); '
                                'border: 1px solid rgba(255, 209, 102, 0.15); '
                                'border-radius: 8px; cursor: pointer;'
                            ).on('click', lambda: ui.navigate.to('/history')):
                                with ui.column().classes('flex-grow gap-0'):
                                    with ui.row().classes('items-center gap-2'):
                                        ui.label(time_str).style(
                                            'color: #ffd166; font-weight: 600; font-size: 12px;'
                                        )
                                        ui.badge(mode).props('color=grey outline')
                                        ui.badge(f'{duration:.0f}s').props('color=grey outline')
                                    ui.label(preview).style(
                                        'color: #999; font-size: 11px; margin-top: 2px;'
                                    )
                                    if top_dx:
                                        ui.label(f'Top: {top_dx}').style(
                                            'color: #60a5fa; font-size: 12px; font-weight: 600; margin-top: 2px;'
                                        )

                load_cases()

        # ============================================================
        # Quick Actions
        # ============================================================
        with ui.row().classes('w-full gap-3 justify-center'):
            ui.button('Run Pipeline', icon='play_arrow',
                      on_click=lambda: ui.navigate.to('/pipeline')).props('color=primary size=lg')
            ui.button('Synonym Review', icon='rate_review',
                      on_click=lambda: ui.navigate.to('/review')).props('flat size=lg').style('color: #4ecdc4;')
            ui.button('User Guide', icon='menu_book',
                      on_click=lambda: ui.navigate.to('/guide')).props('flat size=lg').style('color: #8888aa;')
