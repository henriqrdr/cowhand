# cowhand — Orçamento Familiar (Henrique & Carol)

App web de orçamento familiar compartilhado: lançamentos, despesas recorrentes/cartão,
metas e um dashboard. Frontend em uma única página HTML estática (sem build step no
navegador), com um backend simples (Node + SQLite) que guarda e sincroniza os dados
entre todos os dispositivos.

## Arquitetura

- `build_app.py` — script Python que gera `public/index.html`, `seed_data.json` e
  `taxonomy.json` a partir dos dados de taxonomia (categorias, subcategorias, opções de
  formulário) e do template HTML/CSS/JS embutido no próprio script. Rode
  `python build_app.py` depois de editar os dados ou o template. **Não edite
  `public/index.html` diretamente** — a próxima geração sobrescreve.
- `public/index.html` — o único diretório servido estaticamente por `server.js`.
  Mantê-lo separado da raiz do projeto impede que o banco de dados, `server.js` ou
  outros arquivos internos sejam servidos por engano.
- `seed_data.json` — estado inicial (renda, as 27 despesas recorrentes, as 3 metas),
  usado para semear o banco na primeira execução do servidor.
- `taxonomy.json` — os mesmos enums (categorias, formas de pagamento, etc.) usados pelo
  cliente, lidos por `server.js` para **validar** cada `PUT /api/state` e recusar
  valores fora da lista permitida.
- `server.js` — servidor Express: serve `public/`, expõe a API `/api/state` (GET/PUT),
  persiste o estado em SQLite (`node:sqlite`, nativo do Node ≥ 22.5) e aplica: HTTP
  Basic Auth, rate limiting no login, validação de schema/enum em cada escrita,
  cabeçalhos de segurança (`helmet`, CSP com hash do script inline) e bloqueio de
  requisições PUT de origem cruzada (CSRF).
- `test_app.py` — suíte de testes end-to-end (Playwright).

O app **não roda mais dentro do Artifact da Claude** (não há mais auto-publicação
"quine"). O `index.html` é 100% estático — todo o estado (lançamentos, recorrentes,
metas, renda) fica no servidor, buscado via `GET /api/state` e salvo via
`PUT /api/state` (com controle de versão otimista: se dois salvamentos colidirem, o
navegador que perder recebe a versão vencedora automaticamente). O app também faz
polling a cada 6s para pegar alterações feitas pela outra pessoa.

## Rodando localmente

```bash
npm install
COWHAND_USER=henrique COWHAND_PASS=escolha-uma-senha node server.js
```

Abra `http://localhost:3000` — o navegador vai pedir usuário/senha (HTTP Basic Auth).

## Deploy no Coolify

1. Suba este repositório para o GitHub (`git push`).
2. No Coolify, crie uma nova aplicação apontando para o repositório — ele detecta o
   `Dockerfile` (ou use o `docker-compose.yml` incluso) automaticamente.
3. Defina as variáveis de ambiente `COWHAND_USER` e `COWHAND_PASS` (veja
   `.env.example`) — **obrigatórias**, o servidor recusa iniciar sem elas.
4. Garanta que o volume `/app/data` está persistente (já configurado no
   `docker-compose.yml`) — é onde fica o banco SQLite com todos os lançamentos.
5. Exponha a porta 3000 (ou configure `PORT` e ajuste o proxy do Coolify).

Como só existem dois usuários (Henrique e Carol) compartilhando as mesmas credenciais
de Basic Auth, não há sistema de contas/permissões — é a forma mais simples possível
de manter o app privado sem expor os dados publicamente.

## Estrutura dos dados

Categorias, subcategorias e as 27 despesas recorrentes/cartão estão definidas no topo
de `build_app.py` (`CATEGORIAS`, `SUBCATEGORIAS`, `RECORRENTES`, `METAS`,
`INITIAL_STATE`). Editar esses valores só afeta o **estado inicial** (semeadura do
banco na primeira execução) — depois disso, os dados reais vivem no SQLite do servidor,
não no código.
