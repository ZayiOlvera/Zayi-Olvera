"""
Claude tool definitions and dispatch handler.
All tools callable by Claude during the agent loop.
"""
from __future__ import annotations

import json
from typing import Any

import resolve_client
import analyzer

# ---------------------------------------------------------------------------
# Tool schemas (Claude API format)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_project_info",
        "description": (
            "Obtiene información del proyecto actual de DaVinci Resolve: "
            "nombre, FPS, resolución, lista de timelines y timeline activo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "list_media_pool_clips",
        "description": (
            "Lista todos los clips importados en el Media Pool de DaVinci Resolve, "
            "con nombre, ruta de archivo, duración y tipo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_timeline_items",
        "description": (
            "Lista todos los clips colocados en el timeline actual, "
            "con nombre, track, tiempo de inicio, fin y duración."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "create_timeline",
        "description": "Crea un nuevo timeline vacío en DaVinci Resolve y lo activa.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nombre del nuevo timeline.",
                },
                "fps": {
                    "type": "number",
                    "description": "Frames por segundo. Si se omite, usa el FPS del proyecto.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "set_current_timeline",
        "description": "Cambia el timeline activo en DaVinci Resolve por nombre.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nombre exacto del timeline.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "add_clip_to_timeline",
        "description": (
            "Agrega un clip del Media Pool al timeline activo. "
            "Puedes especificar el punto de entrada y salida dentro del clip fuente (trim)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "clip_name": {
                    "type": "string",
                    "description": "Nombre del clip en el Media Pool (búsqueda parcial permitida).",
                },
                "in_point_sec": {
                    "type": "number",
                    "description": "Punto de entrada en el clip fuente, en segundos. Default: 0.",
                },
                "out_point_sec": {
                    "type": "number",
                    "description": "Punto de salida en el clip fuente, en segundos. Default: duración total.",
                },
            },
            "required": ["clip_name"],
        },
    },
    {
        "name": "trim_timeline_item",
        "description": (
            "Recorta (trim) un clip en el timeline ajustando sus puntos de entrada y salida. "
            "Usa get_timeline_items para obtener el índice del clip."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_index": {
                    "type": "integer",
                    "description": "Índice del clip en el timeline (0-based, orden de aparición).",
                },
                "new_in_sec": {
                    "type": "number",
                    "description": "Nuevo punto de entrada dentro del clip fuente, en segundos.",
                },
                "new_out_sec": {
                    "type": "number",
                    "description": "Nuevo punto de salida dentro del clip fuente, en segundos.",
                },
            },
            "required": ["item_index", "new_in_sec", "new_out_sec"],
        },
    },
    {
        "name": "split_clip",
        "description": "Divide un clip en el timeline en la posición de tiempo indicada (corte).",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_sec": {
                    "type": "number",
                    "description": "Posición en segundos donde se hace el corte.",
                },
            },
            "required": ["time_sec"],
        },
    },
    {
        "name": "delete_timeline_item",
        "description": "Elimina un clip del timeline por su índice. Esta acción no se puede deshacer desde el agente.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_index": {
                    "type": "integer",
                    "description": "Índice del clip en el timeline (0-based).",
                },
            },
            "required": ["item_index"],
        },
    },
    {
        "name": "move_playhead",
        "description": "Mueve el playhead del timeline a una posición de tiempo específica.",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_sec": {
                    "type": "number",
                    "description": "Posición en segundos.",
                },
            },
            "required": ["time_sec"],
        },
    },
    {
        "name": "adjust_color",
        "description": (
            "Aplica corrección de color a un clip del timeline: lift, gamma, gain, saturación y contraste. "
            "Valores neutros: lift=0, gamma=0, gain=0, saturation=1.0, contrast=1.0."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_index": {
                    "type": "integer",
                    "description": "Índice del clip en el timeline (0-based).",
                },
                "lift": {
                    "type": "number",
                    "description": "Ajuste de sombras. Rango típico: -0.2 a 0.2. 0 = sin cambio.",
                },
                "gamma": {
                    "type": "number",
                    "description": "Ajuste de medios tonos. Rango típico: -0.2 a 0.2.",
                },
                "gain": {
                    "type": "number",
                    "description": "Ajuste de luces. Rango típico: -0.2 a 0.2.",
                },
                "saturation": {
                    "type": "number",
                    "description": "Saturación. 1.0 = normal, 0 = blanco/negro, 2.0 = doble.",
                },
                "contrast": {
                    "type": "number",
                    "description": "Contraste. 1.0 = normal.",
                },
            },
            "required": ["item_index"],
        },
    },
    {
        "name": "set_audio_volume",
        "description": "Ajusta el volumen de audio de un clip en el timeline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_index": {
                    "type": "integer",
                    "description": "Índice del clip en el timeline (0-based).",
                },
                "volume_db": {
                    "type": "number",
                    "description": "Volumen en dB. 0 = original, -6 = mitad, -inf = silencio.",
                },
            },
            "required": ["item_index", "volume_db"],
        },
    },
    {
        "name": "add_text_title",
        "description": (
            "Agrega un título de texto (Fusion Text+) al timeline en un tiempo y duración dados. "
            "Requiere DaVinci Resolve Studio para funcionalidad completa de Fusion."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Contenido del texto.",
                },
                "start_sec": {
                    "type": "number",
                    "description": "Tiempo de inicio en el timeline, en segundos.",
                },
                "duration_sec": {
                    "type": "number",
                    "description": "Duración del título en segundos.",
                },
                "x": {
                    "type": "number",
                    "description": "Posición horizontal normalizada (0=izquierda, 0.5=centro, 1=derecha). Default: 0.5",
                },
                "y": {
                    "type": "number",
                    "description": "Posición vertical normalizada (0=arriba, 1=abajo). Default: 0.85",
                },
                "font_size": {
                    "type": "integer",
                    "description": "Tamaño de fuente en puntos. Default: 72",
                },
                "color": {
                    "type": "string",
                    "description": "Color en hexadecimal, ej: '#FFFFFF'. Default: blanco.",
                },
                "font_family": {
                    "type": "string",
                    "description": "Familia tipográfica, ej: 'Arial', 'Helvetica'. Default: Arial.",
                },
                "bold": {
                    "type": "boolean",
                    "description": "Negrita. Default: true.",
                },
            },
            "required": ["text", "start_sec", "duration_sec"],
        },
    },
    {
        "name": "render_project",
        "description": (
            "Exporta/renderiza el timeline actual usando un preset de render de DaVinci Resolve. "
            "Usa get_project_info para ver los presets disponibles."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "output_path": {
                    "type": "string",
                    "description": "Ruta del archivo de salida, ej: '~/Movies/mi_video.mp4'",
                },
                "preset_name": {
                    "type": "string",
                    "description": "Nombre del render preset en Resolve. Default: 'H.264 Master'.",
                },
            },
            "required": ["output_path"],
        },
    },
    # -----------------------------------------------------------------------
    # Analysis tools
    # -----------------------------------------------------------------------
    {
        "name": "transcribe_clip",
        "description": (
            "Transcribe el audio de un clip usando Whisper (IA de reconocimiento de voz). "
            "Devuelve el texto con timestamps. Útil para editar entrevistas o narración."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "clip_name": {
                    "type": "string",
                    "description": "Nombre del clip en el Media Pool.",
                },
                "language": {
                    "type": "string",
                    "description": "Código de idioma, ej: 'es', 'en'. Se auto-detecta si se omite.",
                },
            },
            "required": ["clip_name"],
        },
    },
    {
        "name": "detect_scene_cuts",
        "description": (
            "Detecta automáticamente los cortes/cambios de escena en un clip de video. "
            "Útil para analizar material en bruto o referencias."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "clip_name": {
                    "type": "string",
                    "description": "Nombre del clip en el Media Pool.",
                },
            },
            "required": ["clip_name"],
        },
    },
    {
        "name": "get_audio_levels",
        "description": (
            "Analiza los niveles de audio (pico y RMS en dB) de un clip. "
            "Útil para identificar clips con audio muy bajo, muy alto o con mucho silencio."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "clip_name": {
                    "type": "string",
                    "description": "Nombre del clip en el Media Pool.",
                },
            },
            "required": ["clip_name"],
        },
    },
    {
        "name": "analyze_reference_video",
        "description": (
            "Analiza un video de referencia (MP4/MOV) para extraer su estilo de edición: "
            "ritmo de cortes, temperatura de color, saturación y brillo. "
            "Recibe la ruta completa del archivo en tu Mac."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Ruta absoluta al video de referencia, ej: '/Users/zayi/Desktop/ref.mp4'",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "auto_edit_interview",
        "description": (
            "Flujo de edición automática de entrevista: transcribe el clip, identifica silencios y "
            "muletillas, y agrega al timeline solo los segmentos buenos. "
            "Crea un nuevo timeline si se especifica un nombre."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "clip_name": {
                    "type": "string",
                    "description": "Nombre del clip de entrevista en el Media Pool.",
                },
                "timeline_name": {
                    "type": "string",
                    "description": "Nombre del timeline donde colocar los segmentos. Si no existe, se crea.",
                },
            },
            "required": ["clip_name"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

def handle_tool_call(tool_name: str, tool_input: dict) -> Any:
    """Execute a tool and return a JSON-serializable result."""
    try:
        return _dispatch(tool_name, tool_input)
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _dispatch(tool_name: str, inp: dict) -> Any:
    # --- Resolve info ---
    if tool_name == "get_project_info":
        return resolve_client.get_project_info()

    if tool_name == "list_media_pool_clips":
        return resolve_client.list_media_pool_clips()

    if tool_name == "get_timeline_items":
        return resolve_client.get_timeline_items()

    # --- Timeline management ---
    if tool_name == "create_timeline":
        return resolve_client.create_timeline(inp["name"], inp.get("fps"))

    if tool_name == "set_current_timeline":
        return resolve_client.set_current_timeline(inp["name"])

    # --- Clip editing ---
    if tool_name == "add_clip_to_timeline":
        return resolve_client.add_clip_to_timeline(
            clip_name=inp["clip_name"],
            in_point_sec=inp.get("in_point_sec", 0.0),
            out_point_sec=inp.get("out_point_sec"),
        )

    if tool_name == "trim_timeline_item":
        return resolve_client.trim_timeline_item(
            item_index=inp["item_index"],
            new_in_sec=inp["new_in_sec"],
            new_out_sec=inp["new_out_sec"],
        )

    if tool_name == "split_clip":
        return resolve_client.split_clip(inp["time_sec"])

    if tool_name == "delete_timeline_item":
        return resolve_client.delete_timeline_item(inp["item_index"])

    if tool_name == "move_playhead":
        return resolve_client.move_playhead(inp["time_sec"])

    # --- Color & audio ---
    if tool_name == "adjust_color":
        return resolve_client.adjust_color(
            item_index=inp["item_index"],
            lift=inp.get("lift"),
            gamma=inp.get("gamma"),
            gain=inp.get("gain"),
            saturation=inp.get("saturation"),
            contrast=inp.get("contrast"),
        )

    if tool_name == "set_audio_volume":
        return resolve_client.set_audio_volume(
            item_index=inp["item_index"],
            volume_db=inp["volume_db"],
        )

    if tool_name == "add_text_title":
        return resolve_client.add_text_title(
            text=inp["text"],
            start_sec=inp["start_sec"],
            duration_sec=inp["duration_sec"],
            x=inp.get("x", 0.5),
            y=inp.get("y", 0.85),
            font_size=inp.get("font_size", 72),
            color=inp.get("color", "#FFFFFF"),
            font_family=inp.get("font_family", "Arial"),
            bold=inp.get("bold", True),
        )

    if tool_name == "render_project":
        import os
        output = os.path.expanduser(inp["output_path"])
        return resolve_client.render_project(
            output_path=output,
            preset_name=inp.get("preset_name", "H.264 Master"),
        )

    # --- Analysis ---
    if tool_name == "transcribe_clip":
        file_path = resolve_client.get_clip_path(inp["clip_name"])
        if file_path is None:
            return {"success": False, "error": f"Clip '{inp['clip_name']}' no encontrado en Media Pool."}
        return analyzer.transcribe_clip(file_path, language=inp.get("language"))

    if tool_name == "detect_scene_cuts":
        file_path = resolve_client.get_clip_path(inp["clip_name"])
        if file_path is None:
            return {"success": False, "error": f"Clip '{inp['clip_name']}' no encontrado en Media Pool."}
        return analyzer.detect_scene_cuts(file_path)

    if tool_name == "get_audio_levels":
        file_path = resolve_client.get_clip_path(inp["clip_name"])
        if file_path is None:
            return {"success": False, "error": f"Clip '{inp['clip_name']}' no encontrado en Media Pool."}
        return analyzer.get_audio_levels(file_path)

    if tool_name == "analyze_reference_video":
        import os
        return analyzer.analyze_reference_video(os.path.expanduser(inp["file_path"]))

    # --- Compound: auto-edit interview ---
    if tool_name == "auto_edit_interview":
        return _auto_edit_interview(inp)

    return {"success": False, "error": f"Herramienta desconocida: {tool_name}"}


def _auto_edit_interview(inp: dict) -> dict:
    """
    Compound tool: transcribe → filter → build timeline automatically.
    """
    import os
    clip_name = inp["clip_name"]
    timeline_name = inp.get("timeline_name", f"Auto_{clip_name}")

    # 1. Get file path
    file_path = resolve_client.get_clip_path(clip_name)
    if file_path is None:
        return {"success": False, "error": f"Clip '{clip_name}' no encontrado en Media Pool."}

    # 2. Transcribe
    tx = analyzer.transcribe_clip(file_path)
    if not tx["success"]:
        return tx
    segments = tx["segments"]
    total_duration = tx["duration_sec"]

    # 3. Find fillers
    fillers = analyzer.find_filler_segments(segments)

    # 4. Compute keep ranges
    keep_ranges = analyzer.compute_keep_ranges(segments, fillers, total_duration)

    # 5. Create / switch timeline
    info = resolve_client.get_project_info()
    if timeline_name not in info.get("timelines", []):
        resolve_client.create_timeline(timeline_name)
    else:
        resolve_client.set_current_timeline(timeline_name)

    # 6. Add segments
    added = 0
    for rng in keep_ranges:
        result = resolve_client.add_clip_to_timeline(
            clip_name=clip_name,
            in_point_sec=rng["start"],
            out_point_sec=rng["end"],
        )
        if result.get("success"):
            added += 1

    removed_duration = sum(
        (s["end"] - s["start"]) for s in fillers
    )
    kept_duration = sum(r["end"] - r["start"] for r in keep_ranges)

    return {
        "success": True,
        "timeline": timeline_name,
        "segments_added": added,
        "kept_duration_sec": round(kept_duration, 2),
        "removed_duration_sec": round(removed_duration, 2),
        "fillers_removed": len(fillers),
        "transcript_language": tx.get("language"),
        "message": (
            f"Timeline '{timeline_name}' creado con {added} segmentos. "
            f"Duración total: {_fmt(kept_duration)}. "
            f"Se eliminaron {_fmt(removed_duration)} de silencios/muletillas."
        ),
    }


def _fmt(sec: float) -> str:
    m = int(sec) // 60
    s = int(sec) % 60
    return f"{m}:{s:02d}"
