# cowhand — Orçamento Familiar (Henrique & Carol)

App web de orçamento familiar compartilhado: lançamentos, despesas recorrentes/cartão,
metas e um dashboard, tudo em uma única página HTML autocontida (sem build step, sem
dependências de servidor).

## Arquivos

- `build_app.py` — script Python que gera `index.html` a partir dos dados (categorias,
  despesas recorrentes, metas) e do template HTML/CSS/JS embutido no próprio script.
  Rode `python3 build_app.py` para regenerar o `index.html` depois de editar os dados
  ou o template.
- `index.html` — o app final, pronto para abrir no navegador ou hospedar em qualquer
  servidor de arquivo estático.
- `test_app.py` — suíte de testes end-to-end (Playwright) que valida o app: estado
  inicial, cálculos do dashboard, lançamentos, despesas recorrentes, metas, layout
  mobile, tema claro/escuro e o mecanismo de auto-publicação. Rode com
  `pip install playwright && playwright install chromium && python3 test_app.py`.

## ⚠️ Importante sobre sincronização entre dispositivos/pessoas

Este `index.html` foi construído para rodar dentro do visualizador de Artifacts da
Claude, que expõe uma API (`window.claude.use('artifact')`) usada pelo app para salvar
e sincronizar automaticamente os dados entre todas as pessoas com o link.

Se você hospedar este `index.html` em qualquer outro lugar (GitHub Pages, um servidor
próprio, Coolify, etc.), essa API não existe — o app continua funcionando
normalmente na tela (adicionar/editar lançamentos, ver dashboard, etc.), mas **cada
navegador fica com sua própria cópia dos dados em memória, que se perde ao recarregar
a página** e não é compartilhada entre pessoas ou dispositivos.

Para usar esse app como "sistema compartilhado de verdade" fora do ambiente Claude, é
necessário adicionar um backend próprio (uma API simples + banco de dados, por exemplo)
que substitua essa camada de sincronização. Se quiser, posso ajudar a construir esse
backend para rodar junto no Coolify.

## Estrutura dos dados

Categorias, subcategorias e as 27 despesas recorrentes/cartão estão definidas no topo
de `build_app.py` (`CATEGORIAS`, `SUBCATEGORIAS`, `RECORRENTES`, `METAS`,
`INITIAL_STATE`). Edite esses valores e rode o script de novo para atualizar o app.
