"""
Configuration for Supremacy Studios Agent.
Set ANTHROPIC_API_KEY as an environment variable before running.
"""
import os

# --- Anthropic ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"

# --- DaVinci Resolve scripting module path (macOS default) ---
RESOLVE_SCRIPT_MODULE_PATH = (
    "/Library/Application Support/Blackmagic Design/"
    "DaVinci Resolve/Developer/Scripting/Modules"
)

# --- Whisper model size ---
# Options: "tiny", "base", "small", "medium", "large-v3"
# large-v3 is most accurate (~1.5 GB download on first use)
# small is a good balance for Spanish content (~460 MB)
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")

# --- Whisper language hint (speeds up transcription) ---
# Set to None to auto-detect
WHISPER_LANGUAGE = os.environ.get("WHISPER_LANGUAGE", "es")

# --- Scene detection sensitivity ---
# Lower = more sensitive (detects more cuts). Range 15–40
SCENE_DETECT_THRESHOLD = float(os.environ.get("SCENE_DETECT_THRESHOLD", "27.0"))

# --- Silence / filler word detection ---
SILENCE_THRESHOLD_DB = float(os.environ.get("SILENCE_THRESHOLD_DB", "-40.0"))
SILENCE_MIN_DURATION_SEC = float(os.environ.get("SILENCE_MIN_DURATION_SEC", "0.5"))

FILLER_WORDS = [
    "o sea", "este", "eh", "uh", "um", "pues", "bueno",
    "o sea que", "como que", "sabes", "¿sabes?",
]
