# Resumo do projeto — Orçamento Familiar (Henrique & Carol) / "cowhand"

Este documento resume tudo o que foi decidido e construído nesta conversa, para
retomar o trabalho no Claude Code sem perder contexto.

## 1. Contexto e pedido original

Henrique tinha duas planilhas separadas:
- **"Orçamento Carol.xlsx"** — despesas fixas da casa, controlada por ele.
- **"Planejamento Pessoal Carol.xlsx"** — gastos pessoais da Carol no cartão.

Pedido inicial: unificar as duas em uma única planilha colaborativa, com categorias
padronizadas, detalhamento das despesas do cartão (pet shop, combustível,
assinaturas, supermercado), uma aba de Dashboard visual (renda conjunta, gastos por
categoria, saldo mensal, visão individual vs. conjunta) e uma aba de Metas
Financeiras (aportes de investimento, fundo de férias, compra de carro da Carol).

**Isso já foi entregue** como um arquivo `.xlsx` funcional (fórmulas, tabelas,
gráficos, validado com recálculo no LibreOffice, 0 erros). Não é o foco deste
resumo, mas fica registrado que os dados de origem (categorias, valores reais de
fatura de cartão, assinaturas, etc.) vieram de lá.

Depois da planilha, Henrique perguntou se dava para transformar isso em um
**sistema web para ele e a Carol usarem juntos**, com um único link compartilhado,
sincronizado automaticamente. A resposta escolhida foi: **app web personalizado
(link único)** — não uma migração para Google Sheets.

## 2. O que foi construído

Um app web de página única (`index.html`), autocontido (HTML+CSS+JS embutidos,
sem build step, sem dependências de servidor), com 5 seções:

1. **Dashboard** — KPIs (renda conjunta, gasto sem investimento, aportes de
   investimento, saldo do mês, taxa de poupança), gastos por categoria (lista de
   barras), gastos por responsável (Ele/Ela/Ambos, barra segmentada), Previsível vs.
   Variável vs. Investimento, mini-visão das metas.
2. **Lançamentos** — CRUD de transações (data, descrição, categoria, subcategoria,
   forma de pagamento, responsável, tipo, parcela, valor, status), com busca e
   filtros por categoria/responsável.
3. **Despesas Recorrentes & Cartão** — as 27 despesas recorrentes já mapeadas da
   planilha, com "valor esperado" editável e "valor real do mês" calculado
   automaticamente a partir dos lançamentos (ver lógica de matching abaixo).
4. **Metas** — as 3 metas (Aportes para Investimentos, Fundo de Férias, Aquisição
   de Carro da Carol), com valor atual/alvo/prazo/contribuição planejada editáveis,
   barra de progresso, contribuição do mês calculada, meses restantes e aporte
   necessário/mês.
5. **Ajustes** — renda de Henrique e Carol, seletor de tema (claro/escuro/sistema).

Mês selecionável no topo (input `type="month"`, guardado em localStorage — é
preferência local, não faz parte do estado sincronizado).

### Lógica de matching Recorrentes ↔ Lançamentos

Cada item recorrente tem `categoria` + `subcategoria` e, opcionalmente, uma
`chave` (palavra-chave). O "valor real do mês" de um item é a soma dos
lançamentos do mês cuja `categoria`+`subcategoria` batem; se o item tiver
`chave`, também filtra por essa palavra estar contida na descrição do
lançamento (case-insensitive). A `chave` só é necessária quando várias despesas
recorrentes dividem a mesma subcategoria (ex: 3 assinaturas de streaming
diferentes) — nos outros casos, categoria+subcategoria já é suficiente.

### Design

- Paleta: teal como cor de destaque (`#146356` claro / `#4FBFA8` escuro),
  categórica de 3 cores para Ele/Ela/Ambos e Previsível/Variável/Investimento
  (`#2a78d6`/`#eb6834`/`#1baf7a` no claro, `#3987e5`/`#d95926`/`#199e70` no
  escuro), cores de status good/critical.
- Tipografia: Sora (títulos/nav), Public Sans (corpo), IBM Plex Mono (números),
  via Google Fonts.
- Tema claro/escuro totalmente tokenizado (`:root`, `@media
  prefers-color-scheme`, `:root[data-theme]`).
- Layout: sidebar fixa no desktop, vira barra de abas inferior no mobile.
- Vários bugs de responsividade foram encontrados via screenshot e corrigidos:
  KPIs estourando a largura no mobile (faltava `min-width:0` nos grids), labels
  da barra de abas mobile quebrando linha (criado label curto `short` separado do
  label completo do desktop), e um filtro com `style` inline que não respeitava
  o breakpoint mobile (trocado por uma classe `.filtro-grid` responsiva).

## 3. Arquitetura técnica: auto-publicação ("quine")

O app roda dentro do visualizador de **Artifact** da Claude, que oferece uma
capability chamada `artifact`: a página chama `await claude.use('artifact')` e
depois `artifact.publish(html)` para salvar uma nova versão de si mesma — **toda
vez que alguém edita algo, o app publica o HTML inteiro de novo**, e todas as
outras pessoas com o link recarregam automaticamente para a versão nova. É assim
que Henrique e a Carol ficam sincronizados sem backend próprio.

Regra importante da API: `publish(html)` exige um documento HTML **completo**
(`<!doctype html>` até `</html>`), nunca construído a partir do DOM ao vivo
(`document.documentElement.outerHTML` conteria estado de execução). Por isso o
app se auto-representa: guarda uma cópia de si mesmo (escapada) dentro de uma
tag `<script id="tpl" type="text/plain">`, e reconstrói o HTML de publicação
substituindo dois tokens nessa cópia:

- `__APP_STATE_JSON__` → o novo estado (JSON.stringify do estado mutado)
- `__TPL_SELF__` → a própria cópia escapada (auto-referência)

Isso evita recursão infinita (só há um nível de indireção) mas cria um problema
sutil: qualquer `</script` literal dentro de **qualquer** `<script>` da página
(mesmo dentro de uma string JS, comentário, ou dado do usuário) fecha a tag no
nível do parser HTML, independente da sintaxe JS. A solução usada:

```js
var LT = String.fromCharCode(60); // '<' — nunca escrito literalmente como "<\/script"
var TAG_CASES = ['script', 'Script', 'SCRIPT'];
function escapeScriptClose(s){
  for (var i = 0; i < TAG_CASES.length; i++) {
    s = s.split(LT + '/' + TAG_CASES[i]).join(LT + '\\' + '/' + TAG_CASES[i]);
  }
  return s;
}
function unescapeScriptClose(s){
  for (var i = 0; i < TAG_CASES.length; i++) {
    s = s.split(LT + '\\' + '/' + TAG_CASES[i]).join(LT + '/' + TAG_CASES[i]);
  }
  return s;
}
```

O truque chave: as funções de escape/unescape constroem a substring perigosa
via concatenação em tempo de execução (`String.fromCharCode(60)` + `.split()` /
`.join()`), então o **código-fonte** nunca contém a sequência literal `</script`
em lugar nenhum — o que elimina qualquer ambiguidade entre "proteção adicionada
pelo escape" e "essa mesma sequência aparecendo por acaso no código-fonte das
próprias funções" (esse foi um bug real, encontrado e corrigido durante os
testes).

No lado Python (`build_app.py`), há uma auditoria de segurança que conta as
ocorrências literais de `</script` na fonte montada e falha a build se não for
exatamente 3 (as 3 tags reais: `app-state`, `tpl`, script principal).

### Fluxo de publicação/mutação

```js
function mutate(mutator){
  if (READONLY) { showToast('Este link está em modo somente leitura.', true); return; }
  var next = deepClone(STATE);
  mutator(next);
  next.updatedAt = new Date().toISOString();
  STATE = next;
  renderApp();       // otimista
  queuePublish();     // debounce ~700ms, agrupa edições rápidas em 1 publish
}
```

Tratamento de erros do `publish()` (por código, nunca por texto da mensagem):

- `conflict` → não faz nada; a plataforma já recarrega a view para a versão
  vencedora.
- `not_writer` / `not_granted` / `not_declared` / `capability_disabled` /
  `capability_removed` → entra em modo somente leitura permanente para essa view
  (esconde formulários de edição).
- `rate_limited` → não fica em loop de retry; mostra "alterações pendentes" com
  botão manual de "tentar novamente".
- `upstream_error` → tenta de novo uma vez, depois de um atraso curto
  aleatório.
- Quando a capability não está disponível (`window.claude` não existe — ex:
  hospedado fora do Artifact, como GitHub Pages ou Coolify) → modo "local":
  o app funciona normalmente na tela, mas nada persiste entre recarregamentos
  e nada sincroniza entre pessoas.

## 4. Modelo de dados

```js
STATE = {
  renda: { henrique: 11000, carol: 0 },   // valores mensais, editáveis em Ajustes
  transacoes: [ { id, data, descricao, categoria, subcategoria,
                  formaPagamento, responsavel, tipo, parcela, valor, status } ],
  recorrentes: [ /* 27 itens, ver abaixo */ ],
  metas: [ /* 3 itens, ver abaixo */ ],
  updatedAt: "2026-08-26T...",
}
```

- `CATEGORIAS` (14): Moradia, Educação, Veículos, Alimentação, Pet, Saúde,
  Cuidados Pessoais & Estética, Vestuário & Calçados, Assinaturas, Lazer &
  Recreação, Presentes, Dívidas & Empréstimos, Investimentos, Outros.
- `SUBCATEGORIAS` (43), `RESPONSAVEL_OPTS` = [Ele, Ela, Ambos],
  `TIPO_OPTS` = [Fixo, Variável, Recorrente Parcelado, Investimento],
  `FORMA_PGTO_OPTS` = [Cartão C6 (Henrique), Cartão Santander (Carol), Cartão
  Renner (Carol), Pix, Débito Automático, Boleto, Dinheiro],
  `STATUS_OPTS` = [Pago, Pendente, Agendado].
- **27 despesas recorrentes** (id, categoria, subcategoria, item, responsavel,
  forma, tipo, valorEsperado, parcela, obs, chave) — inclui, por exemplo:
  Condomínio (R$600), Financiamento do Compass (R$2.560,90), Combustível
  (R$1.071,22, sem chave — bate por categoria+subcategoria), Supermercado
  (R$1.617,98), Netflix (R$20,90, chave "Netflix"), Crunchyroll (R$3,90, chave
  "Crunchyroll"), iCloud (R$66,90), Torbox (R$16,65, chave "Torbox"), Claude
  Code (R$110, chave "Claude"), 3 profissionais de estética da Carol (Tina,
  Camila Maciel, Manu — cada uma com sua própria chave), psicóloga, clube,
  2 itens de "Lazer Diversos" (Cancha e HV, cada um com chave), aporte de
  investimento (conta poupança do filho Augusto) e empréstimo Nubank da Carol.
  A lista completa e exata está em `build_app.py` (variável `RECORRENTES`).
- **3 metas**: "Aportes para Investimentos" (subcategoria "Aporte
  Investimento"), "Fundo de Férias" (subcategoria "Fundo de Férias"),
  "Aquisição de Carro (Carol)" (subcategoria "Fundo Carro”) — todas com
  valorAtual/valorAlvo/prazo/contribPlanejada zerados/vazios inicialmente,
  para o usuário preencher.

## 5. Estrutura dos arquivos entregues (`cowhand.zip`)

- `build_app.py` — script Python (~1200 linhas) que gera o `index.html`.
  Contém: dados/constantes, CSS (design tokens, layout, componentes), JS do
  app (self-publish + toda a lógica de UI), o template HTML (`CORE`), e a
  lógica de build (substituição de placeholders + auditoria de segurança +
  escrita do arquivo final). Rodar com `python3 build_app.py` regenera
  `index.html` a partir do zero — é a fonte da verdade; editar `index.html`
  diretamente seria perdido na próxima geração.
- `index.html` — o app já gerado e testado, pronto para publicar.
- `test_app.py` — suíte de testes Playwright (assíncrono) que abre o
  `index.html` num Chromium headless e valida: estado inicial, ausência de
  `NaN`/`undefined`, fluxo de adicionar lançamentos via formulário, matching de
  recorrentes (com e sem `chave`), cálculo de metas, layout mobile (sidebar
  some, barra de abas aparece, sem overflow horizontal), diferença de tokens
  entre tema claro/escuro, o badge de status de sincronização, e um **round-trip
  completo do mecanismo de auto-publicação** (chama
  `window.__buildPublishHtml__(window.__STATE__)`, escreve o resultado em
  disco, recarrega, e confere que o estado bateu — incluindo um valor
  adversarial contendo `</script>` literal, para garantir que o escape
  funciona). Rodar com
  `pip install playwright && playwright install chromium && python3 test_app.py`.
- `README.md` — já explica a limitação de sincronização fora do Artifact.

Este resumo (`RESUMO_PROJETO.md`) também está incluído no zip.

## 6. Estado atual / pendências

- O app está **funcionalmente completo e testado** (ver seção de testes acima),
  mas **ainda não foi publicado** de nenhuma forma definitiva — só foi enviado
  como arquivo para Henrique testar localmente (modo "local", sem
  sincronização).
- Tentativa de subir o código para `github.com/henriqrdr/cowhand` a partir
  desta sessão (Cowork) **não foi possível**: o proxy de git desta sessão
  bloqueou o push com a mensagem "henriqrdr/cowhand is not in this session's
  authorized repository set... add the repository to the session's sources" —
  ou seja, sessões neste ambiente precisam de uma autorização por
  repositório que não está disponível nas ferramentas do Cowork. Um commit
  local já estava pronto (`git commit` bem-sucedido, só o `git push` falhou).
- Decisão do usuário: continuar a partir do **Claude Code**, que deve ter
  acesso nativo ao GitHub (via `gh auth login`, GitHub App, ou ambiente já
  vinculado ao repositório), sem essa limitação.

## 7. Próximos passos sugeridos (para fazer no Claude Code)

1. Extrair `cowhand.zip` (ou usar os arquivos deste resumo) num diretório
   local, `git init`, `git add`, `git commit`, e `git push` para
   `https://github.com/henriqrdr/cowhand.git` — isso deve funcionar direto no
   Claude Code, sem o bloqueio visto no Cowork.
2. Decidir a forma de hospedagem/uso final:
   - **Opção A — Publicar como Claude Artifact** (recomendado para ter
     sincronização automática de verdade entre Henrique e Carol, sem precisar
     manter servidor): usar a ferramenta de Artifact com
     `capabilities: {artifact: {}}`, publicando o `index.html` (ou uma versão
     dele sem as tags `<!doctype>/<html>/<head>/<body>`, já que a ferramenta
     de Artifact costuma envolver o conteúdo num "esqueleto" próprio — vale
     testar as duas formas e conferir o resultado publicado).
   - **Opção B — Self-host via Coolify**: como o `index.html` sozinho não
     sincroniza fora do Artifact, será necessário construir um backend simples
     (API + banco de dados, por exemplo Node/Express + SQLite, ou qualquer
     stack equivalente) para substituir a chamada a `claude.use('artifact')`
     por chamadas HTTP a esse backend. Isso é trabalho novo, ainda não
     iniciado.
3. Se for pela Opção B, também vale revisar se autenticação simples (só ele e
   a Carol acessam) é necessária, já que um backend próprio fica exposto
   publicamente se não for protegido.

## 8. Contexto de comunicação

Henrique se comunica em português; as decisões de produto até agora foram:
rendas 100% separadas, sem migração de dados antigos, abordagem híbrida entre
os dois modelos de planilha original, categorias agrupadas em macro-categorias,
e explicitamente "App web personalizado (link único)" como a forma do sistema
compartilhado.
