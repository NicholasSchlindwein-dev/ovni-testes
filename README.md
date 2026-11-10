# O.V.N.I. — suíte de testes automatizados

Avaliação da 2ª etapa: suíte **Selenium WebDriver + Python + pytest** sobre o **O.V.N.I. — Órgão de Viagens Não Identificadas**, uma agência fictícia de abduções alienígenas criada especialmente para este trabalho.

- Planejamento (cenários, prioridade, automatizar ou não, justificativa): [`docs/PLANO_DE_TESTES.md`](docs/PLANO_DE_TESTES.md)
- Evidências da execução: [`evidencias/relatorio.html`](evidencias/relatorio.html), `evidencias/junit.xml`, `evidencias/screenshots/` e vídeo em `evidencias/video/suite_completa.mp4`

## Como executar

Requisitos: Python 3.10+ e Google Chrome. O driver é baixado sozinho pelo Selenium Manager.

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
pytest                            # suíte completa, headless
```

Variações úteis:

```bash
pytest -m smoke                   # só os fluxos críticos
pytest -m negativo                # só testes negativos
pytest tests/test_checkout.py     # um módulo
HEADED=1 pytest -m smoke          # com o navegador visível (PowerShell: $env:HEADED=1; pytest -m smoke)
```

Gravar vídeo da execução (PowerShell):

```powershell
$env:VIDEO=1; pytest; Remove-Item Env:VIDEO
```

Gera `evidencias/video/suite_completa.mp4` e um MP4 por teste em `evidencias/video/por_teste/`, com nome e resultado do teste na legenda. Nesse modo há uma pausa de 0,4 s após cada clique/digitação, apenas para o espectador acompanhar; a execução normal não usa pausa fixa.

Não é preciso subir o site: uma fixture inicia um servidor HTTP local para a pasta `site/` e o derruba no fim. Para explorar manualmente: `python -m http.server 8000 --directory site` e abrir `http://localhost:8000` (login `agente@ovni.gov` / `area51`).

## Estrutura

```
site/                      sistema sob teste (HTML + CSS + JS, estado em localStorage)
tests/
  conftest.py              setup/teardown: servidor, driver, sessão, evidências
  gravador.py              gravação opcional da execução em MP4
  pages/                   Page Objects (um por tela) + base com esperas explícitas
  data/checkout_invalidos.json   massa dos testes orientados a dados
  test_login.py            autenticação, bloqueio, rotas protegidas, logout
  test_catalogo.py         listagem, busca, filtro, ordenação
  test_carrinho.py         itens, quantidades, cupons, totais
  test_checkout.py         validações do formulário e agendamento ponta a ponta
  test_abducoes.py         histórico, cancelamento, persistência
docs/PLANO_DE_TESTES.md    planejamento da automação
evidencias/                relatório HTML, JUnit XML e screenshots
```

## Onde cada conteúdo da disciplina aparece

| Conteúdo | Onde |
|---|---|
| Seletores | `data-testid` via CSS (`base_page.tid`), CSS composto por linha da tabela (`carrinho_page._na_linha`), XPath relativo do título ao botão do card (`catalogo_page.abduzir`) |
| Esperas e sincronização | Só esperas explícitas (`WebDriverWait`), nenhum `sleep`: debounce da busca (`CatalogoPage.buscar`), login assíncrono (`aguardar_erro_contendo`), overlay de processamento (`CheckoutPage.aguardar_confirmacao`), modal (`AbducoesPage`) |
| Assertions | Todo teste verifica o efeito de negócio: valores monetários, regex do protocolo, status, rota, conteúdo do `localStorage` — não apenas "elemento existe" |
| Positivos e negativos | Marcadores `positivo` (21 testes) e `negativo` (29 testes) |
| Reutilização | Page Objects, `BasePage`, fixtures `sessao` e `carrinho_com` |
| Parametrização / dados | `@pytest.mark.parametrize` em login, busca, ordenação, cupons; checkout negativo lido de JSON |
| Setup e teardown | Fixtures com `yield`: servidor por sessão, navegador limpo por teste |
| Organização | Um módulo por funcionalidade, marcadores `smoke`/`positivo`/`negativo` em `pytest.ini` |
| Relatórios e evidências | `pytest-html` autocontido com screenshot e URL final de cada teste; JUnit XML; PNGs nomeados por teste |

## Investigação de falha

Na primeira execução completa o resultado foi **49 aprovados, 1 reprovado**:

```
FAILED tests/test_carrinho.py::test_adicionar_pacotes_pelo_catalogo_atualiza_badge_e_carrinho
ElementClickInterceptedException: element click intercepted: Element <button ... data-testid="btn-abduzir" data-id="4">
is not clickable at point (1071, 722). Other element would receive the click: <div id="toast" class="toast" ...>
```

- **Sintoma:** o segundo clique em "Abduzir" foi recebido por outro elemento.
- **Evidência:** `evidencias/screenshots/test_adicionar_pacotes_pelo_catalogo_atualiza_badge_e_carrinho__FALHOU.png` mostra o aviso verde do primeiro item sobre o botão do card "Vaca VIP".
- **Causa:** defeito do **site**, não do teste — o aviso fica 2,5 s sobre o canto inferior direito e bloqueia cliques nos cards atrás dele. Um usuário real rápido teria o mesmo problema.
- **Correção:** `pointer-events: none` no `.toast` (`site/style.css`). Contornar no teste (esperar o aviso sumir ou clicar via JavaScript) esconderia o defeito.
- **Reteste:** 50 aprovados, 0 reprovados.

## Resultado atual

50 testes, 50 aprovados, cerca de 4 min 30 s em Chrome headless (um navegador novo por teste, para isolar o `localStorage`).
