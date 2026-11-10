"""Carrinho ("raio trator"): inclusão, quantidades, remoção, cupons e totais."""
import pytest

from pages.carrinho_page import CarrinhoPage
from pages.catalogo_page import CatalogoPage

EXPRESS, VACA = 1, 4          # ids dos pacotes
PRECO_EXPRESS, PRECO_VACA = 199.0, 349.0


@pytest.fixture
def carrinho(sessao, base_url, carrinho_com):
    """Carrinho já com 1 Abdução Express + 1 Vaca VIP."""
    carrinho_com({EXPRESS: 1, VACA: 1})
    return CarrinhoPage(sessao, base_url).abrir().aguardar_rota()


@pytest.mark.positivo
@pytest.mark.smoke
def test_adicionar_pacotes_pelo_catalogo_atualiza_badge_e_carrinho(sessao, base_url):
    catalogo = CatalogoPage(sessao, base_url)
    assert catalogo.qtd_badge() == 0

    catalogo.abduzir("Abdução Express")
    catalogo.aguardar_badge(1)
    assert catalogo.toast() == "Abdução Express fisgado pelo raio trator!"
    catalogo.abduzir("Vaca VIP")
    catalogo.aguardar_badge(2)

    catalogo.ir_para("carrinho")
    carrinho = CarrinhoPage(sessao, base_url).aguardar_rota()
    assert len(carrinho.nomes_itens()) == 2
    assert any("Abdução Express" in n for n in carrinho.nomes_itens())
    assert any("Vaca VIP" in n for n in carrinho.nomes_itens())
    assert carrinho.total() == PRECO_EXPRESS + PRECO_VACA


@pytest.mark.positivo
def test_aumentar_quantidade_recalcula_subtotal_e_total(carrinho):
    carrinho.aumentar(EXPRESS, vezes=2)

    assert carrinho.quantidade(EXPRESS) == 3
    assert carrinho.subtotal_item(EXPRESS) == 3 * PRECO_EXPRESS
    assert carrinho.total() == 3 * PRECO_EXPRESS + PRECO_VACA
    assert carrinho.qtd_badge() == 4


@pytest.mark.negativo
def test_quantidade_respeita_limites_de_1_a_5(carrinho):
    assert not carrinho.botao_menos_habilitado(EXPRESS), "não pode ir abaixo de 1"

    carrinho.aumentar(EXPRESS, vezes=4)

    assert carrinho.quantidade(EXPRESS) == 5
    assert not carrinho.botao_mais_habilitado(EXPRESS), "não pode passar de 5"


@pytest.mark.positivo
def test_remover_item_atualiza_lista_e_total(carrinho):
    carrinho.remover(EXPRESS)
    carrinho.wait.until(lambda d: carrinho.qtd_itens() == 1)

    assert not any("Abdução Express" in n for n in carrinho.nomes_itens())
    assert carrinho.total() == PRECO_VACA
    assert carrinho.qtd_badge() == 1


@pytest.mark.positivo
@pytest.mark.parametrize(
    "codigo, percentual",
    [("TERRAPLANA10", 10), ("vaca50", 50)],
    ids=["cupom_10_porcento", "cupom_50_porcento_minusculo"],
)
def test_cupom_valido_aplica_desconto_percentual(carrinho, codigo, percentual):
    subtotal = PRECO_EXPRESS + PRECO_VACA

    mensagem = carrinho.aplicar_cupom(codigo)

    assert mensagem == f"Cupom {codigo.upper()} aplicado: {percentual}% de desconto."
    assert carrinho.subtotal() == subtotal
    assert carrinho.desconto() == pytest.approx(subtotal * percentual / 100)
    assert carrinho.total() == pytest.approx(subtotal * (100 - percentual) / 100)


@pytest.mark.negativo
@pytest.mark.parametrize(
    "codigo, mensagem",
    [
        ("ET100", "Cupom não reconhecido por nenhuma civilização."),
        ("   ", "Digite um cupom."),
    ],
    ids=["cupom_inexistente", "cupom_em_branco"],
)
def test_cupom_invalido_mostra_erro_e_nao_altera_total(carrinho, codigo, mensagem):
    total_antes = carrinho.total()

    assert carrinho.aplicar_cupom(codigo) == mensagem
    assert carrinho.desconto() == 0
    assert carrinho.total() == total_antes


@pytest.mark.negativo
def test_carrinho_vazio_bloqueia_agendamento(sessao, base_url):
    carrinho = CarrinhoPage(sessao, base_url).abrir().aguardar_rota()

    assert carrinho.mensagem_vazio().endswith("Seu raio trator está vazio. Nem uma vaquinha.")
    assert not carrinho.checkout_habilitado()

    # nem pela URL direta: checkout sem itens devolve ao carrinho
    sessao.get(base_url + "#/checkout")
    carrinho.aguardar_rota("/carrinho")
