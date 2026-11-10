/* O.V.N.I. — Órgão de Viagens Não Identificadas
   SPA sem backend: estado em localStorage, rotas por hash. */
(function () {
  'use strict';

  const USUARIO = { email: 'agente@ovni.gov', senha: 'area51', nome: 'Agente K' };
  const MAX_TENTATIVAS = 3;
  const MAX_QTD = 5;
  const CUPONS = { TERRAPLANA10: 10, VACA50: 50 };
  const CATEGORIAS = { rapida: 'Rápida', turismo: 'Turismo', cientifica: 'Científica', rural: 'Rural' };

  const PACOTES = [
    { id: 1, icone: '🛸', nome: 'Abdução Express', cat: 'rapida', preco: 199, desc: 'Subiu, girou, desceu. Você volta antes do café esfriar.' },
    { id: 2, icone: '🪐', nome: 'Tour Anéis de Saturno', cat: 'turismo', preco: 1499, desc: 'Passeio panorâmico com guia que fala 4 milhões de idiomas.' },
    { id: 3, icone: '🔬', nome: 'Sondagem Premium', cat: 'cientifica', preco: 899, desc: 'Instrumentos aquecidos e playlist relaxante. Nota 5 no ReclameAli.' },
    { id: 4, icone: '🐄', nome: 'Vaca VIP', cat: 'rural', preco: 349, desc: 'Traga seu bovino favorito. Feno incluso na cabine.' },
    { id: 5, icone: '🌾', nome: 'Círculo na Plantação Personalizado', cat: 'rural', preco: 599, desc: 'Seu logotipo num milharal. Arte entregue em até 3 luas.' },
    { id: 6, icone: '🔴', nome: 'Fim de Semana em Marte', cat: 'turismo', preco: 2999, desc: 'Duas noites na cratera Gale. Oxigênio cobrado à parte.' },
    { id: 7, icone: '🧠', nome: 'Apagão de Memória', cat: 'rapida', preco: 99, desc: 'Esqueça aquele vexame de 2014. Procedimento indolor (você não vai lembrar).' },
    { id: 8, icone: '🧪', nome: 'Dissecação Simulada', cat: 'cientifica', preco: 1299, desc: 'Totalmente reversível. Quase sempre.' }
  ];

  /* ---------- utilidades ---------- */
  const db = {
    get(k, padrao) { try { const v = JSON.parse(localStorage.getItem(k)); return v === null ? padrao : v; } catch (e) { return padrao; } },
    set(k, v) { localStorage.setItem(k, JSON.stringify(v)); },
    del(k) { localStorage.removeItem(k); }
  };
  const $ = (sel, raiz) => (raiz || document).querySelector(sel);
  const app = $('#app');
  const brl = n => 'R$ ' + n.toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const semAcento = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const pacote = id => PACOTES.find(p => p.id === id);

  const sessao = () => db.get('ovni_sessao', null);
  const carrinho = () => db.get('ovni_carrinho', []);
  const abducoes = () => db.get('ovni_abducoes', []);

  function totais() {
    const subtotal = carrinho().reduce((s, i) => s + pacote(i.id).preco * i.qtd, 0);
    const cupom = db.get('ovni_cupom', null);
    const desconto = cupom && CUPONS[cupom] ? subtotal * CUPONS[cupom] / 100 : 0;
    return { subtotal, desconto, total: subtotal - desconto, cupom };
  }

  let toastTimer;
  function toast(msg) {
    const t = $('#toast');
    t.textContent = msg; t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.hidden = true; }, 2500);
  }

  function camada(html) {
    const c = $('#camada');
    if (html === null) { c.hidden = true; c.innerHTML = ''; return c; }
    c.innerHTML = html; c.hidden = false; return c;
  }

  /* ---------- navegação ---------- */
  function nav(rota) {
    const s = sessao();
    const n = $('#nav');
    if (!s) { n.innerHTML = ''; return; }
    const qtd = carrinho().reduce((a, i) => a + i.qtd, 0);
    const link = (r, id, txt) => `<a href="#${r}" data-testid="${id}" class="${rota === r ? 'ativo' : ''}">${txt}</a>`;
    n.innerHTML =
      `<span class="saudacao" data-testid="saudacao">Olá, ${esc(s.nome)}</span>` +
      link('/catalogo', 'nav-catalogo', 'Catálogo') +
      link('/carrinho', 'nav-carrinho', `Raio trator <span class="badge" data-testid="badge-carrinho">${qtd}</span>`) +
      link('/abducoes', 'nav-abducoes', 'Minhas abduções') +
      `<button type="button" data-testid="btn-sair">Sair</button>`;
    $('[data-testid=btn-sair]', n).onclick = () => { db.del('ovni_sessao'); location.hash = '#/login'; };
  }

  const ROTAS = {
    '/login': telaLogin,
    '/catalogo': telaCatalogo,
    '/carrinho': telaCarrinho,
    '/checkout': telaCheckout,
    '/confirmacao': telaConfirmacao,
    '/abducoes': telaAbducoes
  };

  function rotear() {
    let rota = location.hash.replace(/^#/, '') || '/catalogo';
    if (!ROTAS[rota]) rota = '/catalogo';
    if (!sessao() && rota !== '/login') { location.hash = '#/login'; return; }
    if (sessao() && rota === '/login') { location.hash = '#/catalogo'; return; }
    camada(null);
    nav(rota);
    app.dataset.rota = rota;
    ROTAS[rota]();
  }

  /* ---------- login ---------- */
  function telaLogin() {
    const bloqueado = () => db.get('ovni_tentativas', 0) >= MAX_TENTATIVAS;
    const MSG_BLOQUEIO = 'Acesso bloqueado. Os Homens de Preto foram notificados.';
    app.innerHTML = `
      <form class="painel estreito" id="form-login" novalidate>
        <h1>Identifique-se</h1>
        <p class="sub">Acesso restrito a agentes credenciados.</p>
        <label for="email">E-mail do agente</label>
        <input type="text" id="email" data-testid="login-email" autocomplete="off">
        <label for="senha">Senha</label>
        <input type="password" id="senha" data-testid="login-senha">
        <p class="erro" data-testid="login-erro" role="alert"></p>
        <button class="btn" type="submit" data-testid="login-entrar">Entrar na nave</button>
        <p class="dica">Credencial de demonstração: agente@ovni.gov / area51</p>
      </form>`;
    const form = $('#form-login'), erro = $('[data-testid=login-erro]'), btn = $('[data-testid=login-entrar]');
    if (bloqueado()) { erro.textContent = MSG_BLOQUEIO; btn.disabled = true; }

    form.onsubmit = ev => {
      ev.preventDefault();
      if (bloqueado()) return;
      const email = $('#email').value.trim(), senha = $('#senha').value;
      erro.textContent = '';
      if (!email) { erro.textContent = 'Informe o e-mail do agente.'; return; }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { erro.textContent = 'E-mail em formato inválido.'; return; }
      if (!senha) { erro.textContent = 'Informe a senha.'; return; }

      btn.disabled = true; btn.textContent = 'Escaneando retina...';
      setTimeout(() => {
        if (email.toLowerCase() === USUARIO.email && senha === USUARIO.senha) {
          db.del('ovni_tentativas');
          db.set('ovni_sessao', { email: USUARIO.email, nome: USUARIO.nome });
          location.hash = '#/catalogo';
          return;
        }
        const n = db.get('ovni_tentativas', 0) + 1;
        db.set('ovni_tentativas', n);
        btn.textContent = 'Entrar na nave';
        if (n >= MAX_TENTATIVAS) { erro.textContent = MSG_BLOQUEIO; return; }
        btn.disabled = false;
        erro.textContent = `Credenciais não reconhecidas. Tentativa ${n} de ${MAX_TENTATIVAS}.`;
      }, 700);
    };
  }

  /* ---------- catálogo ---------- */
  function telaCatalogo() {
    app.innerHTML = `
      <h1>Catálogo de abduções</h1>
      <p class="sub">Escolha sua experiência. A gravidade é opcional.</p>
      <div class="filtros">
        <div><label for="busca">Buscar sinal</label>
          <input type="text" id="busca" data-testid="busca" placeholder="ex.: marte, vaca, memória..."></div>
        <div><label for="categoria">Categoria</label>
          <select id="categoria" data-testid="filtro-categoria">
            <option value="">Todas</option>
            ${Object.entries(CATEGORIAS).map(([v, t]) => `<option value="${v}">${t}</option>`).join('')}
          </select></div>
        <div><label for="ordem">Ordenar</label>
          <select id="ordem" data-testid="ordenacao">
            <option value="">Relevância cósmica</option>
            <option value="preco-asc">Menor preço</option>
            <option value="preco-desc">Maior preço</option>
            <option value="nome">Nome (A-Z)</option>
          </select></div>
      </div>
      <p class="contador" data-testid="contador-resultados"></p>
      <section class="grade" id="grade" data-testid="grade" data-estado="pronto"></section>`;

    const grade = $('#grade'), busca = $('#busca'), cat = $('#categoria'), ordem = $('#ordem');

    function listar() {
      const termo = semAcento(busca.value.trim());
      let itens = PACOTES.filter(p =>
        (!cat.value || p.cat === cat.value) &&
        (!termo || semAcento(p.nome + ' ' + p.desc).includes(termo)));
      if (ordem.value === 'preco-asc') itens = itens.slice().sort((a, b) => a.preco - b.preco);
      if (ordem.value === 'preco-desc') itens = itens.slice().sort((a, b) => b.preco - a.preco);
      if (ordem.value === 'nome') itens = itens.slice().sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));

      $('[data-testid=contador-resultados]').textContent =
        itens.length === 1 ? '1 sinal detectado' : `${itens.length} sinais detectados`;
      grade.innerHTML = itens.length ? itens.map(p => `
        <article class="card" data-testid="pacote" data-id="${p.id}" data-preco="${p.preco}">
          <div class="card-icone">${p.icone}</div>
          <h3 class="card-nome">${p.nome}</h3>
          <span class="card-cat">${CATEGORIAS[p.cat]}</span>
          <p class="card-desc">${p.desc}</p>
          <div class="card-preco">${brl(p.preco)}</div>
          <button class="btn" type="button" data-testid="btn-abduzir" data-id="${p.id}">Abduzir</button>
        </article>`).join('')
        : `<div class="vazio" data-testid="vazio" style="grid-column:1/-1"><b>📡</b>Nenhum sinal detectado neste quadrante.</div>`;
      grade.dataset.estado = 'pronto';
    }

    let espera;
    busca.oninput = () => {            // busca com debounce: exige sincronização nos testes
      grade.dataset.estado = 'sintonizando';
      clearTimeout(espera);
      espera = setTimeout(listar, 400);
    };
    cat.onchange = listar;
    ordem.onchange = listar;

    grade.onclick = ev => {
      const b = ev.target.closest('[data-testid=btn-abduzir]');
      if (!b) return;
      const id = Number(b.dataset.id), c = carrinho(), item = c.find(i => i.id === id);
      if (item && item.qtd >= MAX_QTD) { toast(`Limite de ${MAX_QTD} por pacote: a nave não aguenta.`); return; }
      if (item) item.qtd++; else c.push({ id, qtd: 1 });
      db.set('ovni_carrinho', c);
      nav('/catalogo');
      toast(`${pacote(id).nome} fisgado pelo raio trator!`);
    };
    listar();
  }

  /* ---------- carrinho ---------- */
  function telaCarrinho(msgCupom) {
    const c = carrinho(), t = totais();
    if (!c.length) {
      db.del('ovni_cupom');
      app.innerHTML = `
        <h1>Raio trator</h1>
        <div class="vazio" data-testid="carrinho-vazio"><b>🕳️</b>Seu raio trator está vazio. Nem uma vaquinha.</div>
        <div class="acoes">
          <a class="btn sec" href="#/catalogo" data-testid="voltar-catalogo">Ver catálogo</a>
          <button class="btn" type="button" data-testid="btn-checkout" disabled>Agendar abdução</button>
        </div>`;
      return;
    }
    app.innerHTML = `
      <h1>Raio trator</h1>
      <p class="sub">Itens capturados aguardando embarque.</p>
      <div class="painel">
        <table>
          <thead><tr><th>Pacote</th><th>Preço</th><th>Qtd.</th><th>Subtotal</th><th></th></tr></thead>
          <tbody>${c.map(i => { const p = pacote(i.id); return `
            <tr data-testid="item-carrinho" data-id="${p.id}">
              <td data-testid="item-nome">${p.icone} ${p.nome}</td>
              <td>${brl(p.preco)}</td>
              <td><span class="qtd-caixa">
                <button class="btn mini sec" type="button" data-acao="menos" data-testid="btn-menos" ${i.qtd <= 1 ? 'disabled' : ''}>−</button>
                <span data-testid="qtd">${i.qtd}</span>
                <button class="btn mini sec" type="button" data-acao="mais" data-testid="btn-mais" ${i.qtd >= MAX_QTD ? 'disabled' : ''}>+</button>
              </span></td>
              <td data-testid="item-subtotal">${brl(p.preco * i.qtd)}</td>
              <td><button class="btn mini perigo" type="button" data-acao="remover" data-testid="btn-remover">Devolver</button></td>
            </tr>`; }).join('')}
          </tbody>
        </table>
        <div class="cupom">
          <div style="flex:1"><label for="cupom">Cupom intergaláctico</label>
            <input type="text" id="cupom" data-testid="cupom" value="${t.cupom ? esc(t.cupom) : ''}"></div>
          <button class="btn sec" type="button" data-testid="btn-cupom">Aplicar</button>
        </div>
        <p class="${msgCupom && msgCupom.ok ? 'ok' : 'erro'}" data-testid="msg-cupom">${msgCupom ? esc(msgCupom.txt) : ''}</p>
        <div class="totais">
          <div><span>Subtotal</span><span data-testid="subtotal">${brl(t.subtotal)}</span></div>
          <div><span>Desconto</span><span data-testid="desconto">${brl(t.desconto)}</span></div>
          <div class="total"><span>Total</span><span data-testid="total">${brl(t.total)}</span></div>
        </div>
      </div>
      <div class="acoes">
        <a class="btn sec" href="#/catalogo" data-testid="voltar-catalogo">Continuar abduzindo</a>
        <button class="btn" type="button" data-testid="btn-checkout">Agendar abdução</button>
      </div>`;

    $('tbody', app).onclick = ev => {
      const b = ev.target.closest('[data-acao]');
      if (!b) return;
      const id = Number(b.closest('tr').dataset.id);
      let lista = carrinho();
      const item = lista.find(i => i.id === id);
      if (b.dataset.acao === 'mais' && item.qtd < MAX_QTD) item.qtd++;
      if (b.dataset.acao === 'menos' && item.qtd > 1) item.qtd--;
      if (b.dataset.acao === 'remover') lista = lista.filter(i => i.id !== id);
      db.set('ovni_carrinho', lista);
      nav('/carrinho');
      telaCarrinho();
    };
    $('[data-testid=btn-cupom]').onclick = () => {
      const codigo = $('#cupom').value.trim().toUpperCase();
      if (!codigo) { db.del('ovni_cupom'); telaCarrinho({ ok: false, txt: 'Digite um cupom.' }); return; }
      if (!CUPONS[codigo]) { db.del('ovni_cupom'); telaCarrinho({ ok: false, txt: 'Cupom não reconhecido por nenhuma civilização.' }); return; }
      db.set('ovni_cupom', codigo);
      telaCarrinho({ ok: true, txt: `Cupom ${codigo} aplicado: ${CUPONS[codigo]}% de desconto.` });
    };
    $('[data-testid=btn-checkout]').onclick = () => { location.hash = '#/checkout'; };
  }

  /* ---------- checkout ---------- */
  function lerData(s) {
    const m = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(s);
    if (!m) return null;
    const d = new Date(+m[3], +m[2] - 1, +m[1]);
    return (d.getFullYear() === +m[3] && d.getMonth() === +m[2] - 1 && d.getDate() === +m[1]) ? d : null;
  }

  function telaCheckout() {
    if (!carrinho().length) { location.hash = '#/carrinho'; return; }
    const t = totais();
    const campo = (id, rotulo, extra) => `
      <div><label for="${id}">${rotulo}</label>
        <input type="text" id="${id}" data-testid="ck-${id}" ${extra || ''}>
        <p class="erro" data-testid="erro-${id}"></p></div>`;
    app.innerHTML = `
      <h1>Ficha do espécime</h1>
      <p class="sub">Precisamos de alguns dados antes de ligar o raio. Total a pagar: <b data-testid="ck-total">${brl(t.total)}</b></p>
      <form class="painel" id="form-checkout" novalidate>
        ${campo('nome', 'Nome completo do espécime')}
        <div class="duas">
          ${campo('idade', 'Idade (anos terrestres)', 'inputmode="numeric"')}
          <div><label for="sangue">Tipo sanguíneo</label>
            <select id="sangue" data-testid="ck-sangue">
              <option value="">Selecione...</option>
              ${['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Verde'].map(s => `<option>${s}</option>`).join('')}
            </select>
            <p class="erro" data-testid="erro-sangue"></p></div>
        </div>
        ${campo('data', 'Data da abdução', 'placeholder="DD/MM/AAAA" maxlength="10"')}
        <label class="check"><input type="checkbox" id="termo" data-testid="ck-termo">
          Li e aceito o termo de sondagem (incluindo a cláusula 51).</label>
        <p class="erro" data-testid="erro-termo"></p>
        <button class="btn" type="submit" data-testid="ck-confirmar">Confirmar abdução</button>
      </form>`;

    $('#form-checkout').onsubmit = ev => {
      ev.preventDefault();
      const v = { nome: $('#nome').value.trim(), idade: $('#idade').value.trim(), sangue: $('#sangue').value, data: $('#data').value.trim(), termo: $('#termo').checked };
      const erros = {};
      if (v.nome.length < 3) erros.nome = 'Informe o nome do espécime (mínimo 3 caracteres).';
      if (!/^\d+$/.test(v.idade) || +v.idade < 18 || +v.idade > 120) erros.idade = 'Idade deve estar entre 18 e 120 anos terrestres.';
      if (!v.sangue) erros.sangue = 'Selecione o tipo sanguíneo.';
      const d = lerData(v.data), hoje = new Date(); hoje.setHours(0, 0, 0, 0);
      if (!d) erros.data = 'Data inválida. Use o formato DD/MM/AAAA.';
      else if (d <= hoje) erros.data = 'A data deve ser no futuro. Viagem no tempo é outro departamento.';
      if (!v.termo) erros.termo = 'É obrigatório aceitar o termo de sondagem.';

      ['nome', 'idade', 'sangue', 'data', 'termo'].forEach(k => {
        $(`[data-testid=erro-${k}]`).textContent = erros[k] || '';
        $('#' + k).classList.toggle('invalido', !!erros[k]);
      });
      if (Object.keys(erros).length) return;

      camada(`<div class="painel" data-testid="processando"><h1>Calibrando raio trator</h1>
        <p>Não olhe diretamente para a luz.</p><div class="barra"><i></i></div></div>`);
      setTimeout(() => {
        const tt = totais();
        const reg = {
          protocolo: 'ABD-' + String(Math.floor(Math.random() * 1e6)).padStart(6, '0'),
          nome: v.nome, data: v.data, total: tt.total, status: 'AGENDADA',
          itens: carrinho().map(i => ({ nome: pacote(i.id).nome, qtd: i.qtd }))
        };
        db.set('ovni_abducoes', [reg].concat(abducoes()));
        db.del('ovni_carrinho'); db.del('ovni_cupom');
        location.hash = '#/confirmacao';
      }, 1500);
    };
  }

  function telaConfirmacao() {
    const a = abducoes()[0];
    if (!a) { location.hash = '#/catalogo'; return; }
    app.innerHTML = `
      <div class="painel" style="text-align:center" data-testid="confirmacao">
        <h1>Abdução agendada!</h1>
        <p>Guarde seu protocolo. Ou não — nós sabemos onde você mora.</p>
        <div class="protocolo" data-testid="protocolo">${a.protocolo}</div>
        <p>Espécime: <b data-testid="conf-nome">${esc(a.nome)}</b> · Data: <b data-testid="conf-data">${esc(a.data)}</b> ·
           Total: <b data-testid="conf-total">${brl(a.total)}</b></p>
        <a class="btn" href="#/abducoes" data-testid="ver-abducoes">Ver minhas abduções</a>
      </div>`;
  }

  /* ---------- histórico ---------- */
  function telaAbducoes() {
    const lista = abducoes();
    app.innerHTML = `
      <h1>Minhas abduções</h1>
      <p class="sub">Histórico oficial (o extraoficial é confidencial).</p>
      ${lista.length ? `<div class="painel"><table>
        <thead><tr><th>Protocolo</th><th>Espécime</th><th>Data</th><th>Total</th><th>Status</th><th></th></tr></thead>
        <tbody>${lista.map(a => `
          <tr data-testid="abducao" data-protocolo="${a.protocolo}">
            <td data-testid="ab-protocolo">${a.protocolo}</td>
            <td data-testid="ab-nome">${esc(a.nome)}</td>
            <td>${esc(a.data)}</td>
            <td data-testid="ab-total">${brl(a.total)}</td>
            <td><span class="status ${a.status}" data-testid="ab-status">${a.status}</span></td>
            <td>${a.status === 'AGENDADA' ? '<button class="btn mini perigo" type="button" data-testid="btn-cancelar">Cancelar</button>' : ''}</td>
          </tr>`).join('')}
        </tbody></table></div>`
        : `<div class="vazio" data-testid="abducoes-vazio"><b>👽</b>Você ainda não foi abduzido. Que vida pacata.</div>`}`;

    const corpo = $('tbody', app);
    if (!corpo) return;
    corpo.onclick = ev => {
      const b = ev.target.closest('[data-testid=btn-cancelar]');
      if (!b) return;
      const prot = b.closest('tr').dataset.protocolo;
      const c = camada(`<div class="painel" data-testid="modal-cancelar" role="dialog" aria-modal="true">
        <h1>Desistir?</h1><p>Cancelar a abdução <b>${prot}</b>? Os tripulantes ficarão magoados.</p>
        <div class="acoes" style="justify-content:center">
          <button class="btn sec" type="button" data-testid="modal-nao">Manter</button>
          <button class="btn perigo" type="button" data-testid="modal-sim">Sim, cancelar</button>
        </div></div>`);
      $('[data-testid=modal-nao]', c).onclick = () => camada(null);
      $('[data-testid=modal-sim]', c).onclick = () => {
        db.set('ovni_abducoes', abducoes().map(a => a.protocolo === prot ? Object.assign({}, a, { status: 'CANCELADA' }) : a));
        camada(null);
        telaAbducoes();
        toast(`Abdução ${prot} cancelada.`);
      };
    };
  }

  window.addEventListener('hashchange', rotear);
  rotear();
})();
