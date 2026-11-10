# Plano de automação — O.V.N.I.

## 1. Sistema testado

**O.V.N.I. — Órgão de Viagens Não Identificadas**: agência fictícia de turismo por abdução alienígena. Aplicação web própria (HTML/CSS/JS, sem backend, estado em `localStorage`), criada para este trabalho — não é nenhum dos exemplos usados em aula.

Fluxos identificados na exploração manual:

| Fluxo | Tela | Regras observadas |
|---|---|---|
| Autenticação | `#/login` | Validação de campos, verificação assíncrona (~0,7 s), bloqueio após 3 senhas erradas, rotas protegidas |
| Catálogo | `#/catalogo` | 8 pacotes, busca com debounce (0,4 s) ignorando acento/caixa, filtro por categoria, ordenação |
| Carrinho ("raio trator") | `#/carrinho` | Quantidade de 1 a 5, remoção, cupons percentuais, totais, badge no menu |
| Agendamento | `#/checkout` | Nome ≥ 3 caracteres, idade 18–120, tipo sanguíneo, data futura DD/MM/AAAA, termo obrigatório; processamento assíncrono (~1,5 s); protocolo `ABD-000000` |
| Histórico | `#/abducoes` | Lista persistida, cancelamento com modal de confirmação |

## 2. Ferramenta

**Opção A — Selenium WebDriver + Python + pytest**, com Page Objects, fixtures e `pytest-html`.

## 3. Cenários levantados

Prioridade: **A** = bloqueia uso do sistema / envolve dinheiro; **M** = regra de negócio relevante; **B** = cosmético ou raro.

| # | Funcionalidade | Objetivo | Resultado esperado | Prior. | Automatizar? | Justificativa |
|---|---|---|---|---|---|---|
| 01 | Login | Entrar com credenciais válidas | Vai ao catálogo e mostra "Olá, Agente K" | A | Sim | Porta de entrada de todos os fluxos; repetido a cada regressão |
| 02 | Login | Rejeitar campos vazios / e-mail malformado / credenciais erradas | Mensagem específica; permanece no login | A | Sim | Vários dados para a mesma regra: ideal para parametrização |
| 03 | Login | Bloquear após 3 tentativas erradas | Mensagem de bloqueio, botão desabilitado, persiste ao recarregar | A | Sim | Regra de segurança; tedioso e sujeito a erro manualmente |
| 04 | Controle de acesso | Acessar rota interna sem sessão | Redireciona para o login | A | Sim | Falha aqui expõe todo o sistema; barato de automatizar |
| 05 | Logout | Encerrar sessão | Volta ao login, sessão removida, rota interna bloqueada | M | Sim | Complementa 04; estável |
| 06 | Catálogo | Listar todos os pacotes | 8 cards e contador "8 sinais detectados" | M | Sim | Teste de sanidade rápido |
| 07 | Catálogo | Buscar por nome, descrição, sem acento | Só os pacotes correspondentes | M | Sim | Orientado a dados; exige sincronização com o debounce |
| 08 | Catálogo | Buscar termo inexistente | Estado vazio e contador zero | M | Sim | Caminho negativo determinístico |
| 09 | Catálogo | Filtrar por categoria | Só pacotes da categoria | M | Sim | Regra simples e estável |
| 10 | Catálogo | Ordenar por preço (asc/desc) | Lista em ordem numérica | M | Sim | Conferir ordem de 8 preços à mão é propenso a erro |
| 11 | Catálogo | Combinar busca e filtro sem interseção | Estado vazio | B | Sim | Custo marginal baixo reaproveitando o page object |
| 12 | Carrinho | Adicionar pacotes pelo catálogo | Badge incrementa, aviso aparece, itens e total corretos | A | Sim | Caminho crítico de venda |
| 13 | Carrinho | Aumentar quantidade | Subtotal, total e badge recalculados | A | Sim | Cálculo monetário |
| 14 | Carrinho | Respeitar limites 1–5 | Botões − e + desabilitam nos limites | M | Sim | Valor-limite; fácil de esquecer em teste manual |
| 15 | Carrinho | Remover item | Item some, total e badge atualizam | M | Sim | Cálculo monetário |
| 16 | Cupom | Aplicar cupom válido (10% e 50%, minúsculas) | Desconto e total corretos | A | Sim | Dinheiro; parametrizável |
| 17 | Cupom | Rejeitar cupom inexistente / em branco | Mensagem de erro; total inalterado | M | Sim | Negativo determinístico |
| 18 | Carrinho | Impedir agendamento com carrinho vazio | Botão desabilitado; URL direta devolve ao carrinho | A | Sim | Evita pedido sem itens |
| 19 | Agendamento | Concluir com dados válidos | Protocolo `ABD-\d{6}`, carrinho esvazia, registro "AGENDADA" no histórico | A | Sim | Fluxo ponta a ponta mais importante |
| 20 | Agendamento | Cobrar total com cupom | Total do checkout e da confirmação com desconto | A | Sim | Integração carrinho → checkout |
| 21 | Agendamento | Aceitar idades-limite 18 e 120 | Agendamento concluído | M | Sim | Análise de valor-limite |
| 22 | Agendamento | Rejeitar cada campo inválido (10 variações) | Erro só no campo inválido; nada é gravado | A | Sim | Data-driven (JSON); 10 combinações manuais a cada regressão é inviável |
| 23 | Agendamento | Enviar formulário em branco | Todos os campos acusam erro; carrinho intacto | M | Sim | Complementa 22 |
| 24 | Histórico | Exibir estado vazio | Mensagem de histórico vazio | B | Sim | Rápido e estável |
| 25 | Histórico | Cancelar abdução | Status "CANCELADA", sem botão, persiste ao recarregar, demais intactas | A | Sim | Altera estado persistido |
| 26 | Histórico | Desistir no modal | Status permanece "AGENDADA" | M | Sim | Negativo do 25 |
| 27 | Segurança | Nome com HTML no histórico | Exibido como texto; script não executa | M | Sim | Regressão de XSS é silenciosa para o olho humano |
| 28 | Visual | Animações (disco, glitch, letreiro), cores neon | Aparência conforme o design | B | **Não** | Julgamento subjetivo; asserção por pixel seria frágil. Revisão visual manual |
| 29 | Responsividade | Layout em celular (< 700 px) | Filtros e formulário em uma coluna | B | **Não** | Melhor verificado por exploração manual em dispositivos reais; baixo risco funcional |
| 30 | Acessibilidade | Navegação por teclado e leitor de tela | Foco visível, rótulos lidos | M | **Não** (nesta suíte) | Exige ferramenta específica (axe) e avaliação humana; fora do escopo de Selenium funcional |
| 31 | Aviso (toast) | Sumir após 2,5 s | Aviso desaparece sozinho | B | **Não** | Dependente de tempo: teste lento e instável para ganho mínimo |
| 32 | Protocolo | Unicidade entre agendamentos | Protocolos nunca se repetem | B | **Não** | Geração aleatória: colisão não é reproduzível via UI; caberia teste unitário |
| 33 | Compatibilidade | Firefox / Edge | Mesmo comportamento | B | **Não** (por ora) | Suíte roda em Chrome; bastaria nova fixture, adiado por custo de tempo de execução |

## 4. Cenários implementados

Todos os marcados "Sim" (01–27), em 5 módulos:

| Módulo | Cenários | Testes executados |
|---|---|---|
| `tests/test_login.py` | 01–05 | 12 |
| `tests/test_catalogo.py` | 06–11 | 10 |
| `tests/test_carrinho.py` | 12–18 | 9 |
| `tests/test_checkout.py` | 19–23 | 15 |
| `tests/test_abducoes.py` | 24–27 | 4 |
| **Total** | **27 cenários** | **50 (21 positivos, 29 negativos)** |

A diferença entre cenários e testes vem da parametrização: cada conjunto de dados cobre uma classe de equivalência ou valor-limite distinto (ex.: idade 17, 121 e não numérica), não repetições arbitrárias.
