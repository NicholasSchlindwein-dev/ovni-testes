"""Histórico de abduções: listagem, cancelamento via modal e persistência."""
import json

import pytest

from pages.abducoes_page import AbducoesPage

REGISTROS = [
    {"protocolo": "ABD-000042", "nome": "Fox Mulder", "data": "13/09/2099", "total": 199, "status": "AGENDADA", "itens": []},
    {"protocolo": "ABD-001947", "nome": "Dana Scully", "data": "08/07/2099", "total": 1499, "status": "AGENDADA", "itens": []},
]


@pytest.fixture
def historico(sessao, base_url):
    sessao.execute_script("localStorage.setItem('ovni_abducoes', arguments[0]);", json.dumps(REGISTROS))
    return AbducoesPage(sessao, base_url).abrir().aguardar_rota()


@pytest.mark.positivo
def test_historico_vazio_exibe_mensagem(sessao, base_url):
    pagina = AbducoesPage(sessao, base_url).abrir().aguardar_rota()

    assert pagina.protocolos() == []
    assert pagina.mensagem_vazio().endswith("Você ainda não foi abduzido. Que vida pacata.")


@pytest.mark.positivo
def test_cancelar_abducao_muda_status_e_persiste_apos_recarregar(historico):
    historico.pedir_cancelamento("ABD-000042")
    historico.confirmar_cancelamento()

    assert historico.status("ABD-000042") == "CANCELADA"
    assert not historico.pode_cancelar("ABD-000042")
    assert historico.status("ABD-001947") == "AGENDADA", "outras abduções não podem ser afetadas"
    assert historico.toast() == "Abdução ABD-000042 cancelada."

    historico.driver.refresh()
    historico.aguardar_rota()
    assert historico.status("ABD-000042") == "CANCELADA"


@pytest.mark.negativo
def test_desistir_no_modal_mantem_abducao_agendada(historico):
    historico.pedir_cancelamento("ABD-001947")
    historico.desistir_do_cancelamento()

    assert historico.status("ABD-001947") == "AGENDADA"
    assert historico.pode_cancelar("ABD-001947")


@pytest.mark.negativo
def test_nome_com_html_e_exibido_como_texto(sessao, base_url):
    """Segurança: nome malicioso não pode virar marcação na tabela."""
    malicioso = '<img src=x onerror="window.__xss=1">'
    registro = {**REGISTROS[0], "nome": malicioso}
    sessao.execute_script("localStorage.setItem('ovni_abducoes', arguments[0]);", json.dumps([registro]))
    pagina = AbducoesPage(sessao, base_url).abrir().aguardar_rota()

    assert pagina.nome("ABD-000042") == malicioso
    assert sessao.execute_script("return window.__xss") is None
