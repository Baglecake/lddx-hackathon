"""
Guiding Assistant — /assistant

AI-powered help chatbot using the same Gemma 4 model on RunPod.
Answers questions about the platform, explains medical terminology,
and helps users navigate the LDDx pipeline.
"""

import os
import sys
import json
import requests
from typing import List, Dict

from nicegui import ui

sys.path.insert(0, os.path.dirname(__file__))

SYSTEM_PROMPT = """You are the LDDx Assistant, a helpful guide for the Local-DDx diagnostic platform.

About the platform:
- Local-DDx is a multi-agent AI system for collaborative differential diagnosis
- It uses "Social Chain of Thought" where multiple AI specialist agents debate diagnoses
- The pipeline has 7 rounds: Specialized Ranking, Symptom Management, Team Differentials, Master List, Refinement & Debate (3 sub-rounds), Preferential Voting, and Can't Miss
- The system runs on Gemma 4, a multimodal AI model from Google
- Results are evaluated using a clinical equivalence engine with synonym matching

About the synonym review:
- Medical students review synonym mappings to improve the evaluation accuracy
- They can join classrooms, vote on whether pipeline outputs match ground truth, and add missing synonyms
- The review has 3 sections: Diagnostic Match Review, Synonym Dictionary Review, and Clinical Hierarchy Review

Your role:
- Answer questions about how the platform works
- Explain medical terminology when asked
- Help users understand differential diagnosis concepts
- Guide users to the right page (Pipeline, History, Review)
- Be concise and friendly

Do NOT:
- Provide actual medical advice or diagnoses
- Claim to be a real doctor
- Make up information about the platform's features

Keep responses brief and helpful — 2-3 sentences when possible."""


def _get_inference_url():
    url = os.environ.get('INFERENCE_URL', '')
    if not url:
        endpoint_id = os.environ.get('RUNPOD_ENDPOINT_ID', '')
        if endpoint_id:
            url = f"https://api.runpod.ai/v2/{endpoint_id}/openai/v1"
    return url


def _chat_completion(messages: List[Dict[str, str]], max_tokens: int = 512) -> str:
    url = _get_inference_url()
    if not url:
        return "I'm not connected to a model right now. Please check the RunPod configuration."

    api_key = os.environ.get('RUNPOD_API_KEY', '')
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.post(
            f"{url}/chat/completions",
            headers=headers,
            json={
                "model": os.environ.get('RUNPOD_MODEL', 'google/gemma-4-26b-a4b-it'),
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        return f"Sorry, I got an error ({resp.status_code}). The model server may be loading."
    except Exception as e:
        return f"Sorry, I couldn't reach the model server: {str(e)[:100]}"


@ui.page('/assistant')
def assistant_page():
    from main import render_nav
    render_nav(active='Assistant')

    # Chat state
    chat_history = []

    with ui.column().classes('w-full max-w-3xl mx-auto gap-0').style(
        'margin-top: 56px; height: calc(100vh - 56px); background: #0f0f23;'
    ):
        # Header
        with ui.row().classes('w-full items-center gap-3 p-4').style(
            'border-bottom: 1px solid #333355;'
        ):
            ui.html(
                '<div style="background:#4f8cff;color:white;border-radius:50%;'
                'width:36px;height:36px;display:flex;align-items:center;'
                'justify-content:center;font-size:18px;">?</div>'
            )
            with ui.column().classes('gap-0'):
                ui.label('LDDx Assistant').style('color: #4f8cff; font-weight: 700; font-size: 16px;')
                ui.label('Ask me anything about the platform').style('color: #8888aa; font-size: 12px;')

        # Chat area
        chat_scroll = ui.scroll_area().classes('w-full flex-grow')
        with chat_scroll:
            chat_container = ui.column().classes('w-full gap-3 p-4')

            # Welcome message
            with chat_container:
                with ui.row().classes('w-full gap-3'):
                    ui.html(
                        '<div style="background:#4f8cff;color:white;border-radius:50%;'
                        'width:32px;height:32px;display:flex;align-items:center;'
                        'justify-content:center;font-size:14px;flex-shrink:0;">A</div>'
                    )
                    ui.markdown(
                        "Hi! I'm the LDDx Assistant. I can help you with:\n\n"
                        "- **How the pipeline works** — the 7-round diagnostic process\n"
                        "- **Navigating the platform** — Pipeline, History, Review pages\n"
                        "- **Medical terminology** — explaining clinical concepts\n"
                        "- **The synonym review** — how to contribute\n\n"
                        "What would you like to know?"
                    ).style('color: #c0c0d0; font-size: 14px;')

        # Input area
        with ui.row().classes('w-full items-center gap-2 p-4').style(
            'border-top: 1px solid #333355;'
        ):
            msg_input = ui.input(placeholder='Ask a question...').classes('flex-grow').props(
                'outlined dense'
            ).style('color: #e0e0e0;')

            async def send_message():
                user_msg = msg_input.value.strip()
                if not user_msg:
                    return

                msg_input.value = ''

                # Show user message
                with chat_container:
                    with ui.row().classes('w-full gap-3 justify-end'):
                        ui.label(user_msg).style(
                            'background: #2d5aa0; color: white; padding: 10px 14px; '
                            'border-radius: 12px 12px 2px 12px; font-size: 14px; '
                            'max-width: 80%;'
                        )

                chat_scroll.scroll_to(percent=1.0)

                # Build messages for API
                chat_history.append({"role": "user", "content": user_msg})
                messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_history[-10:]

                # Show typing indicator
                with chat_container:
                    typing = ui.row().classes('w-full gap-3')
                    with typing:
                        ui.html(
                            '<div style="background:#4f8cff;color:white;border-radius:50%;'
                            'width:32px;height:32px;display:flex;align-items:center;'
                            'justify-content:center;font-size:14px;flex-shrink:0;">A</div>'
                        )
                        typing_label = ui.label('Thinking...').style(
                            'color: #8888aa; font-size: 14px; font-style: italic;'
                        )

                chat_scroll.scroll_to(percent=1.0)

                # Get response
                import asyncio
                response = await asyncio.to_thread(_chat_completion, messages)

                # Remove typing indicator and show response
                chat_container.remove(typing)

                chat_history.append({"role": "assistant", "content": response})

                with chat_container:
                    with ui.row().classes('w-full gap-3'):
                        ui.html(
                            '<div style="background:#4f8cff;color:white;border-radius:50%;'
                            'width:32px;height:32px;display:flex;align-items:center;'
                            'justify-content:center;font-size:14px;flex-shrink:0;">A</div>'
                        )
                        ui.markdown(response).style(
                            'color: #c0c0d0; font-size: 14px; max-width: 80%; '
                            'overflow-wrap: break-word;'
                        )

                chat_scroll.scroll_to(percent=1.0)

            send_btn = ui.button(icon='send', on_click=send_message).props('flat dense').style('color: #4f8cff;')
            msg_input.on('keydown.enter', send_message)
