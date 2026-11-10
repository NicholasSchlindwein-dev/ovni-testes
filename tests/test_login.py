"""Autenticação e controle de acesso."""
import pytest

from conftest import USUARIO
from pages.catalogo_page import CatalogoPage
from pages.login_page import LoginPage


@pytest.fixture
def login(driver, base_url):
    pagina = LoginPage(driver, base_url)
    driver.get(base_url)
    return pagina.aguardar_rota()


@pytest.mark.positivo
@pytest.mark.smoke
def test_login_com_credenciais_validas_abre_catalogo(login):
    login.autenticar(USUARIO["email"], USUARIO["senha"])

    login.aguardar_rota("/catalogo")
    assert login.saudacao() == f"Olá, {USUARIO['nome']}"
    assert login.driver.current_url.endswith("#/catalogo")


@pytest.mark.negativo
@pytest.mark.parametrize(
    "email, senha, mensagem",
    [
        pytest.param("", "area51", "Informe o e-mail do agente.", id="email_vazio"),
        pytest.param("agente.ovni.gov", "area51", "E-mail em formato inválido.", id="email_sem_arroba"),
        pytest.param(USUARIO["email"], "", "Informe a senha.", id="senha_vazia"),
        pytest.param(USUARIO["email"], "area52", "Credenciais não reconhecidas. Tentativa 1 de 3.", id="senha_errada"),
        pytest.param("et@casa.com", "area51", "Credenciais não reconhecidas. Tentativa 1 de 3.", id="usuario_inexistente"),
    ],
)
def test_login_invalido_exibe_mensagem_e_nao_autentica(login, email, senha, mensagem):
    login.autenticar(email, senha)

    assert login.mensagem_erro() == mensagem
    assert login.rota_atual() == "/login"
    assert not login.existe(login.SAUDACAO), "barra de usuário não deveria aparecer sem login"


@pytest.mark.negativo
def test_tres_tentativas_erradas_bloqueiam_ate_a_senha_correta(login):
    for tentativa in (1, 2):
        login.autenticar(USUARIO["email"], "errada")
        login.aguardar_erro_contendo(f"Tentativa {tentativa} de 3")
    login.autenticar(USUARIO["email"], "errada")

    erro = login.aguardar_erro_contendo("Acesso bloqueado")
    assert erro == "Acesso bloqueado. Os Homens de Preto foram notificados."
    assert not login.botao_habilitado()

    # bloqueio persiste após recarregar: senha correta não entra mais
    login.driver.refresh()
    login.aguardar_rota()
    assert not login.botao_habilitado()
    assert login.mensagem_erro().startswith("Acesso bloqueado")


@pytest.mark.negativo
@pytest.mark.parametrize("rota", ["/catalogo", "/carrinho", "/checkout", "/abducoes"])
def test_rota_protegida_sem_sessao_redireciona_para_login(driver, base_url, rota):
    driver.get(base_url + "#" + rota)

    pagina = LoginPage(driver, base_url).aguardar_rota("/login")
    assert pagina.visivel(pagina.EMAIL).is_displayed()
    assert driver.current_url.endswith("#/login")


@pytest.mark.positivo
def test_logout_encerra_sessao_e_bloqueia_retorno(sessao, base_url):
    catalogo = CatalogoPage(sessao, base_url)
    catalogo.sair()

    login = LoginPage(sessao, base_url).aguardar_rota("/login")
    assert not login.existe(login.SAUDACAO)

    # tentar voltar direto ao catálogo deve cair no login de novo
    sessao.get(base_url + "#/catalogo")
    login.aguardar_rota("/login")
    assert sessao.execute_script("return localStorage.getItem('ovni_sessao')") is None
