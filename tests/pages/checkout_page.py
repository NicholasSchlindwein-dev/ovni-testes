from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from .base_page import BasePage, tid, valor


class CheckoutPage(BasePage):
    ROTA = "/checkout"

    NOME = tid("ck-nome")
    IDADE = tid("ck-idade")
    SANGUE = tid("ck-sangue")
    DATA = tid("ck-data")
    TERMO = tid("ck-termo")
    CONFIRMAR = tid("ck-confirmar")
    TOTAL = tid("ck-total")
    PROCESSANDO = tid("processando")

    PROTOCOLO = tid("protocolo")
    CONF_NOME = tid("conf-nome")
    CONF_TOTAL = tid("conf-total")
    VER_ABDUCOES = tid("ver-abducoes")

    def preencher(self, nome="", idade="", sangue="", data="", termo=False):
        self.digitar(self.NOME, nome)
        self.digitar(self.IDADE, idade)
        if sangue:
            Select(self.visivel(self.SANGUE)).select_by_visible_text(sangue)
        self.digitar(self.DATA, data)
        caixa = self.visivel(self.TERMO)
        if caixa.is_selected() != termo:
            caixa.click()

    def confirmar(self):
        self.clicar(self.CONFIRMAR)

    def erro(self, campo):
        return self.driver.find_element(*tid(f"erro-{campo}")).text.strip()

    def campo_marcado_invalido(self, campo):
        classes = self.driver.find_element(*tid(f"ck-{campo}")).get_attribute("class") or ""
        return "invalido" in classes.split()

    def total(self):
        return valor(self.texto(self.TOTAL))

    def aguardar_confirmacao(self):
        """Processamento é assíncrono (overlay ~1,5 s) antes da tela de protocolo."""
        self.visivel(self.PROCESSANDO)
        self.wait.until(EC.invisibility_of_element_located(self.PROCESSANDO))
        self.aguardar_rota("/confirmacao")

    def protocolo(self):
        return self.texto(self.PROTOCOLO)

    def nome_confirmado(self):
        return self.texto(self.CONF_NOME)

    def total_confirmado(self):
        return valor(self.texto(self.CONF_TOTAL))
