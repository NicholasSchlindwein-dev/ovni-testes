from selenium.webdriver.common.by import By

from .base_page import BasePage, tid, valor


class CarrinhoPage(BasePage):
    ROTA = "/carrinho"

    ITENS = tid("item-carrinho")
    VAZIO = tid("carrinho-vazio")
    SUBTOTAL = tid("subtotal")
    DESCONTO = tid("desconto")
    TOTAL = tid("total")
    CUPOM = tid("cupom")
    BTN_CUPOM = tid("btn-cupom")
    MSG_CUPOM = tid("msg-cupom")
    BTN_CHECKOUT = tid("btn-checkout")

    def _na_linha(self, pacote_id, testid):
        return (By.CSS_SELECTOR, f'tr[data-testid="item-carrinho"][data-id="{pacote_id}"] [data-testid="{testid}"]')

    def nomes_itens(self):
        return [e.text.strip() for e in self.driver.find_elements(*tid("item-nome"))]

    def qtd_itens(self):
        return len(self.driver.find_elements(*self.ITENS))

    def quantidade(self, pacote_id):
        return int(self.texto(self._na_linha(pacote_id, "qtd")))

    def subtotal_item(self, pacote_id):
        return valor(self.texto(self._na_linha(pacote_id, "item-subtotal")))

    def aumentar(self, pacote_id, vezes=1):
        for _ in range(vezes):
            antes = self.quantidade(pacote_id)
            self.clicar(self._na_linha(pacote_id, "btn-mais"))
            self.wait.until(lambda d: self.quantidade(pacote_id) == antes + 1)

    def diminuir(self, pacote_id):
        self.clicar(self._na_linha(pacote_id, "btn-menos"))

    def botao_mais_habilitado(self, pacote_id):
        return self.driver.find_element(*self._na_linha(pacote_id, "btn-mais")).is_enabled()

    def botao_menos_habilitado(self, pacote_id):
        return self.driver.find_element(*self._na_linha(pacote_id, "btn-menos")).is_enabled()

    def remover(self, pacote_id):
        self.clicar(self._na_linha(pacote_id, "btn-remover"))

    def aplicar_cupom(self, codigo):
        self.digitar(self.CUPOM, codigo)
        self.clicar(self.BTN_CUPOM)
        return self.aguardar_texto(self.MSG_CUPOM)

    def subtotal(self):
        return valor(self.texto(self.SUBTOTAL))

    def desconto(self):
        return valor(self.texto(self.DESCONTO))

    def total(self):
        return valor(self.texto(self.TOTAL))

    def mensagem_vazio(self):
        return self.texto(self.VAZIO)

    def checkout_habilitado(self):
        return self.visivel(self.BTN_CHECKOUT).is_enabled()

    def ir_para_checkout(self):
        self.clicar(self.BTN_CHECKOUT)
