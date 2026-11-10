"""Gravação em vídeo da execução (opcional, ligada com a variável VIDEO=1).

Uma thread tira screenshots do navegador durante o teste; no teardown o ffmpeg
(embutido no pacote imageio-ffmpeg) monta um MP4 com o nome e o resultado do
teste na legenda. No fim da sessão as partes são unidas em um vídeo único.
"""
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

INTERVALO = 0.2          # ~5 capturas por segundo (mais que isso disputa o driver com o teste)
PAUSA_FINAL = 1.2        # segura a última tela para dar tempo de ler
FONTE = r"C\:/Windows/Fonts/consola.ttf"


def _ffmpeg():
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


class Gravador:
    def __init__(self, driver):
        self.driver = driver
        self.pasta = Path(tempfile.mkdtemp(prefix="ovni_video_"))
        self.quadros = []            # (arquivo, instante)
        self._parar = threading.Event()
        self._thread = threading.Thread(target=self._capturar, daemon=True)

    def iniciar(self):
        self._thread.start()

    def _capturar(self):
        while not self._parar.is_set():
            inicio = time.monotonic()
            try:
                png = self.driver.get_screenshot_as_png()
            except Exception:
                break
            arquivo = f"q{len(self.quadros):05d}.png"
            (self.pasta / arquivo).write_bytes(png)
            self.quadros.append((arquivo, inicio))
            self._parar.wait(max(0.0, INTERVALO - (time.monotonic() - inicio)))

    def finalizar(self, destino, legenda):
        """Para a captura e gera o MP4. Deve ser chamado antes de driver.quit()."""
        self._parar.set()
        self._thread.join(timeout=5)
        try:
            if not self.quadros:
                return None
            linhas = ["ffconcat version 1.0"]
            for (arquivo, t), proximo in zip(self.quadros, self.quadros[1:] + [None]):
                duracao = (proximo[1] - t) if proximo else PAUSA_FINAL
                linhas += [f"file {arquivo}", f"duration {duracao:.3f}"]
            linhas.append(f"file {self.quadros[-1][0]}")   # exigência do demuxer concat
            (self.pasta / "lista.txt").write_text("\n".join(linhas), encoding="utf-8")
            (self.pasta / "legenda.txt").write_text(legenda, encoding="utf-8")

            filtro = (
                "fps=10,scale=trunc(iw/2)*2:trunc(ih/2)*2,"
                f"drawtext=fontfile='{FONTE}':textfile=legenda.txt:x=12:y=h-th-12:"
                "fontsize=18:fontcolor=white:box=1:boxcolor=black@0.8:boxborderw=8"
            )
            destino.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [_ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-i", "lista.txt",
                 "-vf", filtro, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "10",
                 str(destino.resolve())],
                cwd=self.pasta, check=True,
            )
            return destino
        finally:
            shutil.rmtree(self.pasta, ignore_errors=True)


def unir(partes, destino):
    """Concatena os vídeos por teste (mesmo codec) em um arquivo único."""
    if not partes:
        return None
    lista = destino.parent / "_partes.txt"
    lista.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in partes), encoding="utf-8"
    )
    try:
        subprocess.run(
            [_ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(lista), "-c", "copy", str(destino)],
            check=True,
        )
    finally:
        lista.unlink(missing_ok=True)
    return destino
