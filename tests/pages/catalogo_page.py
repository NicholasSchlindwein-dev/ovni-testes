from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from .base_page import BasePage, tid, valor


class CatalogoPage(BasePage):
    ROTA = "/catalogo"

    BUSCA = tid("busca")
    CATEGORIA = tid("filtro-categoria")
    ORDENACAO = tid("ordenacao")
    GRADE_PRONTA = (By.CSS_SELECTOR, '#grade[data-estado="pronto"]')
    CARDS = tid("pacote")
    NOMES = (By.CSS_SELECTOR, '[data-testid="pacote"] .card-nome')
    CONTADOR = tid("contador-resultados")
    VAZIO = tid("vazio")

    def buscar(self, termo):
        self.digitar(self.BUSCA, termo)
        # a busca tem debounce: a grade fica "sintonizando" até renderizar
        self.wait.until(lambda d: d.find_elements(*self.GRADE_PRONTA))

    def filtrar_categoria(self, rotulo):
        Select(self.visivel(self.CATEGORIA)).select_by_visible_text(rotulo)

    def ordenar(self, rotulo):
        Select(self.visivel(self.ORDENACAO)).select_by_visible_text(rotulo)

    def nomes(self):
        return [e.text.strip() for e in self.driver.find_elements(*self.NOMES)]

    def precos(self):
        return [float(e.get_attribute("data-preco")) for e in self.driver.find_elements(*self.CARDS)]

    def categorias_exibidas(self):
        return {e.text.strip() for e in self.driver.find_elements(By.CSS_SELECTOR, ".card-cat")}

    def contador(self):
        return self.texto(self.CONTADOR)

    def mensagem_vazio(self):
        return self.texto(self.VAZIO)

    def abduzir(self, nome_pacote):
        # XPath relativo: do título do card até o botão do mesmo card
        botao = (
            By.XPATH,
            f'//article[@data-testid="pacote"][.//h3[normalize-space()="{nome_pacote}"]]'
            '//button[@data-testid="btn-abduzir"]',
        )
        self.clicar(botao)

    def preco_de(self, nome_pacote):
        card = self.driver.find_element(
            By.XPATH, f'//article[@data-testid="pacote"][.//h3[normalize-space()="{nome_pacote}"]]'
        )
        return valor(card.find_element(By.CSS_SELECTOR, ".card-preco").text)
