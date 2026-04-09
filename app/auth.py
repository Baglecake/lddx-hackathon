"""
Authentication module — login, signup, session management.

Uses Supabase email+password auth. Access tokens stored in NiceGUI app.storage.
"""

import os
import sys
from typing import Optional, Dict

from nicegui import ui, app

sys.path.insert(0, os.path.dirname(__file__))
from supabase_client import get_supabase


def get_current_user() -> Optional[Dict]:
    """Get the current authenticated user from session storage, or None."""
    token = app.storage.user.get('access_token')
    if not token:
        return None

    sb = get_supabase()
    if not sb:
        return None

    try:
        user_resp = sb.auth.get_user(token)
        if user_resp and user_resp.user:
            return {
                'id': user_resp.user.id,
                'email': user_resp.user.email,
            }
    except Exception:
        # Token expired or invalid
        app.storage.user.pop('access_token', None)

    return None


def require_auth():
    """Redirect to login if not authenticated. Call at top of protected pages.

    If Supabase is not configured (local dev), returns a dummy user so the
    app works without auth.
    """
    sb = get_supabase()
    if not sb:
        # No Supabase = local dev mode, skip auth
        return {'id': 'local-user', 'email': 'local'}

    user = get_current_user()
    if not user:
        ui.navigate.to('/login')
        return None
    return user


def get_auth_header() -> Dict[str, str]:
    """Get Authorization header for Supabase RLS queries."""
    token = app.storage.user.get('access_token')
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# ---------------------------------------------------------------------------
# Login Page
# ---------------------------------------------------------------------------

@ui.page('/login')
def login_page():
    from main import render_nav
    render_nav()

    with ui.column().classes('w-full max-w-md mx-auto p-6 gap-4').style(
        'margin-top: 100px;'
    ):
        with ui.card().classes('w-full').style(
            'background: #1a1a2e; border: 1px solid #333355; border-radius: 12px;'
        ):
            with ui.column().classes('w-full gap-4 p-6'):
                ui.label('Sign In').classes('text-2xl font-bold').style('color: #4f8cff;')
                ui.label('Access the LDDx diagnostic platform').style(
                    'color: #8888aa; font-size: 13px; margin-top: -8px;'
                )

                email_input = ui.input(label='Email').classes('w-full').props('type=email')
                password_input = ui.input(label='Password').classes('w-full').props('type=password')

                error_label = ui.label('').style('color: #ff6b6b; font-size: 13px;')
                error_label.set_visibility(False)

                async def do_login():
                    email = email_input.value.strip()
                    password = password_input.value

                    if not email or not password:
                        error_label.text = 'Please enter email and password'
                        error_label.set_visibility(True)
                        return

                    sb = get_supabase()
                    if not sb:
                        error_label.text = 'Database not connected'
                        error_label.set_visibility(True)
                        return

                    try:
                        result = sb.auth.sign_in_with_password({
                            "email": email,
                            "password": password,
                        })

                        if result.session:
                            app.storage.user['access_token'] = result.session.access_token
                            app.storage.user['user_email'] = result.user.email
                            app.storage.user['user_id'] = str(result.user.id)
                            ui.navigate.to('/dashboard')
                        else:
                            error_label.text = 'Login failed'
                            error_label.set_visibility(True)

                    except Exception as e:
                        msg = str(e)
                        if 'Invalid login' in msg or 'invalid' in msg.lower():
                            error_label.text = 'Invalid email or password'
                        elif 'Email not confirmed' in msg:
                            error_label.text = 'Please check your email to confirm your account'
                        else:
                            error_label.text = f'Error: {msg[:100]}'
                        error_label.set_visibility(True)

                ui.button('Sign In', on_click=do_login).classes('w-full').props('color=primary size=lg')
                password_input.on('keydown.enter', do_login)

                ui.separator().style('border-color: #333355;')

                with ui.row().classes('w-full justify-center gap-1'):
                    ui.label("Don't have an account?").style('color: #8888aa; font-size: 13px;')
                    ui.link('Sign up', '/signup').style('color: #4f8cff; font-size: 13px;')


# ---------------------------------------------------------------------------
# Signup Page
# ---------------------------------------------------------------------------

@ui.page('/signup')
def signup_page():
    from main import render_nav
    render_nav()

    with ui.column().classes('w-full max-w-md mx-auto p-6 gap-4').style(
        'margin-top: 100px;'
    ):
        with ui.card().classes('w-full').style(
            'background: #1a1a2e; border: 1px solid #333355; border-radius: 12px;'
        ):
            with ui.column().classes('w-full gap-4 p-6'):
                ui.label('Create Account').classes('text-2xl font-bold').style('color: #4f8cff;')
                ui.label('Join the LDDx diagnostic platform').style(
                    'color: #8888aa; font-size: 13px; margin-top: -8px;'
                )

                email_input = ui.input(label='Email').classes('w-full').props('type=email')
                password_input = ui.input(label='Password (min 6 characters)').classes('w-full').props(
                    'type=password'
                )
                confirm_input = ui.input(label='Confirm Password').classes('w-full').props(
                    'type=password'
                )

                error_label = ui.label('').style('color: #ff6b6b; font-size: 13px;')
                error_label.set_visibility(False)
                success_label = ui.label('').style('color: #4ecdc4; font-size: 13px;')
                success_label.set_visibility(False)

                async def do_signup():
                    email = email_input.value.strip()
                    password = password_input.value
                    confirm = confirm_input.value

                    error_label.set_visibility(False)
                    success_label.set_visibility(False)

                    if not email or not password:
                        error_label.text = 'Please fill in all fields'
                        error_label.set_visibility(True)
                        return

                    if len(password) < 6:
                        error_label.text = 'Password must be at least 6 characters'
                        error_label.set_visibility(True)
                        return

                    if password != confirm:
                        error_label.text = 'Passwords do not match'
                        error_label.set_visibility(True)
                        return

                    sb = get_supabase()
                    if not sb:
                        error_label.text = 'Database not connected'
                        error_label.set_visibility(True)
                        return

                    try:
                        result = sb.auth.sign_up({
                            "email": email,
                            "password": password,
                        })

                        if result.user:
                            success_label.text = (
                                'Account created! Check your email to confirm, then sign in.'
                            )
                            success_label.set_visibility(True)
                        else:
                            error_label.text = 'Signup failed'
                            error_label.set_visibility(True)

                    except Exception as e:
                        msg = str(e)
                        if 'already registered' in msg.lower():
                            error_label.text = 'This email is already registered'
                        else:
                            error_label.text = f'Error: {msg[:100]}'
                        error_label.set_visibility(True)

                ui.button('Create Account', on_click=do_signup).classes('w-full').props('color=primary size=lg')
                confirm_input.on('keydown.enter', do_signup)

                ui.separator().style('border-color: #333355;')

                with ui.row().classes('w-full justify-center gap-1'):
                    ui.label('Already have an account?').style('color: #8888aa; font-size: 13px;')
                    ui.link('Sign in', '/login').style('color: #4f8cff; font-size: 13px;')
