from selenium.webdriver.support import expected_conditions as EC

from .base_page import BasePage, tid


class LoginPage(BasePage):
    ROTA = "/login"

    EMAIL = tid("login-email")
    SENHA = tid("login-senha")
    ENTRAR = tid("login-entrar")
    ERRO = tid("login-erro")

    def autenticar(self, email, senha):
        self.digitar(self.EMAIL, email)
        self.digitar(self.SENHA, senha)
        self.clicar(self.ENTRAR)

    def mensagem_erro(self):
        return self.aguardar_texto(self.ERRO)

    def aguardar_erro_contendo(self, trecho):
        self.wait.until(EC.text_to_be_present_in_element(self.ERRO, trecho))
        return self.texto(self.ERRO)

    def botao_habilitado(self):
        return self.driver.find_element(*self.ENTRAR).is_enabled()
