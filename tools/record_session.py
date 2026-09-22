"""
Grava simultaneamente:
  - session.json  : dados neurais com timestamps
  - gameplay.mp4  : captura da tela (via ffmpeg)

Uso:
    python record_session.py --duration 60 --monitor 1

Requer ffmpeg instalado:
    Windows: https://ffmpeg.org/download.html
    ou: winget install ffmpeg
"""

import asyncio
import json
import argparse
import time
import subprocess
import threading
import sys
import os


def start_ffmpeg(monitor: int, duration: int, out_video: str):
    """
    Inicia ffmpeg para capturar a tela do monitor especificado.
    Detecta automaticamente a resolução do monitor via mss.
    """
    try:
        import mss as _mss
        with _mss.MSS() as sct:
            monitors = sct.monitors
            if len(monitors) > monitor:
                mon = monitors[monitor]
                x, y = mon["left"], mon["top"]
                w, h = mon["width"], mon["height"]
            else:
                mon = monitors[1]
                x, y = mon["left"], mon["top"]
                w, h = mon["width"], mon["height"]
    except Exception:
        x, y, w, h = 0, 0, 1920, 1080

    # Ajusta para múltiplo de 2 (exigido pelo codec h264)
    w = w - (w % 2)
    h = h - (h % 2)

    if sys.platform == "win32":
        # Windows: usa gdigrab
        cmd = [
            "ffmpeg", "-y",
            "-f", "gdigrab",
            "-framerate", "30",
            "-offset_x", str(x),
            "-offset_y", str(y),
            "-video_size", f"{w}x{h}",
            "-i", "desktop",
            "-t", str(duration),
            "-vcodec", "libx264",
            "-crf", "23",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-vf", f"scale=1280:-2",
            out_video
        ]
    elif sys.platform == "darwin":
        # macOS: usa avfoundation
        cmd = [
            "ffmpeg", "-y",
            "-f", "avfoundation",
            "-framerate", "30",
            "-i", "1:none",
            "-t", str(duration),
            "-vcodec", "libx264",
            "-crf", "23",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1280:-2",
            out_video
        ]
    else:
        # Linux: usa x11grab
        cmd = [
            "ffmpeg", "-y",
            "-f", "x11grab",
            "-framerate", "30",
            "-video_size", f"{w}x{h}",
            "-i", f":0.0+{x},{y}",
            "-t", str(duration),
            "-vcodec", "libx264",
            "-crf", "23",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1280:-2",
            out_video
        ]

    print(f"  ffmpeg: capturando {w}x{h} do monitor {monitor}")
    print(f"  saída:  {out_video}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


async def record_ws(duration: int, out_json: str, start: float = None):
    """Grava os dados do WebSocket com timestamps relativos ao início do vídeo."""
    try:
        import websockets
    except ImportError:
        print("ERRO: pip install websockets")
        return []

    frames = []
    if start is None:
        start = time.time()

    print(f"  WebSocket: conectando em ws://localhost:8765 ...")

    try:
        async with websockets.connect("ws://localhost:8765", ping_interval=None) as ws:
            print(f"  WebSocket: conectado — gravando {duration}s")
            async for msg in ws:
                try:
                    data = json.loads(msg)
                    data["_t"] = round(time.time() - start, 3)
                    frames.append(data)

                    elapsed = time.time() - start
                    pct = int(elapsed / duration * 40)
                    bar = "█" * pct + "░" * (40 - pct)
                    print(f"\r  [{bar}] {elapsed:.1f}s / {duration}s  frames={len(frames)}", end="", flush=True)

                    if elapsed >= duration:
                        break
                except Exception:
                    pass
    except Exception as e:
        print(f"\n  WebSocket erro: {e}")
        print("  Certifique-se que main.py está rodando")
        return []

    print(f"\n  WebSocket: {len(frames)} frames gravados")
    return frames


def save_json(frames: list, out_json: str):
    """Comprime e salva o JSON."""
    if not frames:
        print("  Nenhum frame para salvar")
        return

    # Comprime frames muito similares
    compressed = [frames[0]]
    for f in frames[1:]:
        p = compressed[-1]
        if (abs(f.get("fw_bias", 0) - p.get("fw_bias", 0)) > 0.004
                or f.get("collected", 0) != p.get("collected", 0)
                or f.get("pressed_keys", []) != p.get("pressed_keys", [])):
            compressed.append(f)

    with open(out_json, "w") as fp:
        json.dump(compressed, fp, separators=(",", ":"))

    size_kb = os.path.getsize(out_json) / 1024
    duration = frames[-1]["_t"] if frames else 0
    print(f"  JSON: {len(compressed)} frames → {out_json} ({size_kb:.1f} KB)")
    print(f"  Duração: {duration:.1f}s  Coletas: {frames[-1].get('collected', 0)}")


async def main_async(args):
    print("=" * 55)
    print("  FLY BRAIN — GRAVAÇÃO SINCRONIZADA")
    print("=" * 55)
    print(f"  Duração:  {args.duration}s")
    print(f"  Monitor:  {args.monitor}")
    print(f"  Vídeo:    {args.out_video}")
    print(f"  JSON:     {args.out_json}")
    print()

    # Verifica ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"],
                       capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERRO: ffmpeg não encontrado.")
        print("  Windows: winget install ffmpeg")
        print("  ou baixe em: https://ffmpeg.org/download.html")
        return

    print("Iniciando gravação simultânea...")
    print()

    # Inicia ffmpeg e marca o instante exato
    t_ffmpeg_start = time.time()
    ffmpeg_proc = start_ffmpeg(args.monitor, args.duration, args.out_video)

    # Pequeno delay para o ffmpeg inicializar
    await asyncio.sleep(0.5)

    # Grava WebSocket — passa o instante de início do ffmpeg
    # para que os _t do JSON sejam relativos ao início do vídeo
    frames = await record_ws(args.duration, args.out_json, t_ffmpeg_start)

    # Aguarda ffmpeg terminar
    print("\nAguardando ffmpeg finalizar...")
    try:
        ffmpeg_proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        ffmpeg_proc.terminate()

    # Salva JSON
    save_json(frames, args.out_json)

    print()
    print("=" * 55)
    print("  GRAVAÇÃO CONCLUÍDA")
    print(f"  Coloque {args.out_video} e {args.out_json}")
    print("  na raiz do projeto junto com visualizer.html")
    print("=" * 55)


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Grava vídeo + dados neurais sincronizados"
    )
    p.add_argument("--duration",  type=int, default=60,
                   help="Duração em segundos (default: 60)")
    p.add_argument("--monitor",   type=int, default=1,
                   help="Monitor a capturar (default: 1)")
    p.add_argument("--out-video", default="gameplay.mp4",
                   help="Nome do arquivo de vídeo")
    p.add_argument("--out-json",  default="session.json",
                   help="Nome do arquivo JSON")
    args = p.parse_args()

    asyncio.run(main_async(args))