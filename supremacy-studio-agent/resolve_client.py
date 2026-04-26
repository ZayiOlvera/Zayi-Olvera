"""
DaVinci Resolve Python API wrapper.
Requires DaVinci Resolve to be open and running on macOS.
"""
import sys
import os
from typing import Optional

import config


def _load_resolve_module():
    path = config.RESOLVE_SCRIPT_MODULE_PATH
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        import DaVinciResolveScript as dvr  # type: ignore
        return dvr
    except ImportError:
        return None


def connect() -> tuple:
    """
    Returns (resolve, project, media_pool, timeline) or raises RuntimeError.
    """
    dvr = _load_resolve_module()
    if dvr is None:
        raise RuntimeError(
            "No se pudo cargar el módulo de DaVinci Resolve.\n"
            f"Verifica la ruta: {config.RESOLVE_SCRIPT_MODULE_PATH}\n"
            "Asegúrate de que DaVinci Resolve esté abierto."
        )
    resolve = dvr.scriptapp("Resolve")
    if resolve is None:
        raise RuntimeError(
            "DaVinci Resolve no está corriendo o no acepta conexiones de scripting.\n"
            "Abre DaVinci Resolve y activa Preferences → General → 'External scripting using local network'."
        )
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject()
    if project is None:
        raise RuntimeError("No hay ningún proyecto abierto en DaVinci Resolve.")
    media_pool = project.GetMediaPool()
    timeline = project.GetCurrentTimeline()
    return resolve, project, media_pool, timeline


# ---------------------------------------------------------------------------
# Project info
# ---------------------------------------------------------------------------

def get_project_info() -> dict:
    resolve, project, media_pool, timeline = connect()
    timelines = []
    count = project.GetTimelineCount()
    for i in range(1, count + 1):
        tl = project.GetTimelineByIndex(i)
        timelines.append(tl.GetName())
    fps_str = project.GetSetting("timelineFrameRate")
    width = project.GetSetting("timelineResolutionWidth")
    height = project.GetSetting("timelineResolutionHeight")
    current_tl_name = timeline.GetName() if timeline else None
    return {
        "project_name": project.GetName(),
        "fps": fps_str,
        "resolution": f"{width}x{height}",
        "timelines": timelines,
        "current_timeline": current_tl_name,
    }


# ---------------------------------------------------------------------------
# Media Pool
# ---------------------------------------------------------------------------

def _fps(project) -> float:
    try:
        return float(project.GetSetting("timelineFrameRate"))
    except Exception:
        return 24.0


def list_media_pool_clips() -> list[dict]:
    resolve, project, media_pool, timeline = connect()
    root_folder = media_pool.GetRootFolder()
    clips = []

    def recurse(folder):
        for clip in folder.GetClipList():
            props = clip.GetClipProperty()
            clips.append({
                "name": props.get("Clip Name", ""),
                "file_path": props.get("File Path", ""),
                "duration_sec": _frames_to_sec(props.get("Frames", 0), project),
                "type": props.get("Type", ""),
                "fps": props.get("FPS", ""),
            })
        for subfolder in folder.GetSubFolderList():
            recurse(subfolder)

    recurse(root_folder)
    return clips


def _frames_to_sec(frames, project) -> float:
    try:
        return int(frames) / _fps(project)
    except Exception:
        return 0.0


def get_clip_path(clip_name: str) -> Optional[str]:
    clips = list_media_pool_clips()
    for c in clips:
        if c["name"].lower() == clip_name.lower() or clip_name.lower() in c["name"].lower():
            return c["file_path"]
    return None


# ---------------------------------------------------------------------------
# Timelines
# ---------------------------------------------------------------------------

def create_timeline(name: str, fps: Optional[float] = None) -> dict:
    resolve, project, media_pool, timeline = connect()
    if fps is None:
        fps = _fps(project)
    new_tl = media_pool.CreateEmptyTimeline(name)
    if new_tl is None:
        return {"success": False, "error": f"No se pudo crear el timeline '{name}'."}
    project.SetCurrentTimeline(new_tl)
    return {"success": True, "timeline_name": new_tl.GetName()}


def set_current_timeline(name: str) -> dict:
    resolve, project, media_pool, timeline = connect()
    count = project.GetTimelineCount()
    for i in range(1, count + 1):
        tl = project.GetTimelineByIndex(i)
        if tl.GetName().lower() == name.lower():
            project.SetCurrentTimeline(tl)
            return {"success": True, "timeline_name": tl.GetName()}
    return {"success": False, "error": f"No se encontró un timeline llamado '{name}'."}


# ---------------------------------------------------------------------------
# Timeline items
# ---------------------------------------------------------------------------

def get_timeline_items() -> list[dict]:
    resolve, project, media_pool, timeline = connect()
    if timeline is None:
        return []
    fps = _fps(project)
    items = []
    # Tracks: 1 = video track 1, etc. Video tracks enumerated with GetItemListInTrack
    track_count = timeline.GetTrackCount("video")
    for track_idx in range(1, track_count + 1):
        for item in (timeline.GetItemListInTrack("video", track_idx) or []):
            start_frame = item.GetStart()
            end_frame = item.GetEnd()
            items.append({
                "name": item.GetName(),
                "track": f"video_{track_idx}",
                "start_sec": start_frame / fps,
                "end_sec": end_frame / fps,
                "duration_sec": (end_frame - start_frame) / fps,
                "left_offset_sec": item.GetLeftOffset() / fps,
                "right_offset_sec": item.GetRightOffset() / fps,
                "_item_ref": None,  # not serializable; use index-based lookups
            })
    audio_track_count = timeline.GetTrackCount("audio")
    for track_idx in range(1, audio_track_count + 1):
        for item in (timeline.GetItemListInTrack("audio", track_idx) or []):
            start_frame = item.GetStart()
            end_frame = item.GetEnd()
            items.append({
                "name": item.GetName(),
                "track": f"audio_{track_idx}",
                "start_sec": start_frame / fps,
                "end_sec": end_frame / fps,
                "duration_sec": (end_frame - start_frame) / fps,
            })
    return items


def _get_video_item_by_index(timeline, fps: float, index: int):
    """Return the timeline item object at the given 0-based index across all video tracks."""
    idx = 0
    track_count = timeline.GetTrackCount("video")
    for track_idx in range(1, track_count + 1):
        items = timeline.GetItemListInTrack("video", track_idx) or []
        for item in items:
            if idx == index:
                return item
            idx += 1
    return None


def add_clip_to_timeline(
    clip_name: str,
    in_point_sec: float = 0.0,
    out_point_sec: Optional[float] = None,
    insert_at_sec: Optional[float] = None,
) -> dict:
    resolve, project, media_pool, timeline = connect()
    fps = _fps(project)

    # Find clip in Media Pool
    root_folder = media_pool.GetRootFolder()
    clip_obj = None

    def find(folder):
        nonlocal clip_obj
        for clip in folder.GetClipList():
            props = clip.GetClipProperty()
            name = props.get("Clip Name", "")
            if name.lower() == clip_name.lower() or clip_name.lower() in name.lower():
                clip_obj = clip
                return
        for subfolder in folder.GetSubFolderList():
            find(subfolder)

    find(root_folder)
    if clip_obj is None:
        return {"success": False, "error": f"Clip '{clip_name}' no encontrado en el Media Pool."}

    props = clip_obj.GetClipProperty()
    total_frames = int(props.get("Frames", 0))
    if out_point_sec is None:
        out_point_sec = total_frames / fps

    in_frame = int(in_point_sec * fps)
    out_frame = int(out_point_sec * fps)

    clip_info = {
        "mediaPoolItem": clip_obj,
        "startFrame": in_frame,
        "endFrame": out_frame,
        "mediaType": 1,  # video+audio
    }

    if insert_at_sec is not None and timeline is not None:
        # Append at specific frame by moving playhead
        timeline.SetCurrentTimecode(
            _sec_to_timecode(insert_at_sec, fps)
        )

    result = media_pool.AppendToTimeline([clip_info])
    if result:
        return {
            "success": True,
            "clip_name": clip_name,
            "in_sec": in_point_sec,
            "out_sec": out_point_sec,
            "duration_sec": out_point_sec - in_point_sec,
        }
    return {"success": False, "error": "AppendToTimeline falló."}


def trim_timeline_item(item_index: int, new_in_sec: float, new_out_sec: float) -> dict:
    resolve, project, media_pool, timeline = connect()
    if timeline is None:
        return {"success": False, "error": "No hay timeline activo."}
    fps = _fps(project)
    item = _get_video_item_by_index(timeline, fps, item_index)
    if item is None:
        return {"success": False, "error": f"Item {item_index} no encontrado."}

    duration_frames = int((new_out_sec - new_in_sec) * fps)
    ok1 = item.SetLeftOffset(int(new_in_sec * fps))
    # SetDuration trims the right side to match the desired duration
    ok2 = item.SetDuration(duration_frames)
    return {"success": bool(ok1 and ok2), "item_index": item_index}


def split_clip(time_sec: float) -> dict:
    resolve, project, media_pool, timeline = connect()
    if timeline is None:
        return {"success": False, "error": "No hay timeline activo."}
    fps = _fps(project)
    tc = _sec_to_timecode(time_sec, fps)
    timeline.SetCurrentTimecode(tc)
    # Split via keyboard shortcut emulation is not possible through API;
    # use the dedicated Split method available in Resolve 18+
    ok = timeline.Split()
    if ok is None:
        # Older Resolve versions: try SetCurrentTimecode + DeleteClips workaround is unavailable;
        # inform the user
        return {
            "success": False,
            "error": "Split() no disponible en esta versión de Resolve. Usa Cmd+B en Resolve con el playhead en la posición correcta.",
        }
    return {"success": True, "split_at_sec": time_sec}


def delete_timeline_item(item_index: int) -> dict:
    resolve, project, media_pool, timeline = connect()
    if timeline is None:
        return {"success": False, "error": "No hay timeline activo."}
    fps = _fps(project)
    item = _get_video_item_by_index(timeline, fps, item_index)
    if item is None:
        return {"success": False, "error": f"Item {item_index} no encontrado."}
    ok = timeline.DeleteClips([item])
    return {"success": bool(ok), "item_index": item_index}


def move_playhead(time_sec: float) -> dict:
    resolve, project, media_pool, timeline = connect()
    if timeline is None:
        return {"success": False, "error": "No hay timeline activo."}
    fps = _fps(project)
    tc = _sec_to_timecode(time_sec, fps)
    ok = timeline.SetCurrentTimecode(tc)
    return {"success": bool(ok), "playhead_sec": time_sec, "timecode": tc}


# ---------------------------------------------------------------------------
# Color correction
# ---------------------------------------------------------------------------

def adjust_color(
    item_index: int,
    lift: Optional[float] = None,
    gamma: Optional[float] = None,
    gain: Optional[float] = None,
    saturation: Optional[float] = None,
    contrast: Optional[float] = None,
) -> dict:
    """
    Apply node-based color correction on the Color page.
    Values are relative offsets from neutral (0.0 = no change for lift/gamma/gain,
    1.0 = no change for saturation/contrast).
    """
    resolve, project, media_pool, timeline = connect()
    if timeline is None:
        return {"success": False, "error": "No hay timeline activo."}
    fps = _fps(project)
    item = _get_video_item_by_index(timeline, fps, item_index)
    if item is None:
        return {"success": False, "error": f"Item {item_index} no encontrado."}

    # Switch to color page is not required for API-based grading
    node_graph = item.GetNodeGraph()
    if node_graph is None:
        # Simpler approach: use SetLUT or direct property setting
        return {
            "success": False,
            "error": (
                "GetNodeGraph no disponible en esta versión de Resolve. "
                "Usa adjust_color manualmente desde la Color Page."
            ),
        }

    # Add a corrector node or use node 1
    nodes = node_graph.GetNodeList()
    if not nodes:
        node_graph.AddNode()
        nodes = node_graph.GetNodeList()

    node = nodes[0]
    if lift is not None:
        node.SetParam("Lift", {"Red": lift, "Green": lift, "Blue": lift, "Master": lift})
    if gamma is not None:
        node.SetParam("Gamma", {"Red": gamma, "Green": gamma, "Blue": gamma, "Master": gamma})
    if gain is not None:
        node.SetParam("Gain", {"Red": gain, "Green": gain, "Blue": gain, "Master": gain})
    if saturation is not None:
        node.SetParam("Saturation", saturation)
    if contrast is not None:
        node.SetParam("Contrast", contrast)

    return {"success": True, "item_index": item_index}


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------

def set_audio_volume(item_index: int, volume_db: float) -> dict:
    resolve, project, media_pool, timeline = connect()
    if timeline is None:
        return {"success": False, "error": "No hay timeline activo."}
    fps = _fps(project)
    item = _get_video_item_by_index(timeline, fps, item_index)
    if item is None:
        return {"success": False, "error": f"Item {item_index} no encontrado."}
    ok = item.SetVolume(volume_db)
    return {"success": bool(ok), "item_index": item_index, "volume_db": volume_db}


# ---------------------------------------------------------------------------
# Titles / Text overlays
# ---------------------------------------------------------------------------

def add_text_title(
    text: str,
    start_sec: float,
    duration_sec: float,
    x: float = 0.5,
    y: float = 0.85,
    font_size: int = 72,
    color: str = "#FFFFFF",
    font_family: str = "Arial",
    bold: bool = True,
) -> dict:
    """
    Adds a Fusion 'Text+' title generator to the timeline.
    Requires DaVinci Resolve Studio for full Fusion support.
    """
    resolve, project, media_pool, timeline = connect()
    if timeline is None:
        return {"success": False, "error": "No hay timeline activo."}
    fps = _fps(project)

    # Use the built-in 'Text+' generator from the Effects library
    # CreateFusionTitle is available in Resolve 18+
    ok = timeline.InsertFusionTitleIntoTimeline("Text+")
    if not ok:
        return {
            "success": False,
            "error": (
                "InsertFusionTitleIntoTimeline no disponible. "
                "Agrega el título manualmente desde Effects → Titles → Text+ en Resolve."
            ),
        }

    # The newly inserted title is selected; configure it
    # (Full Fusion parameter control requires the Fusion scripting API which is
    #  separate from the main scripting API — simplified approach below)
    return {
        "success": True,
        "message": (
            f"Título '{text}' insertado. Para configurar texto, fuente y posición, "
            "selecciona el clip en la timeline e ingresa a Fusion (Shift+5)."
        ),
        "text": text,
        "start_sec": start_sec,
        "duration_sec": duration_sec,
    }


# ---------------------------------------------------------------------------
# Render / Export
# ---------------------------------------------------------------------------

def render_project(output_path: str, preset_name: str = "H.264 Master") -> dict:
    resolve, project, media_pool, timeline = connect()

    # Validate preset exists
    presets = project.GetRenderPresetList()
    if preset_name not in presets:
        return {
            "success": False,
            "error": f"Preset '{preset_name}' no encontrado. Presets disponibles: {presets}",
        }

    project.LoadRenderPreset(preset_name)

    # Set output directory and filename
    out_dir = os.path.dirname(output_path) or os.path.expanduser("~/Movies")
    out_name = os.path.splitext(os.path.basename(output_path))[0] or "Supremacy_Export"
    project.SetRenderSettings({
        "SelectAllFrames": True,
        "TargetDir": out_dir,
        "CustomName": out_name,
    })

    job_id = project.AddRenderJob()
    if not job_id:
        return {"success": False, "error": "No se pudo agregar el render job."}

    project.StartRendering(job_id)
    return {
        "success": True,
        "message": f"Render iniciado. Salida en: {os.path.join(out_dir, out_name)}",
        "preset": preset_name,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sec_to_timecode(seconds: float, fps: float) -> str:
    total_frames = int(round(seconds * fps))
    frames = total_frames % int(fps)
    total_sec = total_frames // int(fps)
    secs = total_sec % 60
    mins = (total_sec // 60) % 60
    hours = total_sec // 3600
    return f"{hours:02d}:{mins:02d}:{secs:02d}:{frames:02d}"
