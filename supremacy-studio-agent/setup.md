# Supremacy Studios Agent — Guía de Instalación

## Requisitos previos

- macOS (Apple Silicon o Intel)
- DaVinci Resolve 18+ instalado (Free o Studio)
- Python 3.10+
- Una API Key de Anthropic: https://console.anthropic.com

---

## 1. Instalar dependencias

```bash
cd supremacy-studio-agent
pip install -r requirements.txt
```

En la primera ejecución, faster-whisper descargará el modelo de IA (~460 MB para `small`, ~1.5 GB para `large-v3`).

---

## 2. Configurar API Key

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

Para hacerlo permanente, agrégalo a tu `~/.zshrc` o `~/.bash_profile`:

```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-..."' >> ~/.zshrc
source ~/.zshrc
```

---

## 3. Activar el scripting en DaVinci Resolve

1. Abre DaVinci Resolve
2. Ve a **DaVinci Resolve → Preferences → General**
3. Activa **"External scripting using local network"**
4. Reinicia Resolve si se te solicita

---

## 4. Correr el agente

Con DaVinci Resolve abierto y un proyecto activo:

```bash
python agent.py
```

---

## 5. Primer uso: verificar conexión

Al iniciar, el agente mostrará el nombre del proyecto y el timeline activo si la conexión es exitosa.

Si ves `⚠ Resolve no disponible`, verifica:
- Que DaVinci Resolve esté abierto
- Que tengas un proyecto abierto (no solo el Project Manager)
- Que el scripting externo esté activado (paso 3)

---

## Ejemplos de uso

```
Tú: ¿Qué material tengo en el proyecto?
Tú: Transcribe el clip Interview_01.mp4
Tú: Edita la entrevista quitando silencios y muletillas, guárdala en un timeline llamado "Corte limpio"
Tú: Analiza la referencia en ~/Desktop/referencia.mp4
Tú: Aplica ese look a todos los clips del timeline actual
Tú: Exporta en H.264 1080p a ~/Movies/final.mp4
```

---

## Personalización

Edita `config.py` para:
- Cambiar el modelo de Whisper: `WHISPER_MODEL = "large-v3"` (más preciso, más lento)
- Cambiar el idioma de transcripción: `WHISPER_LANGUAGE = "en"`
- Ajustar la sensibilidad de detección de escenas: `SCENE_DETECT_THRESHOLD = 20.0`
- Agregar muletillas personalizadas a la lista `FILLER_WORDS`

---

## Notas importantes

- **Split de clips**: Requiere Resolve 18+. En versiones anteriores, mueve el playhead en Resolve y usa `Cmd+B`.
- **Títulos Fusion**: Requiere DaVinci Resolve **Studio**. En la versión Free, agrega los títulos manualmente.
- **Corrección de color vía API**: Disponible en Resolve 18+. En versiones anteriores, usa el Color Page manualmente.
- **No se puede deshacer desde el agente**: Antes de operaciones destructivas (eliminar clips), guarda manualmente con `Cmd+S` en Resolve.
- **Modelos de Whisper grandes**: Requieren bastante RAM. En Macs con 8 GB, usar `small` o `medium`.
