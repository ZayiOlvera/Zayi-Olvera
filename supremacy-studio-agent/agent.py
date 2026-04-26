#!/usr/bin/env python3
"""
Supremacy Studios — DaVinci Resolve AI Agent
CLI chat loop powered by Claude with tool use.

Usage:
  python agent.py

Requirements:
  - DaVinci Resolve open on macOS
  - ANTHROPIC_API_KEY environment variable set
  - Dependencies installed: pip install -r requirements.txt
"""
from __future__ import annotations

import json
import os
import sys
from typing import Optional

# ---------------------------------------------------------------------------
# Bootstrap check
# ---------------------------------------------------------------------------

def _check_requirements():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n[ERROR] ANTHROPIC_API_KEY no está configurada.")
        print("Ejecuta: export ANTHROPIC_API_KEY='sk-ant-...'")
        sys.exit(1)

_check_requirements()

import anthropic
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

import config
import tools as tool_module

console = Console()

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Eres el agente de edición de video de Supremacy Studios, un editor experto que controla DaVinci Resolve directamente a través de su API de scripting.

## Tu rol
Ayudas al editor de video de Supremacy Studios a editar videos de forma eficiente usando lenguaje natural. Tienes acceso a herramientas que te permiten:
- Ver y gestionar el material en el Media Pool
- Crear y manipular timelines
- Agregar, cortar, trim y eliminar clips
- Aplicar corrección de color
- Ajustar el audio
- Agregar títulos y texto
- Transcribir entrevistas y eliminar silencios/muletillas automáticamente
- Analizar videos de referencia para replicar su estilo
- Exportar/renderizar el proyecto

## Cómo trabajar
1. Cuando el usuario te dé una instrucción, usa las herramientas disponibles para ejecutarla paso a paso
2. Siempre confirma lo que hiciste después de ejecutar acciones
3. Para operaciones destructivas (eliminar clips, sobreescribir renders), menciona lo que vas a hacer ANTES de hacerlo y espera confirmación si hay duda
4. Si una herramienta falla, explica el error claramente y sugiere alternativas
5. Cuando analices material, presenta la información de forma concisa y útil
6. Habla en español a menos que el usuario cambie el idioma

## Contexto del proyecto
- El editor usa DaVinci Resolve en macOS
- El material ya está importado en el proyecto de Resolve
- Las referencias de estilo se proporcionan como archivos MP4/MOV en la Mac del usuario
- El objetivo es editar videos de 0 a 100: desde el material en bruto hasta el export final

## Limitaciones conocidas
- split_clip() requiere Resolve 18 o superior
- add_text_title() requiere Resolve Studio para Fusion completo
- adjust_color() a través de API puede estar limitado según la versión de Resolve
- DaVinci Resolve debe estar abierto para que cualquier herramienta funcione

Cuando encuentres una limitación de la API, siempre sugiere la alternativa manual en Resolve."""


# ---------------------------------------------------------------------------
# Claude client with tool use + prompt caching
# ---------------------------------------------------------------------------

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

# Cached system prompt
CACHED_SYSTEM = [
    {
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }
]

# Cached tool definitions
CACHED_TOOLS = [
    {**tool, "cache_control": {"type": "ephemeral"}}
    if i == len(tool_module.TOOL_DEFINITIONS) - 1
    else tool
    for i, tool in enumerate(tool_module.TOOL_DEFINITIONS)
]


def run_agent_turn(messages: list[dict]) -> tuple[str, list[dict]]:
    """
    Send messages to Claude, handle tool calls in a loop, return final text response.
    Returns (final_text, updated_messages).
    """
    while True:
        with Progress(
            SpinnerColumn(style="bold red"),
            TextColumn("[dim]Pensando...[/dim]"),
            transient=True,
            console=console,
        ) as progress:
            progress.add_task("", total=None)
            response = client.beta.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=4096,
                system=CACHED_SYSTEM,
                tools=CACHED_TOOLS,
                messages=messages,
                betas=["prompt-caching-2024-07-31"],
            )

        # Collect assistant content blocks
        assistant_content = []
        tool_calls = []
        text_parts = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                tool_calls.append(block)
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        messages.append({"role": "assistant", "content": assistant_content})

        # No tool calls → we're done
        if not tool_calls or response.stop_reason == "end_turn":
            return "\n".join(text_parts), messages

        # Execute tool calls
        tool_results = []
        for tc in tool_calls:
            _print_tool_call(tc.name, tc.input)
            result = _execute_tool(tc.name, tc.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        messages.append({"role": "user", "content": tool_results})


def _execute_tool(name: str, input_data: dict) -> dict:
    with Progress(
        SpinnerColumn(style="yellow"),
        TextColumn(f"[dim]Ejecutando [bold]{name}[/bold]...[/dim]"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task("", total=None)
        return tool_module.handle_tool_call(name, input_data)


def _print_tool_call(name: str, input_data: dict):
    params = ", ".join(f"{k}={repr(v)}" for k, v in input_data.items())
    console.print(f"  [dim cyan]→ {name}({params})[/dim cyan]")


# ---------------------------------------------------------------------------
# CLI loop
# ---------------------------------------------------------------------------

WELCOME_BANNER = """
╔══════════════════════════════════════════════════════╗
║       SUPREMACY STUDIOS — AI VIDEO EDITOR            ║
║       Controlando DaVinci Resolve via scripting      ║
╚══════════════════════════════════════════════════════╝
[dim]Escribe tu instrucción de edición en español.
Comandos: /salir  /limpiar  /historial  /ayuda[/dim]
"""


def main():
    console.print(WELCOME_BANNER, style="bold red")

    # Verify Resolve is accessible
    console.print("[dim]Verificando conexión con DaVinci Resolve...[/dim]")
    try:
        import resolve_client
        info = resolve_client.get_project_info()
        console.print(
            f"[green]✓ Conectado a Resolve[/green] — Proyecto: [bold]{info['project_name']}[/bold]  "
            f"FPS: {info['fps']}  Resolución: {info['resolution']}"
        )
        if info.get("current_timeline"):
            console.print(f"  Timeline activo: [bold]{info['current_timeline']}[/bold]")
    except Exception as exc:
        console.print(f"[yellow]⚠ Resolve no disponible:[/yellow] {exc}")
        console.print("[dim]Puedes seguir usando el agente para análisis de archivos locales.[/dim]")

    console.print()

    messages: list[dict] = []

    while True:
        try:
            user_input = console.input("[bold red]Tú:[/bold red] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Hasta luego.[/dim]")
            break

        if not user_input:
            continue

        # Built-in commands
        if user_input.lower() in ("/salir", "/exit", "/quit"):
            console.print("[dim]Hasta luego.[/dim]")
            break

        if user_input.lower() in ("/limpiar", "/clear"):
            messages.clear()
            console.clear()
            console.print(WELCOME_BANNER, style="bold red")
            console.print("[dim]Historial limpiado.[/dim]")
            continue

        if user_input.lower() in ("/historial", "/history"):
            console.print(f"[dim]{len(messages)} mensajes en el historial.[/dim]")
            continue

        if user_input.lower() in ("/ayuda", "/help"):
            _print_help()
            continue

        # Add user message
        messages.append({"role": "user", "content": user_input})

        try:
            response_text, messages = run_agent_turn(messages)
        except anthropic.APIError as exc:
            console.print(f"[red]Error de API:[/red] {exc}")
            messages.pop()  # remove the failed user message
            continue
        except Exception as exc:
            console.print(f"[red]Error inesperado:[/red] {exc}")
            messages.pop()
            continue

        console.print()
        console.print("[bold red]Agente:[/bold red]")
        console.print(Markdown(response_text))
        console.print()


def _print_help():
    help_text = """
## Comandos disponibles
- `/salir` — Salir del agente
- `/limpiar` — Limpiar el historial de conversación
- `/historial` — Ver cuántos mensajes hay en el historial

## Ejemplos de instrucciones
- `¿Qué material tengo en el proyecto?`
- `Transcribe el clip Interview_01.mp4`
- `Edita la entrevista quitando silencios y muletillas, ponla en un timeline llamado "Corte_limpio"`
- `Analiza la referencia en ~/Desktop/referencia.mp4`
- `Aplica el look de la referencia a todos los clips del timeline`
- `Agrega el clip BRoll_oficina del segundo 5 al 30 al final del timeline`
- `Divide el clip en la posición 1:23`
- `Ajusta el volumen del clip 0 a -3 dB`
- `Exporta el timeline actual en H.264 1080p`
"""
    console.print(Markdown(help_text))


if __name__ == "__main__":
    main()
