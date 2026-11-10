"""Agendamento da abdução: validações do formulário (orientado a dados) e conclusão."""
import json
import re
from datetime import date, timedelta
from pathlib import Path

import pytest

from pages.abducoes_page import AbducoesPage
from pages.carrinho_page import CarrinhoPage
from pages.checkout_page import CheckoutPage

DATA_FUTURA = (date.today() + timedelta(days=30)).strftime("%d/%m/%Y")
CASOS_INVALIDOS = json.loads(
    (Path(__file__).parent / "data" / "checkout_invalidos.json").read_text(encoding="utf-8")
)
VALIDO = {"nome": "Dana Scully", "idade": "32", "sangue": "AB-", "data": DATA_FUTURA, "termo": True}


def _resolver(dados):
    """Troca o marcador FUTURA do arquivo de dados por uma data real no futuro."""
    return {**dados, "data": DATA_FUTURA if dados["data"] == "FUTURA" else dados["data"]}


@pytest.fixture
def checkout(sessao, base_url, carrinho_com):
    """Checkout aberto com 1 Abdução Express (199) + 2 Vaca VIP (698) = 897."""
    carrinho_com({1: 1, 4: 2})
    return CheckoutPage(sessao, base_url).abrir().aguardar_rota()


@pytest.mark.positivo
@pytest.mark.smoke
def test_agendamento_valido_gera_protocolo_e_registra_no_historico(checkout, base_url):
    assert checkout.total() == 897.0

    checkout.preencher(**VALIDO)
    checkout.confirmar()
    checkout.aguardar_confirmacao()

    protocolo = checkout.protocolo()
    assert re.fullmatch(r"ABD-\d{6}", protocolo), f"protocolo fora do padrão: {protocolo}"
    assert checkout.nome_confirmado() == "Dana Scully"
    assert checkout.total_confirmado() == 897.0
    assert checkout.qtd_badge() == 0, "carrinho deve esvaziar após agendar"

    checkout.clicar(checkout.VER_ABDUCOES)
    historico = AbducoesPage(checkout.driver, base_url).aguardar_rota()
    assert historico.protocolos() == [protocolo]
    assert historico.status(protocolo) == "AGENDADA"
    assert historico.total(protocolo) == 897.0


@pytest.mark.positivo
def test_cupom_aplicado_no_carrinho_e_cobrado_no_agendamento(sessao, base_url, carrinho_com):
    carrinho_com({1: 1, 4: 2})
    carrinho = CarrinhoPage(sessao, base_url).abrir().aguardar_rota()
    carrinho.aplicar_cupom("TERRAPLANA10")
    carrinho.ir_para_checkout()

    checkout = CheckoutPage(sessao, base_url).aguardar_rota()
    assert checkout.total() == pytest.approx(807.30)
    checkout.preencher(**VALIDO)
    checkout.confirmar()
    checkout.aguardar_confirmacao()

    assert checkout.total_confirmado() == pytest.approx(807.30)


@pytest.mark.positivo
@pytest.mark.parametrize("idade", ["18", "120"], ids=["limite_inferior", "limite_superior"])
def test_idades_nos_limites_sao_aceitas(checkout, idade):
    checkout.preencher(**{**VALIDO, "idade": idade})
    checkout.confirmar()

    checkout.aguardar_confirmacao()
    assert checkout.protocolo().startswith("ABD-")


@pytest.mark.negativo
@pytest.mark.parametrize("caso", CASOS_INVALIDOS, ids=[c["id"] for c in CASOS_INVALIDOS])
def test_dado_invalido_impede_agendamento(checkout, caso):
    checkout.preencher(**_resolver(caso["dados"]))
    checkout.confirmar()

    assert checkout.erro(caso["campo"]) == caso["mensagem"]
    if caso["campo"] != "termo":
        assert checkout.campo_marcado_invalido(caso["campo"])
    outros = {"nome", "idade", "sangue", "data", "termo"} - {caso["campo"]}
    assert all(checkout.erro(c) == "" for c in outros), "só o campo inválido deve acusar erro"
    assert checkout.rota_atual() == "/checkout"
    assert not checkout.existe(checkout.PROCESSANDO)
    assert checkout.driver.execute_script("return localStorage.getItem('ovni_abducoes')") is None


@pytest.mark.negativo
def test_formulario_em_branco_acusa_todos_os_campos(checkout):
    checkout.confirmar()

    erros = {c: checkout.erro(c) for c in ("nome", "idade", "sangue", "data", "termo")}
    assert all(erros.values()), f"campos sem mensagem de erro: {[c for c, e in erros.items() if not e]}"
    assert checkout.qtd_badge() == 3, "carrinho deve permanecer intacto"
