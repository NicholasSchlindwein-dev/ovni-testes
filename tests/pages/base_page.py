"""Base dos Page Objects: seletores, esperas explícitas e barra de navegação."""
import os
import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

GRAVANDO = os.environ.get("VIDEO") == "1"
TEMPO_LIMITE = 15 if GRAVANDO else 6   # captura de vídeo divide o driver com o teste
PAUSA_DEMO = 0.4 if GRAVANDO else 0


def tid(nome):
    """Localizador por data-testid (seletor estável, imune a mudança de layout)."""
    return (By.CSS_SELECTOR, f'[data-testid="{nome}"]')


def valor(texto):
    """'R$ 1.499,00' -> 1499.0"""
    limpo = re.sub(r"[^\d,]", "", texto).replace(",", ".")
    return float(limpo)


class BasePage:
    ROTA = None

    APP = tid("app")
    SAUDACAO = tid("saudacao")
    BADGE = tid("badge-carrinho")
    BTN_SAIR = tid("btn-sair")
    TOAST = tid("toast")

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, TEMPO_LIMITE)

    # ---- navegação ----
    def abrir(self):
        self.driver.get(self.base_url + "#" + self.ROTA)
        return self

    def aguardar_rota(self, rota=None):
        rota = rota or self.ROTA
        self.wait.until(
            lambda d: d.find_element(*self.APP).get_attribute("data-rota") == rota,
            f"rota {rota} nao carregou (atual: {self.rota_atual()})",
        )
        return self

    def rota_atual(self):
        return self.driver.find_element(*self.APP).get_attribute("data-rota")

    def ir_para(self, item_nav):
        self.clicar(tid(f"nav-{item_nav}"))

    # ---- interação ----
    def visivel(self, loc):
        return self.wait.until(EC.visibility_of_element_located(loc))

    def clicar(self, loc):
        self.wait.until(EC.element_to_be_clickable(loc)).click()
        self._pausa_demo()

    def digitar(self, loc, texto):
        campo = self.visivel(loc)
        campo.clear()
        campo.send_keys(texto)
        self._pausa_demo()

    @staticmethod
    def _pausa_demo():
        """Só na gravação de vídeo: desacelera para o espectador acompanhar.
        Na execução normal não há pausa fixa — a sincronização é toda por espera explícita."""
        if PAUSA_DEMO:
            time.sleep(PAUSA_DEMO)

    def texto(self, loc):
        return self.visivel(loc).text.strip()

    def aguardar_texto(self, loc, minimo=1):
        """Espera o elemento ter algum texto e o devolve (mensagens assíncronas)."""
        self.wait.until(lambda d: len(d.find_element(*loc).text.strip()) >= minimo)
        return self.driver.find_element(*loc).text.strip()

    def existe(self, loc):
        return len(self.driver.find_elements(*loc)) > 0

    # ---- barra superior ----
    def saudacao(self):
        return self.texto(self.SAUDACAO)

    def qtd_badge(self):
        return int(self.texto(self.BADGE))

    def aguardar_badge(self, esperado):
        self.wait.until(EC.text_to_be_present_in_element(self.BADGE, str(esperado)))

    def toast(self):
        return self.texto(self.TOAST)

    def sair(self):
        self.clicar(self.BTN_SAIR)
