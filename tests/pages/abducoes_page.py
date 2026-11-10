from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base_page import BasePage, tid, valor


class AbducoesPage(BasePage):
    ROTA = "/abducoes"

    LINHAS = tid("abducao")
    VAZIO = tid("abducoes-vazio")
    MODAL = tid("modal-cancelar")
    MODAL_SIM = tid("modal-sim")
    MODAL_NAO = tid("modal-nao")

    def _na_linha(self, protocolo, testid):
        return (By.CSS_SELECTOR, f'tr[data-protocolo="{protocolo}"] [data-testid="{testid}"]')

    def protocolos(self):
        return [e.text.strip() for e in self.driver.find_elements(*tid("ab-protocolo"))]

    def status(self, protocolo):
        return self.texto(self._na_linha(protocolo, "ab-status"))

    def nome(self, protocolo):
        return self.texto(self._na_linha(protocolo, "ab-nome"))

    def total(self, protocolo):
        return valor(self.texto(self._na_linha(protocolo, "ab-total")))

    def pode_cancelar(self, protocolo):
        return self.existe(self._na_linha(protocolo, "btn-cancelar"))

    def pedir_cancelamento(self, protocolo):
        self.clicar(self._na_linha(protocolo, "btn-cancelar"))
        self.visivel(self.MODAL)

    def confirmar_cancelamento(self):
        self.clicar(self.MODAL_SIM)
        self.wait.until(EC.invisibility_of_element_located(self.MODAL))

    def desistir_do_cancelamento(self):
        self.clicar(self.MODAL_NAO)
        self.wait.until(EC.invisibility_of_element_located(self.MODAL))

    def mensagem_vazio(self):
        return self.texto(self.VAZIO)
