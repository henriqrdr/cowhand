# cowhand — Orçamento Familiar (Henrique & Carol)

App web de orçamento familiar compartilhado: lançamentos, despesas recorrentes/cartão,
metas e um dashboard. Frontend em uma única página HTML estática (sem build step no
navegador), com um backend simples (Node + SQLite) que guarda e sincroniza os dados
entre todos os dispositivos.

## Arquitetura

- `build_app.py` — script Python que gera `index.html` a partir dos dados de taxonomia
  (categorias, subcategorias, opções de formulário) e do template HTML/CSS/JS embutido
  no próprio script. Rode `python build_app.py` para regenerar `index.html` e
  `seed_data.json` depois de editar os dados ou o template. **Não edite `index.html`
  diretamente** — a próxima geração sobrescreve.
- `seed_data.json` — estado inicial (renda, as 27 despesas recorrentes, as 3 metas),
  gerado junto com `index.html`. Usado para semear o banco na primeira execução do
  servidor.
- `server.js` — servidor Express que serve `index.html` estático, expõe a API
  `/api/state` (GET/PUT) e persiste o estado em SQLite (via `node:sqlite`, nativo do
  Node ≥ 22.5, sem dependência de compilação). Protegido por HTTP Basic Auth.
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
