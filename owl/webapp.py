"""Loopback-only OWL task UI. Credentials are not displayed or editable."""

import logging
import os

import gradio as gr
from owl.providers import PROVIDERS
from owl.runtime import run_task

logger = logging.getLogger(__name__)


def submit(task: str, provider: str, model: str, mode: str) -> str:
    try:
        return run_task(task, provider=provider, model=model.strip() or None, mode=mode)
    except ValueError as exc:
        return f"Configuration error: {exc}"
    except Exception as exc:
        logger.error("OWL run failed: %s", type(exc).__name__)
        return f"Execution failed ({type(exc).__name__}). Check provider connectivity."


def create_ui():
    with gr.Blocks(title="OWL - Local-first Agents") as app:
        gr.Markdown(
            "# OWL\n"
            "Local-first agents using Ollama, Ollama Cloud or Amazon Bedrock. "
            "Cloud requests leave your machine and may incur charges."
        )
        provider = gr.Dropdown(choices=list(PROVIDERS),
                               value=os.getenv("OWL_PROVIDER", "ollama"),
                               label="Model provider")
        model = gr.Textbox(label="Model identifier (optional)",
                           placeholder="Leave blank to use the .env model")
        mode = gr.Radio(choices=["assistant", "workforce"],
                        value="assistant", label="Execution mode")
        task = gr.Textbox(lines=5, label="Task", placeholder="Enter a task in English")
        run = gr.Button("Run", variant="primary")
        output = gr.Textbox(lines=14, label="Result", interactive=False)
        run.click(submit, inputs=[task, provider, model, mode], outputs=output)
        gr.Markdown("No shell, filesystem or browser execution is exposed by this UI. "
                    "Configure credentials in a local .env file, not in the browser.")
    return app


def main():
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    create_ui().queue(default_concurrency_limit=1).launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=port, share=False, show_error=False,
    )


if __name__ == "__main__":
    main()
