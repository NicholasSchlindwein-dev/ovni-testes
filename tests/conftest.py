"""Setup e teardown compartilhados da suíte.

- servidor: sobe o site estático uma vez por sessão (teardown derruba).
- driver: um Chrome limpo por teste (isolamento de localStorage).
- sessao / carrinho_com: atalhos de pré-condição para não repetir login via UI.
- hook de relatório: screenshot de todo teste anexado ao pytest-html.
"""
import json
import os
import re
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from selenium import webdriver

RAIZ = Path(__file__).resolve().parent.parent
DIR_SITE = RAIZ / "site"
DIR_PRINTS = RAIZ / "evidencias" / "screenshots"

DIR_VIDEOS = RAIZ / "evidencias" / "video"
GRAVAR_VIDEO = os.environ.get("VIDEO") == "1"
_videos = []

USUARIO = {"email": "agente@ovni.gov", "senha": "area51", "nome": "Agente K"}


def _nome_arquivo(nodeid):
    return re.sub(r"[^\w\-]+", "_", nodeid.split("::", 1)[-1]).strip("_")[:120]


class _HandlerSilencioso(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def base_url():
    handler = partial(_HandlerSilencioso, directory=str(DIR_SITE))
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{servidor.server_address[1]}/"
    servidor.shutdown()
    servidor.server_close()


@pytest.fixture
def driver(request):
    opcoes = webdriver.ChromeOptions()
    if os.environ.get("HEADED") != "1":
        opcoes.add_argument("--headless=new")
    opcoes.add_argument("--window-size=1366,900")
    opcoes.add_argument("--lang=pt-BR")
    navegador = webdriver.Chrome(options=opcoes)

    gravador = None
    if GRAVAR_VIDEO:
        from gravador import Gravador

        gravador = Gravador(navegador)
        gravador.iniciar()

    yield navegador

    if gravador:
        resultado = getattr(request.node, "_resultado", "sem resultado").upper()
        nome = _nome_arquivo(request.node.nodeid)
        destino = DIR_VIDEOS / "por_teste" / f"{len(_videos) + 1:02d}_{nome}.mp4"
        try:
            video = gravador.finalizar(destino, f"[{resultado}] {request.node.nodeid}")
            if video:
                _videos.append(video)
        except Exception as erro:
            print(f"[evidencia] video indisponivel: {erro}")
    navegador.quit()


def pytest_sessionfinish(session):
    if GRAVAR_VIDEO and _videos:
        from gravador import unir

        unir(_videos, DIR_VIDEOS / "suite_completa.mp4")


@pytest.fixture
def sessao(driver, base_url):
    """Pré-condição: agente já autenticado, parado no catálogo."""
    from pages.catalogo_page import CatalogoPage

    driver.get(base_url)
    driver.execute_script(
        "localStorage.setItem('ovni_sessao', arguments[0]);",
        json.dumps({"email": USUARIO["email"], "nome": USUARIO["nome"]}),
    )
    driver.get(base_url + "#/catalogo")
    CatalogoPage(driver, base_url).aguardar_rota("/catalogo")
    return driver


@pytest.fixture
def carrinho_com(sessao):
    """Fábrica: semeia o carrinho direto no storage. Uso: carrinho_com({1: 1, 4: 2})."""

    def _semear(itens):
        dados = [{"id": pid, "qtd": qtd} for pid, qtd in itens.items()]
        sessao.execute_script(
            "localStorage.setItem('ovni_carrinho', arguments[0]);", json.dumps(dados)
        )

    return _semear


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    resultado = yield
    relatorio = resultado.get_result()
    if relatorio.when != "call":
        return
    item._resultado = "passou" if relatorio.passed else "falhou"
    navegador = item.funcargs.get("driver")
    if navegador is None:
        return
    DIR_PRINTS.mkdir(parents=True, exist_ok=True)
    nome = _nome_arquivo(item.nodeid)
    status = "FALHOU" if relatorio.failed else "ok"
    try:
        navegador.save_screenshot(str(DIR_PRINTS / f"{nome}__{status}.png"))
        from pytest_html import extras

        extra = getattr(relatorio, "extras", [])
        extra.append(extras.png(navegador.get_screenshot_as_base64(), name="Tela final"))
        extra.append(extras.url(navegador.current_url, name="URL final"))
        relatorio.extras = extra
    except Exception as erro:  # evidência nunca deve mascarar o resultado do teste
        print(f"[evidencia] screenshot indisponivel: {erro}")
