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
- `login.html` — página de login própria (formulário HTML puro, sem JS), servida em
  `/login`. Fica fora de `public/` — só é acessível através da rota `/login`.
- `assets/cowhand-logo.png` — logo oficial do app (fonte da verdade). `build_app.py`
  copia esse arquivo para `public/logo.png` a cada build; é dele que vêm as cores da
  paleta (`--accent` navy, `--cat-1` dourado, `--cat-2` laranja).
- `server.js` — servidor Express: serve `public/`, expõe a API `/api/state` (GET/PUT),
  persiste o estado em SQLite (`node:sqlite`, nativo do Node ≥ 22.5) e aplica: login com
  sessão por cookie (`HttpOnly`, `Secure` em produção, `SameSite=Strict` — ver seção
  "Autenticação"), rate limiting no login, validação de schema/enum em cada escrita,
  cabeçalhos de segurança (`helmet`, CSP com hash do script inline) e bloqueio de
  requisições PUT de origem cruzada (CSRF, defesa extra além do `SameSite`).
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

Abra `http://localhost:3000` — você será redirecionado para `/login`.

## Autenticação

Login por sessão (cookie `HttpOnly` + `SameSite=Strict`), não HTTP Basic Auth:

- `POST /api/login` valida usuário/senha contra `COWHAND_USER`/`COWHAND_PASS` e, se
  corretos, cria uma sessão (tabela `sessions` no SQLite) e devolve um cookie de sessão
  válido por 30 dias.
- Toda rota (exceto `/login` e `/api/login`) exige sessão válida — sem uma, `GET`s são
  redirecionados para `/login` e chamadas de API recebem `401`.
- `GET /logout` apaga a sessão no servidor (não só o cookie no navegador) e redireciona
  para `/login`.
- `Secure` é decidido por requisição (`req.secure`, via `trust proxy`), não por
  `NODE_ENV` fixo — o app funciona tanto acessado direto por HTTP na rede local quanto
  por HTTPS através de um proxy/túnel (ex: Cloudflare Tunnel) na frente, ao mesmo tempo, sem
  precisar de configuração diferente para cada caso. Um cookie `Secure` recebido numa
  resposta HTTP simples seria descartado silenciosamente pelo navegador (RFC 6265) —
  por isso não dá pra fixar isso em produção, precisa refletir a requisição real.
- 10 tentativas de login por minuto por IP; depois disso, `429`.

Como só existem dois usuários (Henrique e Carol) compartilhando as mesmas credenciais,
não há sistema de contas/permissões — cada um faz login pelo próprio navegador e recebe
sua própria sessão (dá pra derrubar o acesso de um dispositivo específico apagando a
linha dele na tabela `sessions`, sem afetar o outro).

## Deploy no Coolify

1. Suba este repositório para o GitHub (`git push`).
2. No Coolify, crie uma nova aplicação apontando para o repositório — ele detecta o
   `Dockerfile` (ou use o `docker-compose.yml` incluso) automaticamente.
3. Defina as variáveis de ambiente `COWHAND_USER` e `COWHAND_PASS` (veja
   `.env.example`) — **obrigatórias**, o servidor recusa iniciar sem elas.
4. Garanta que o volume `/app/data` está persistente (já configurado no
   `docker-compose.yml`) — é onde fica o banco SQLite com todos os lançamentos.
5. Exponha a porta 3000 (ou configure `PORT` e ajuste o proxy do Coolify).

## Deploy sem Coolify (docker compose direto)

Se o host não tiver como rodar o instalador do Coolify (ex: sistemas com raiz somente-
leitura, como NAS baseados em imagem imutável — foi o caso ao testar num ZimaOS), dá
pra pular o Coolify e usar o `docker-compose.yml` do repo diretamente:

```bash
git clone https://github.com/henriqrdr/cowhand.git
cd cowhand
printf 'COWHAND_USER=seu-usuario\nCOWHAND_PASS=sua-senha\n' > .env
docker compose up -d --build
```

Se a porta 3000 já estiver em uso por outro serviço no host, edite `ports:` em
`docker-compose.yml` (ex: `"3600:3000"`) antes de subir.

## Backup

O único dado que precisa de backup é o SQLite (`/app/data/cowhand.sqlite` dentro do
container, num volume Docker nomeado — o código-fonte já está versionado no GitHub).

Script de exemplo (`backup.sh`, ajuste os caminhos pro seu host):

```bash
#!/bin/bash
set -euo pipefail
SRC_DB="$(docker volume inspect cowhand_cowhand_data --format '{{.Mountpoint}}')/cowhand.sqlite"
BACKUP_DIR="./backups"
DATE="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BACKUP_DIR"
sqlite3 "$SRC_DB" ".backup '$BACKUP_DIR/cowhand-$DATE.sqlite'"
gzip "$BACKUP_DIR/cowhand-$DATE.sqlite"
find "$BACKUP_DIR" -name 'cowhand-*.sqlite.gz' -mtime +30 -delete
```

Usa `sqlite3 .backup` (não `cp` do arquivo bruto) — é seguro rodar com o app no ar,
mesmo em modo WAL, porque faz uma cópia consistente via a própria engine do SQLite, sem
risco de pegar um arquivo pela metade de uma escrita. Agende via `crontab -e`:

```
30 3 * * * /bin/bash /caminho/para/backup.sh >> /caminho/para/backups/backup.log 2>&1
```

Vale manter uma cópia fora do próprio host (outro disco, nuvem, etc.) — um backup que
mora só na mesma máquina que ele protege não sobrevive a uma falha de disco.

**Restaurar:** pare o container, substitua o arquivo do volume pelo backup
descompactado, suba de novo:

```bash
docker compose stop cowhand
gunzip -k cowhand-AAAAMMDD-HHMMSS.sqlite.gz
cp cowhand-AAAAMMDD-HHMMSS.sqlite "$(docker volume inspect cowhand_cowhand_data --format '{{.Mountpoint}}')/cowhand.sqlite"
docker compose start cowhand
```

## Parcelas automáticas

Um lançamento novo com Tipo = "Recorrente Parcelado" e Parcela no formato `N/M` (ex:
`3/12`) gera automaticamente as parcelas `N+1/M` até `M/M` nos meses seguintes (mesma
descrição/categoria/valor, data avançando um mês por vez), com status "Agendado" —
só a parcela digitada mantém o status escolhido no formulário. Isso só acontece ao
**criar** o lançamento, não ao editar um já existente (evita duplicar a série). Cada
parcela gerada é um lançamento independente — editar ou excluir uma não afeta as outras.

## Estrutura dos dados

Categorias, subcategorias e as 27 despesas recorrentes/cartão estão definidas no topo
de `build_app.py` (`CATEGORIAS`, `SUBCATEGORIAS`, `RECORRENTES`, `METAS`,
`INITIAL_STATE`). Editar esses valores só afeta o **estado inicial** (semeadura do
banco na primeira execução) — depois disso, os dados reais vivem no SQLite do servidor,
não no código.
