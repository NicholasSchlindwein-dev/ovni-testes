"""Catálogo: listagem, busca (com debounce), filtro e ordenação."""
import pytest

from pages.catalogo_page import CatalogoPage


@pytest.fixture
def catalogo(sessao, base_url):
    return CatalogoPage(sessao, base_url)


@pytest.mark.positivo
def test_catalogo_lista_os_oito_pacotes(catalogo):
    assert len(catalogo.nomes()) == 8
    assert catalogo.contador() == "8 sinais detectados"


@pytest.mark.positivo
@pytest.mark.parametrize(
    "termo, esperados",
    [
        pytest.param("marte", ["Fim de Semana em Marte"], id="termo_no_nome"),
        pytest.param("bovino", ["Vaca VIP"], id="termo_so_na_descricao"),
        pytest.param("MEMORIA", ["Apagão de Memória"], id="ignora_acento_e_caixa"),
        pytest.param("pre",["Dissecação Simulada", "Sondagem Premium", "Abdução Express"], id="varios_resultados"),
    ],
)
def test_busca_retorna_apenas_pacotes_correspondentes(catalogo, termo, esperados):
    catalogo.buscar(termo)

    assert sorted(catalogo.nomes()) == sorted(esperados)


@pytest.mark.negativo
def test_busca_sem_correspondencia_mostra_estado_vazio(catalogo):
    catalogo.buscar("unicórnio")

    assert catalogo.nomes() == []
    assert catalogo.mensagem_vazio().endswith("Nenhum sinal detectado neste quadrante.")
    assert catalogo.contador() == "0 sinais detectados"


@pytest.mark.positivo
def test_filtro_por_categoria_exibe_somente_a_categoria(catalogo):
    catalogo.filtrar_categoria("Turismo")

    assert sorted(catalogo.nomes()) == ["Fim de Semana em Marte", "Tour Anéis de Saturno"]
    assert catalogo.categorias_exibidas() == {"TURISMO"}


@pytest.mark.positivo
@pytest.mark.parametrize(
    "rotulo, decrescente",
    [("Menor preço", False), ("Maior preço", True)],
    ids=["crescente", "decrescente"],
)
def test_ordenacao_por_preco(catalogo, rotulo, decrescente):
    catalogo.ordenar(rotulo)

    precos = catalogo.precos()
    assert len(precos) == 8
    assert precos == sorted(precos, reverse=decrescente)


@pytest.mark.negativo
def test_busca_e_filtro_combinados_sem_intersecao(catalogo):
    catalogo.filtrar_categoria("Rural")
    catalogo.buscar("marte")  # Marte existe, mas é Turismo

    assert catalogo.nomes() == []
    assert catalogo.existe(catalogo.VAZIO)
