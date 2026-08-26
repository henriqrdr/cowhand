# -*- coding: utf-8 -*-
import json, os, sys

# =====================================================================================
# INITIAL DATA (seeded from the couple's real spreadsheet + card statement)
# =====================================================================================

CATEGORIAS = [
    "Moradia", "Educação", "Veículos", "Alimentação", "Pet", "Saúde",
    "Cuidados Pessoais & Estética", "Vestuário & Calçados", "Assinaturas",
    "Lazer & Recreação", "Presentes", "Dívidas & Empréstimos", "Investimentos", "Outros",
]

SUBCATEGORIAS = [
    "Condomínio", "Aluguel/Financiamento Imóvel", "Água", "Gás", "Luz", "Internet/TV",
    "Limpeza/Manutenção Casa", "Mensalidade Escolar", "Material Escolar", "Cursos",
    "Financiamento Veículo", "Combustível", "Manutenção Veículo", "Seguro Veículo",
    "Estacionamento/Pedágio", "Supermercado", "Restaurante/Delivery", "Padaria",
    "Ração/Petshop", "Veterinário/Remédio Pet", "Farmácia", "Plano de Saúde",
    "Consultas Médicas", "Psicólogo/Terapia", "Cabelo", "Estética", "Cosméticos",
    "Academia/Treino", "Roupas", "Sapatos/Tênis", "Streaming", "Nuvem/Software",
    "App/Ferramenta de Trabalho", "Clube", "Viagem", "Lazer Diversos", "Presentes",
    "Empréstimo", "Cartão Parcelado Outros", "Aporte Investimento", "Fundo de Férias",
    "Fundo Carro", "Diversos",
]

RESPONSAVEL_OPTS = ["Ele", "Ela", "Ambos"]
TIPO_OPTS = ["Fixo", "Variável", "Recorrente Parcelado", "Investimento"]
FORMA_PGTO_OPTS = [
    "Cartão C6 (Henrique)", "Cartão Santander (Carol)", "Cartão Renner (Carol)",
    "Pix", "Débito Automático", "Boleto", "Dinheiro",
]
STATUS_OPTS = ["Pago", "Pendente", "Agendado"]

# id, categoria, subcategoria, item, responsavel, forma, tipo, valorEsperado, parcela, obs, chave
RECORRENTES = [
    dict(id="r1", categoria="Moradia", subcategoria="Condomínio", item="Condomínio Apto 102",
         responsavel="Ambos", forma="Débito Automático", tipo="Fixo", valorEsperado=600.00, parcela="",
         obs="Média recente (Ago/2026: R$ 596,15).", chave=""),
    dict(id="r2", categoria="Moradia", subcategoria="Gás", item="Gás encanado",
         responsavel="Ambos", forma="Boleto", tipo="Fixo", valorEsperado=444.00, parcela="",
         obs="Valor de Ago/2026.", chave=""),
    dict(id="r3", categoria="Moradia", subcategoria="Luz", item="RGE - Energia Elétrica Apto 102",
         responsavel="Ambos", forma="Débito Automático", tipo="Variável", valorEsperado=450.00, parcela="",
         obs="Varia bastante: Jul/2026 R$ 402,14, Ago/2026 R$ 669,95.", chave=""),
    dict(id="r4", categoria="Moradia", subcategoria="Internet/TV", item="Net Apto 102",
         responsavel="Ambos", forma="Débito Automático", tipo="Fixo", valorEsperado=147.00, parcela="",
         obs="Valor estável nos últimos meses.", chave=""),
    dict(id="r5", categoria="Moradia", subcategoria="Limpeza/Manutenção Casa", item="Diarista mensal",
         responsavel="Ambos", forma="Pix", tipo="Fixo", valorEsperado=720.00, parcela="",
         obs="Valor de Ago/2026.", chave=""),
    dict(id="r6", categoria="Educação", subcategoria="Mensalidade Escolar", item="Murialdo - Augusto",
         responsavel="Ambos", forma="Boleto", tipo="Fixo", valorEsperado=1295.00, parcela="",
         obs="Havia duplicidade nas duas planilhas antigas - contar 1x.", chave=""),
    dict(id="r7", categoria="Educação", subcategoria="Material Escolar",
         item="Centro Técnico Social (material Augusto)", responsavel="Ele", forma="Cartão C6 (Henrique)",
         tipo="Recorrente Parcelado", valorEsperado=375.00, parcela="6/8",
         obs="Termina em 2 parcelas (~out/2026) - remover depois.", chave=""),
    dict(id="r8", categoria="Veículos", subcategoria="Financiamento Veículo", item="Parcela Compass",
         responsavel="Ele", forma="Cartão C6 (Henrique)", tipo="Recorrente Parcelado", valorEsperado=2560.90,
         parcela="15/48", obs="Financiamento do carro do Henrique, termina em 48/48 (~2029).", chave=""),
    dict(id="r9", categoria="Veículos", subcategoria="Combustível", item="Posto Longhi e outros postos",
         responsavel="Ele", forma="Cartão C6 (Henrique)", tipo="Variável", valorEsperado=1071.22, parcela="",
         obs="Baseado na fatura C6 de 05/08/2026.", chave=""),
    dict(id="r10", categoria="Alimentação", subcategoria="Supermercado",
         item="Zaffari / Sacolão Minuano / Super Crisan / Savi", responsavel="Ambos",
         forma="Cartão C6 (Henrique)", tipo="Variável", valorEsperado=1617.98, parcela="",
         obs="Baseado na fatura C6 de 05/08/2026.", chave=""),
    dict(id="r11", categoria="Alimentação", subcategoria="Restaurante/Delivery", item="Diversos restaurantes",
         responsavel="Ambos", forma="Cartão C6 (Henrique)", tipo="Variável", valorEsperado=926.35, parcela="",
         obs="Baseado na fatura C6 de 05/08/2026.", chave=""),
    dict(id="r12", categoria="Pet", subcategoria="Ração/Petshop", item="Petz Digital + Central de Rações",
         responsavel="Ambos", forma="Cartão C6 (Henrique)", tipo="Variável", valorEsperado=224.29, parcela="",
         obs="Petz Digital R$ 178,39 + Central de Rações R$ 45,90.", chave=""),
    dict(id="r13", categoria="Pet", subcategoria="Veterinário/Remédio Pet", item="Fórmula Bichos Manipulados",
         responsavel="Ambos", forma="Cartão C6 (Henrique)", tipo="Recorrente Parcelado", valorEsperado=204.00,
         parcela="3/3", obs="Última parcela - sai da lista no mês seguinte.", chave=""),
    dict(id="r14", categoria="Assinaturas", subcategoria="Streaming", item="Netflix (Plano Básico)",
         responsavel="Ambos", forma="Cartão C6 (Henrique)", tipo="Fixo", valorEsperado=20.90, parcela="",
         obs="Informado por Henrique em 23/08/2026.", chave="Netflix"),
    dict(id="r15", categoria="Assinaturas", subcategoria="Streaming", item="Crunchyroll",
         responsavel="Ambos", forma="Cartão C6 (Henrique)", tipo="Fixo", valorEsperado=3.90, parcela="",
         obs="Fatura C6 de 05/08/2026.", chave="Crunchyroll"),
    dict(id="r16", categoria="Assinaturas", subcategoria="Nuvem/Software", item="iCloud/Apple",
         responsavel="Ambos", forma="Cartão C6 (Henrique)", tipo="Fixo", valorEsperado=66.90, parcela="",
         obs="Confirmar se não é a mesma assinatura já contada na planilha antiga da Carol.", chave=""),
    dict(id="r17", categoria="Assinaturas", subcategoria="App/Ferramenta de Trabalho", item="Torbox",
         responsavel="Ele", forma="Cartão C6 (Henrique)", tipo="Fixo", valorEsperado=16.65, parcela="",
         obs="Fatura C6 de 05/08/2026.", chave="Torbox"),
    dict(id="r18", categoria="Assinaturas", subcategoria="App/Ferramenta de Trabalho", item="Claude Code",
         responsavel="Ele", forma="Cartão C6 (Henrique)", tipo="Fixo", valorEsperado=110.00, parcela="",
         obs="Ferramenta de trabalho.", chave="Claude"),
    dict(id="r19", categoria="Cuidados Pessoais & Estética", subcategoria="Estética", item="Tina Biasus",
         responsavel="Ela", forma="Cartão Santander (Carol)", tipo="Fixo", valorEsperado=90.00, parcela="",
         obs="", chave="Tina"),
    dict(id="r20", categoria="Cuidados Pessoais & Estética", subcategoria="Estética", item="Camila Maciel",
         responsavel="Ela", forma="Cartão Santander (Carol)", tipo="Fixo", valorEsperado=80.00, parcela="",
         obs="", chave="Camila Maciel"),
    dict(id="r21", categoria="Cuidados Pessoais & Estética", subcategoria="Estética", item="Manu Trombetta",
         responsavel="Ela", forma="Cartão Santander (Carol)", tipo="Fixo", valorEsperado=55.00, parcela="",
         obs="", chave="Manu"),
    dict(id="r22", categoria="Saúde", subcategoria="Psicólogo/Terapia", item="Carla Porto",
         responsavel="Ela", forma="Cartão Santander (Carol)", tipo="Fixo", valorEsperado=340.00, parcela="",
         obs="", chave=""),
    dict(id="r23", categoria="Lazer & Recreação", subcategoria="Clube", item="Clube Recreio da Juventude",
         responsavel="Ambos", forma="Débito Automático", tipo="Fixo", valorEsperado=500.00, parcela="",
         obs="", chave=""),
    dict(id="r24", categoria="Lazer & Recreação", subcategoria="Lazer Diversos", item="Cancha",
         responsavel="Ambos", forma="Pix", tipo="Variável", valorEsperado=70.00, parcela="",
         obs="", chave="Cancha"),
    dict(id="r25", categoria="Lazer & Recreação", subcategoria="Lazer Diversos", item="HV",
         responsavel="Ambos", forma="Boleto", tipo="Fixo", valorEsperado=215.00, parcela="",
         obs="", chave="HV"),
    dict(id="r26", categoria="Investimentos", subcategoria="Aporte Investimento",
         item="Conta Augusto (poupança do filho)", responsavel="Ele", forma="Pix", tipo="Investimento",
         valorEsperado=100.00, parcela="", obs="", chave=""),
    dict(id="r27", categoria="Dívidas & Empréstimos", subcategoria="Empréstimo",
         item="Empréstimo Nubank (Carol)", responsavel="Ela", forma="Débito Automático",
         tipo="Recorrente Parcelado", valorEsperado=55.48, parcela="",
         obs="Confirmar quantas parcelas restam.", chave=""),
]

METAS = [
    dict(id="m1", nome="Aportes para Investimentos", subcategoria="Aporte Investimento",
         valorAtual=0, valorAlvo=0, prazo="", contribPlanejada=0),
    dict(id="m2", nome="Fundo de Férias", subcategoria="Fundo de Férias",
         valorAtual=0, valorAlvo=0, prazo="", contribPlanejada=0),
    dict(id="m3", nome="Aquisição de Carro (Carol)", subcategoria="Fundo Carro",
         valorAtual=0, valorAlvo=0, prazo="", contribPlanejada=0),
]

INITIAL_STATE = dict(
    renda=dict(henrique=11000, carol=0),
    transacoes=[],
    recorrentes=RECORRENTES,
    metas=METAS,
    updatedAt="2026-08-26",
)

# =====================================================================================
# CSS
# =====================================================================================
CSS = r'''
:root {
  color-scheme: light;
  --bg: #f7f6f2;
  --surface: #ffffff;
  --surface-2: #f1efe9;
  --text: #14181a;
  --text-2: #52514e;
  --text-muted: #898781;
  --line: #e1e0d9;
  --accent: #146356;
  --accent-strong: #0e4a40;
  --accent-soft: #dceeea;
  --accent-ink: #ffffff;
  --good: #0ca30c;
  --critical: #c8373a;
  --warning: #a8710a;
  --cat-1: #2a78d6;
  --cat-2: #c65a26;
  --cat-3: #1a9c6c;
  --shadow: 0 1px 2px rgba(20,24,26,0.06), 0 4px 16px rgba(20,24,26,0.05);
  --radius: 10px;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --bg: #0d0d0d;
    --surface: #1a1a19;
    --surface-2: #212320;
    --text: #f5f4f0;
    --text-2: #c3c2b7;
    --text-muted: #8f8d86;
    --line: #2c2c2a;
    --accent: #4fbfa8;
    --accent-strong: #7fd9c4;
    --accent-soft: #16302b;
    --accent-ink: #06201b;
    --good: #2fbf3f;
    --critical: #e6716f;
    --warning: #d9a441;
    --cat-1: #3987e5;
    --cat-2: #d97b45;
    --cat-3: #33b688;
    --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 4px 20px rgba(0,0,0,0.35);
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #0d0d0d;
  --surface: #1a1a19;
  --surface-2: #212320;
  --text: #f5f4f0;
  --text-2: #c3c2b7;
  --text-muted: #8f8d86;
  --line: #2c2c2a;
  --accent: #4fbfa8;
  --accent-strong: #7fd9c4;
  --accent-soft: #16302b;
  --accent-ink: #06201b;
  --good: #2fbf3f;
  --critical: #e6716f;
  --warning: #d9a441;
  --cat-1: #3987e5;
  --cat-2: #d97b45;
  --cat-3: #33b688;
  --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 4px 20px rgba(0,0,0,0.35);
}

* { box-sizing: border-box; }
html, body { height: 100%; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: "Public Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 14.5px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}
h1, h2, h3, .brand, .tabbar a, .navlink { font-family: "Sora", "Public Sans", sans-serif; }
.mono, .money, input[type="number"], .figure { font-family: "IBM Plex Mono", ui-monospace, monospace; font-variant-numeric: tabular-nums; }
h1, h2, h3 { text-wrap: balance; margin: 0 0 4px; color: var(--text); }
a { color: inherit; }
button, input, select, textarea { font: inherit; color: inherit; }
::selection { background: var(--accent-soft); }

#shell { display: flex; min-height: 100vh; }

/* Sidebar (desktop) */
#sidebar {
  width: 240px;
  flex: none;
  background: var(--surface);
  border-right: 1px solid var(--line);
  padding: 22px 16px;
  display: flex;
  flex-direction: column;
  gap: 22px;
  position: sticky;
  top: 0;
  height: 100vh;
}
.brand { font-weight: 800; font-size: 18px; letter-spacing: -0.01em; display: flex; align-items: center; gap: 10px; }
.brand-mark {
  width: 34px; height: 34px; border-radius: 9px;
  background: linear-gradient(155deg, var(--accent), var(--accent-strong));
  display: flex; align-items: center; justify-content: center;
  color: var(--accent-ink); font-weight: 800; font-size: 15px; flex: none;
}
.navlist { display: flex; flex-direction: column; gap: 2px; }
.navlink {
  display: flex; align-items: center; gap: 11px;
  padding: 9px 11px; border-radius: 8px;
  color: var(--text-2); font-weight: 600; font-size: 13.5px;
  text-decoration: none; cursor: pointer; border: none; background: none; text-align: left; width: 100%;
}
.navlink svg { flex: none; opacity: 0.8; }
.navlink:hover { background: var(--surface-2); color: var(--text); }
.navlink.active { background: var(--accent-soft); color: var(--accent-strong); }
.navlink.active svg { opacity: 1; }
.sidebar-foot { margin-top: auto; font-size: 12px; color: var(--text-muted); padding: 0 11px; }

/* Main */
#main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
#topbar {
  position: sticky; top: 0; z-index: 5;
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--line);
  padding: 14px 28px;
  display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
}
#topbar .spacer { flex: 1; }
.month-field { display: flex; align-items: center; gap: 8px; }
.month-field label { font-size: 12px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
input[type="month"], input[type="date"], input[type="text"], input[type="number"], select, textarea {
  background: var(--surface); border: 1px solid var(--line); border-radius: 8px;
  padding: 8px 10px; font-size: 13.5px; color: var(--text);
}
input[type="month"] { font-family: "IBM Plex Mono", monospace; }
input:focus-visible, select:focus-visible, textarea:focus-visible, button:focus-visible, a:focus-visible {
  outline: 2px solid var(--accent); outline-offset: 1px;
}
#appwrap { padding: 22px 28px 90px; max-width: 1160px; width: 100%; margin: 0 auto; }

.btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 15px; border-radius: 8px; border: 1px solid var(--line);
  background: var(--surface); font-weight: 600; font-size: 13.5px; cursor: pointer;
  white-space: nowrap;
}
.btn:hover { border-color: var(--text-muted); }
.btn-primary { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); }
.btn-primary:hover { background: var(--accent-strong); border-color: var(--accent-strong); }
.btn-ghost { border-color: transparent; background: none; }
.btn-ghost:hover { background: var(--surface-2); }
.btn-danger { color: var(--critical); }
.btn-sm { padding: 5px 10px; font-size: 12.5px; border-radius: 7px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.card {
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius);
  padding: 18px; box-shadow: var(--shadow);
}
.section-title { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin: 0 0 12px; }

.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
.kpi { min-width: 0; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 16px 18px; box-shadow: var(--shadow); }
.kpi .label { font-size: 12px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
.kpi .value { font-family: "IBM Plex Mono", monospace; font-size: 22px; font-weight: 600; margin-top: 6px; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.kpi .value.good { color: var(--good); }
.kpi .value.critical { color: var(--critical); }
.kpi .sub { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

.grid-2 { display: grid; grid-template-columns: 1.3fr 1fr; gap: 16px; align-items: start; min-width: 0; }
.grid-2 > * { min-width: 0; }
.filtro-grid { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 12px; }

.barlist { display: flex; flex-direction: column; gap: 10px; }
.barlist .row { display: grid; grid-template-columns: 150px 1fr 84px; align-items: center; gap: 10px; }
.barlist .row .lbl { font-size: 13px; color: var(--text-2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.barlist .track { height: 8px; background: var(--surface-2); border-radius: 5px; overflow: hidden; }
.barlist .fill { height: 100%; border-radius: 5px; background: var(--accent); }
.barlist .val { font-family: "IBM Plex Mono", monospace; font-size: 12.5px; text-align: right; color: var(--text-2); font-variant-numeric: tabular-nums; }

.seg { display: flex; height: 10px; border-radius: 6px; overflow: hidden; background: var(--surface-2); }
.seg > span { height: 100%; }
.legend { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 10px; }
.legend .item { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--text-2); }
.legend .dot { width: 9px; height: 9px; border-radius: 3px; flex: none; }

.progress { height: 9px; background: var(--surface-2); border-radius: 6px; overflow: hidden; }
.progress > span { display: block; height: 100%; background: var(--accent); border-radius: 6px; }

table { border-collapse: collapse; width: 100%; font-size: 13px; }
th { text-align: left; font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted); font-weight: 700; padding: 8px 10px; border-bottom: 1px solid var(--line); white-space: nowrap; }
td { padding: 9px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
tr:last-child td { border-bottom: none; }
.table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface); box-shadow: var(--shadow); }
.table-wrap table { min-width: 720px; }
.num { font-family: "IBM Plex Mono", monospace; text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.critical-text { color: var(--critical); }
.good-text { color: var(--good); }

.badge { display: inline-flex; align-items: center; gap: 5px; padding: 2px 9px; border-radius: 999px; font-size: 11.5px; font-weight: 700; }
.badge-ele { background: color-mix(in srgb, var(--cat-1) 16%, transparent); color: var(--cat-1); }
.badge-ela { background: color-mix(in srgb, var(--cat-2) 16%, transparent); color: var(--cat-2); }
.badge-ambos { background: color-mix(in srgb, var(--cat-3) 16%, transparent); color: var(--cat-3); }
.badge-pago { background: color-mix(in srgb, var(--good) 16%, transparent); color: var(--good); }
.badge-pendente { background: color-mix(in srgb, var(--warning) 18%, transparent); color: var(--warning); }
.badge-agendado { background: var(--surface-2); color: var(--text-muted); }

.empty { text-align: center; padding: 40px 20px; color: var(--text-muted); }
.empty .big { font-size: 28px; margin-bottom: 6px; }

.field { display: flex; flex-direction: column; gap: 5px; }
.field label { font-size: 12px; font-weight: 600; color: var(--text-2); }
.field-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.formcard { display: flex; flex-direction: column; gap: 12px; }
.formcard .actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 4px; }
textarea { resize: vertical; min-height: 40px; }

.modal-backdrop {
  position: fixed; inset: 0; background: rgba(10,12,12,0.45); backdrop-filter: blur(2px);
  display: flex; align-items: flex-start; justify-content: center; padding: 6vh 16px; z-index: 50; overflow-y: auto;
}
.modal { background: var(--surface); border-radius: 14px; border: 1px solid var(--line); box-shadow: var(--shadow); width: 100%; max-width: 560px; padding: 22px; }
.modal-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.modal-head h3 { font-size: 16px; }

.toast-wrap { position: fixed; bottom: 90px; left: 50%; transform: translateX(-50%); z-index: 60; display: flex; flex-direction: column; gap: 8px; align-items: center; }
.toast { background: var(--text); color: var(--bg); padding: 9px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; box-shadow: var(--shadow); }
.toast.err { background: var(--critical); color: #fff; }

.readonly-banner { background: var(--surface-2); border: 1px solid var(--line); border-radius: 8px; padding: 10px 14px; font-size: 12.5px; color: var(--text-2); margin-bottom: 16px; display: flex; gap: 8px; align-items: center; }

/* Mobile bottom tab bar */
#mobiletabs { display: none; }

@media (max-width: 860px) {
  #sidebar { display: none; }
  #appwrap { padding: 16px 14px 90px; }
  #topbar { padding: 12px 14px; }
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .kpi .value { font-size: 18px; }
  .grid-2 { grid-template-columns: 1fr; }
  .field-row { grid-template-columns: 1fr; }
  .filtro-grid { grid-template-columns: 1fr; }
  #mobiletabs {
    display: flex; position: fixed; bottom: 0; left: 0; right: 0; z-index: 10;
    background: var(--surface); border-top: 1px solid var(--line);
    padding: 6px 4px calc(6px + env(safe-area-inset-bottom));
  }
  #mobiletabs button {
    flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; gap: 3px;
    background: none; border: none; padding: 6px 2px; color: var(--text-muted); font-size: 10.5px; font-weight: 600;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  #mobiletabs button.active { color: var(--accent-strong); }
  .table-wrap table { min-width: 640px; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
'''

print("Data section OK:",
      len(CATEGORIAS), "categorias,",
      len(SUBCATEGORIAS), "subcategorias,",
      len(RECORRENTES), "recorrentes,",
      len(METAS), "metas")

# =====================================================================================
# APP JS
# =====================================================================================
APP_JS = r'''
(function(){
"use strict";

/* ---------- server sync plumbing ---------- */
var API_STATE_URL = 'api/state';
var STATE = null;
var STATE_VERSION = 0;
window.__STATE__ = null;

/* ---------- small utils ---------- */
function deepClone(o){ return JSON.parse(JSON.stringify(o)); }
function uid(prefix){ return prefix + '_' + Math.random().toString(36).slice(2, 10); }
function escapeHtml(s){
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function fmtMoney(n){
  n = Number(n) || 0;
  try { return n.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'}); }
  catch(e){ return 'R$ ' + n.toFixed(2); }
}
function fmtDate(d){
  if (!d) return '-';
  var p = d.split('-');
  if (p.length !== 3) return d;
  return p[2] + '/' + p[1] + '/' + p[0];
}
function currentMonthStr(){
  var d = new Date();
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
}
function monthLabel(m){
  var MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];
  var p = (m || '').split('-');
  if (p.length !== 2) return m;
  var idx = parseInt(p[1], 10) - 1;
  return (MESES[idx] || p[1]) + ' de ' + p[0];
}
function lsGet(k, d){ try { var v = localStorage.getItem(k); return v == null ? d : v; } catch(e){ return d; } }
function lsSet(k, v){ try { localStorage.setItem(k, v); } catch(e){} }
function clamp(n, a, b){ return Math.max(a, Math.min(b, n)); }

/* ---------- static taxonomy (baked in at build time, never republished as state) ---------- */
var CATEGORIAS = __CATEGORIAS_JSON__;
var SUBCATEGORIAS = __SUBCATEGORIAS_JSON__;
var RESPONSAVEL_OPTS = __RESPONSAVEL_OPTS_JSON__;
var TIPO_OPTS = __TIPO_OPTS_JSON__;
var FORMA_PGTO_OPTS = __FORMA_PGTO_OPTS_JSON__;
var STATUS_OPTS = __STATUS_OPTS_JSON__;

var TABS = [
  {id:'dashboard', label:'Dashboard', short:'Dashboard'},
  {id:'lancamentos', label:'Lançamentos', short:'Lançam.'},
  {id:'recorrentes', label:'Recorrentes & Cartão', short:'Cartão'},
  {id:'metas', label:'Metas', short:'Metas'},
  {id:'ajustes', label:'Ajustes', short:'Ajustes'}
];

/* ---------- view/local state (never published) ---------- */
var MONTH = lsGet('ofc_month', currentMonthStr());
var ACTIVE_TAB = lsGet('ofc_tab', 'dashboard');
var THEME = lsGet('ofc_theme', 'system');
var READONLY = false;
var dirty = false;
var publishing = false;
var publishTimer = null;
var syncBadgeState = 'idle';
var editingTxId = null;
var lancFiltro = {texto: '', categoria: '', responsavel: ''};

function applyTheme(t){
  if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
  else document.documentElement.removeAttribute('data-theme');
}
applyTheme(THEME);

/* ---------- data helpers ---------- */
function txForMonth(month){
  return STATE.transacoes.filter(function(t){ return (t.data || '').slice(0,7) === month; });
}
function valorRealRecorrente(rec, txs){
  var filtered = txs.filter(function(t){ return t.categoria === rec.categoria && t.subcategoria === rec.subcategoria; });
  if (rec.chave) {
    var k = rec.chave.toLowerCase();
    filtered = filtered.filter(function(t){ return (t.descricao || '').toLowerCase().indexOf(k) !== -1; });
  }
  return filtered.reduce(function(s,t){ return s + (Number(t.valor) || 0); }, 0);
}
function contribMeta(meta, txs){
  return txs.filter(function(t){ return t.subcategoria === meta.subcategoria && t.tipo === 'Investimento'; })
            .reduce(function(s,t){ return s + (Number(t.valor) || 0); }, 0);
}
function mesesRestantes(prazo){
  if (!prazo) return null;
  var now = new Date();
  var alvo = new Date(prazo + 'T00:00:00');
  var months = (alvo.getFullYear() - now.getFullYear()) * 12 + (alvo.getMonth() - now.getMonth());
  return months;
}
function dashboardData(){
  var txs = txForMonth(MONTH);
  var rendaConjunta = (Number(STATE.renda.henrique) || 0) + (Number(STATE.renda.carol) || 0);
  var investTxs = txs.filter(function(t){ return t.tipo === 'Investimento'; });
  var aportes = investTxs.reduce(function(s,t){ return s + (Number(t.valor) || 0); }, 0);
  var totalTxs = txs.reduce(function(s,t){ return s + (Number(t.valor) || 0); }, 0);
  var gastoTotal = totalTxs - aportes;
  var saldo = rendaConjunta - gastoTotal - aportes;
  var taxa = rendaConjunta > 0 ? (aportes / rendaConjunta) : 0;

  var spendTxs = txs.filter(function(t){ return t.tipo !== 'Investimento'; });
  var byCat = {};
  spendTxs.forEach(function(t){ byCat[t.categoria] = (byCat[t.categoria] || 0) + (Number(t.valor) || 0); });
  var catList = Object.keys(byCat).map(function(k){ return {label:k, value:byCat[k]}; }).sort(function(a,b){ return b.value - a.value; });

  var byResp = {Ele:0, Ela:0, Ambos:0};
  txs.forEach(function(t){ if (byResp.hasOwnProperty(t.responsavel)) byResp[t.responsavel] += (Number(t.valor) || 0); });

  var grp = {'Previsível':0, 'Variável':0, 'Investimento':0};
  txs.forEach(function(t){
    var v = Number(t.valor) || 0;
    if (t.tipo === 'Fixo' || t.tipo === 'Recorrente Parcelado') grp['Previsível'] += v;
    else if (t.tipo === 'Variável') grp['Variável'] += v;
    else if (t.tipo === 'Investimento') grp['Investimento'] += v;
  });

  return {rendaConjunta:rendaConjunta, gastoTotal:gastoTotal, aportes:aportes, saldo:saldo, taxa:taxa, catList:catList, byResp:byResp, grp:grp, txs:txs};
}

/* ---------- mutation + publish pipeline ---------- */
function mutate(mutator){
  if (READONLY) { showToast('Este link está em modo somente leitura.', true); return; }
  var next = deepClone(STATE);
  mutator(next);
  next.updatedAt = new Date().toISOString();
  STATE = next;
  window.__STATE__ = STATE;
  dirty = true;
  renderApp();
  queuePublish();
}
function queuePublish(){
  if (publishTimer) clearTimeout(publishTimer);
  publishTimer = setTimeout(flushPublish, 700);
}
function setSyncBadge(s){ syncBadgeState = s; renderSyncBadge(); }
function flushPublish(){
  if (!dirty || publishing) return;
  publishing = true;
  setSyncBadge('saving');
  fetch(API_STATE_URL, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({state: STATE, version: STATE_VERSION})
  }).then(function(r){
    if (r.status === 401 || r.status === 403) { var e = new Error('auth'); e.code = 'auth'; throw e; }
    if (r.status === 409) { var e2 = new Error('conflict'); e2.code = 'conflict'; e2.body = r.json(); throw e2; }
    if (!r.ok) { var e3 = new Error('upstream'); e3.code = 'upstream_error'; throw e3; }
    return r.json();
  }).then(function(d){
    STATE_VERSION = d.version;
    dirty = false;
    publishing = false;
    setSyncBadge('saved');
  }).catch(function(e){
    publishing = false;
    var code = e && e.code;
    if (code === 'conflict') {
      Promise.resolve(e.body).then(function(d){
        STATE = d.state; STATE_VERSION = d.version; window.__STATE__ = STATE;
        dirty = false;
        showToast('Carol/Henrique salvou uma alteração ao mesmo tempo — a tela foi atualizada com a versão mais recente.', true);
        setSyncBadge('saved');
        renderApp();
      });
    } else if (code === 'auth') {
      READONLY = true;
      setSyncBadge('readonly');
      showToast('Sessão não autenticada — recarregue a página e faça login novamente.', true);
      renderApp();
    } else {
      setSyncBadge('pending');
      showToast('Não foi possível salvar agora. Toque em "tentar novamente".', true);
    }
  });
}
function pollState(){
  if (dirty || publishing) return;
  fetch(API_STATE_URL).then(function(r){ return r.ok ? r.json() : null; }).then(function(d){
    if (!d || d.version === STATE_VERSION) return;
    STATE = d.state; STATE_VERSION = d.version; window.__STATE__ = STATE;
    setSyncBadge('saved');
    renderApp();
  }).catch(function(){ /* ignore transient poll failures */ });
}

/* ---------- toasts ---------- */
function showToast(msg, isErr){
  var wrap = document.getElementById('toast-wrap');
  if (!wrap) return;
  var el = document.createElement('div');
  el.className = 'toast' + (isErr ? ' err' : '');
  el.textContent = msg;
  wrap.appendChild(el);
  setTimeout(function(){ el.remove(); }, 3200);
}

/* ---------- modal ---------- */
function openModal(titleHtml, bodyHtml){
  var root = document.getElementById('modal-root');
  root.innerHTML =
    '<div class="modal-backdrop" data-act="modal-backdrop">' +
      '<div class="modal" role="dialog" aria-modal="true">' +
        '<div class="modal-head"><h3>' + titleHtml + '</h3>' +
          '<button class="btn btn-ghost btn-sm" data-act="modal-close" type="button">Fechar</button></div>' +
        bodyHtml +
      '</div>' +
    '</div>';
}
function closeModal(){ document.getElementById('modal-root').innerHTML = ''; editingTxId = null; }

function openConfirm(message, onConfirm){
  openModal('Confirmar', '<p style="color:var(--text-2);margin:0 0 16px">' + escapeHtml(message) + '</p>' +
    '<div class="actions" style="display:flex;gap:10px;justify-content:flex-end">' +
      '<button class="btn" data-act="modal-close" type="button">Cancelar</button>' +
      '<button class="btn btn-primary" style="background:var(--critical);border-color:var(--critical)" id="confirm-yes" type="button">Excluir</button>' +
    '</div>');
  document.getElementById('confirm-yes').addEventListener('click', function(){ closeModal(); onConfirm(); });
}

/* ---------- form field builders ---------- */
function selectHtml(name, opts, current, extra){
  return '<select name="' + name + '" ' + (extra || '') + '>' +
    '<option value="">Selecione...</option>' +
    opts.map(function(o){ return '<option value="' + escapeHtml(o) + '"' + (o === current ? ' selected' : '') + '>' + escapeHtml(o) + '</option>'; }).join('') +
    '</select>';
}

/* ================= RENDER: SHELL ================= */
function renderShell(){
  var navHtml = TABS.map(function(t){
    return '<button class="navlink' + (t.id === ACTIVE_TAB ? ' active' : '') + '" data-act="nav" data-tab="' + t.id + '" type="button">' + t.label + '</button>';
  }).join('');
  document.getElementById('navlist-desktop').innerHTML = navHtml;
  document.getElementById('mobiletabs').innerHTML = TABS.map(function(t){
    return '<button class="' + (t.id === ACTIVE_TAB ? 'active' : '') + '" data-act="nav" data-tab="' + t.id + '" type="button">' + t.short + '</button>';
  }).join('');
  document.getElementById('sidebar-foot').innerHTML = 'Henrique &amp; Carol<br>Orçamento familiar compartilhado';
  var mi = document.getElementById('month-input');
  if (mi.value !== MONTH) mi.value = MONTH;
  renderSyncBadge();
}
function renderSyncBadge(){
  var el = document.getElementById('topbar-actions');
  if (!el) return;
  var map = {
    idle: {label:'Carregando...', cls:''},
    saved: {label:'Salvo', cls:'good-text'},
    saving: {label:'Salvando...', cls:''},
    pending: {label:'Alterações pendentes', cls:'critical-text'},
    readonly: {label:'Não foi possível autenticar', cls:'critical-text'}
  };
  var s = map[syncBadgeState] || map.idle;
  var retryBtn = (syncBadgeState === 'pending') ? '<button class="btn btn-sm" data-act="retry-publish" type="button">Tentar novamente</button>' : '';
  el.innerHTML = '<span class="mono ' + s.cls + '" style="font-size:12px">' + s.label + '</span>' + retryBtn;
}

/* ================= RENDER: DASHBOARD ================= */
function renderDashboard(){
  var d = dashboardData();
  var maxCat = d.catList.length ? d.catList[0].value : 0;
  var catRows = d.catList.length ? d.catList.map(function(c){
    var pct = maxCat > 0 ? clamp((c.value / maxCat) * 100, 2, 100) : 0;
    return '<div class="row"><div class="lbl">' + escapeHtml(c.label) + '</div>' +
      '<div class="track"><div class="fill" style="width:' + pct + '%"></div></div>' +
      '<div class="val">' + fmtMoney(c.value) + '</div></div>';
  }).join('') : '<div class="empty">Sem lançamentos neste mês ainda.</div>';

  var respTotal = d.byResp.Ele + d.byResp.Ela + d.byResp.Ambos;
  function segPct(v){ return respTotal > 0 ? (v / respTotal * 100) : 0; }
  var respSeg = respTotal > 0 ?
    '<div class="seg">' +
      '<span style="width:' + segPct(d.byResp.Ele) + '%;background:var(--cat-1)"></span>' +
      '<span style="width:' + segPct(d.byResp.Ela) + '%;background:var(--cat-2)"></span>' +
      '<span style="width:' + segPct(d.byResp.Ambos) + '%;background:var(--cat-3)"></span>' +
    '</div>' : '<div class="empty">Sem dados</div>';
  var respLegend = '<div class="legend">' +
    '<div class="item"><span class="dot" style="background:var(--cat-1)"></span>Ele ' + fmtMoney(d.byResp.Ele) + '</div>' +
    '<div class="item"><span class="dot" style="background:var(--cat-2)"></span>Ela ' + fmtMoney(d.byResp.Ela) + '</div>' +
    '<div class="item"><span class="dot" style="background:var(--cat-3)"></span>Ambos ' + fmtMoney(d.byResp.Ambos) + '</div>' +
  '</div>';

  var grpTotal = d.grp['Previsível'] + d.grp['Variável'] + d.grp['Investimento'];
  function gpct(v){ return grpTotal > 0 ? (v / grpTotal * 100) : 0; }
  var grpSeg = grpTotal > 0 ?
    '<div class="seg">' +
      '<span style="width:' + gpct(d.grp['Previsível']) + '%;background:var(--cat-1)"></span>' +
      '<span style="width:' + gpct(d.grp['Variável']) + '%;background:var(--cat-2)"></span>' +
      '<span style="width:' + gpct(d.grp['Investimento']) + '%;background:var(--cat-3)"></span>' +
    '</div>' : '<div class="empty">Sem dados</div>';
  var grpLegend = '<div class="legend">' +
    '<div class="item"><span class="dot" style="background:var(--cat-1)"></span>Previsível ' + fmtMoney(d.grp['Previsível']) + '</div>' +
    '<div class="item"><span class="dot" style="background:var(--cat-2)"></span>Variável ' + fmtMoney(d.grp['Variável']) + '</div>' +
    '<div class="item"><span class="dot" style="background:var(--cat-3)"></span>Investimento ' + fmtMoney(d.grp['Investimento']) + '</div>' +
  '</div>';

  var metasHtml = STATE.metas.map(function(m){
    var pct = m.valorAlvo > 0 ? clamp((m.valorAtual / m.valorAlvo) * 100, 0, 100) : 0;
    return '<div style="margin-bottom:14px">' +
      '<div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:5px">' +
        '<span style="font-weight:600">' + escapeHtml(m.nome) + '</span>' +
        '<span class="mono" style="color:var(--text-muted)">' + fmtMoney(m.valorAtual) + ' / ' + fmtMoney(m.valorAlvo) + '</span>' +
      '</div>' +
      '<div class="progress"><span style="width:' + pct + '%"></span></div>' +
    '</div>';
  }).join('');

  var html =
    '<h2 style="margin-bottom:2px">Visão geral</h2>' +
    '<p style="color:var(--text-muted);margin:0 0 18px;font-size:13px">' + escapeHtml(monthLabel(MONTH)) + '</p>' +
    renderReadonlyBanner() +
    '<div class="kpi-grid">' +
      '<div class="kpi"><div class="label">Renda conjunta</div><div class="value">' + fmtMoney(d.rendaConjunta) + '</div></div>' +
      '<div class="kpi"><div class="label">Gasto (s/ investim.)</div><div class="value">' + fmtMoney(d.gastoTotal) + '</div></div>' +
      '<div class="kpi"><div class="label">Aportes investimento</div><div class="value">' + fmtMoney(d.aportes) + '</div></div>' +
      '<div class="kpi"><div class="label">Saldo do mês</div><div class="value ' + (d.saldo >= 0 ? 'good' : 'critical') + '">' + fmtMoney(d.saldo) + '</div>' +
        '<div class="sub">Taxa de poupança: ' + (d.taxa * 100).toFixed(1) + '%</div></div>' +
    '</div>' +
    '<div class="grid-2">' +
      '<div class="card"><div class="section-title">Gastos por categoria</div><div class="barlist">' + catRows + '</div></div>' +
      '<div style="display:flex;flex-direction:column;gap:16px">' +
        '<div class="card"><div class="section-title">Por responsável</div>' + respSeg + respLegend + '</div>' +
        '<div class="card"><div class="section-title">Previsível vs. variável vs. investimento</div>' + grpSeg + grpLegend + '</div>' +
        '<div class="card"><div class="section-title">Metas</div>' + metasHtml + '</div>' +
      '</div>' +
    '</div>';
  document.getElementById('app').innerHTML = html;
}
function renderReadonlyBanner(){
  if (!READONLY) return '';
  return '<div class="readonly-banner">Modo somente leitura — peça acesso de edição no link compartilhado para adicionar ou alterar lançamentos.</div>';
}

/* ================= RENDER: LANÇAMENTOS ================= */
function renderLancamentos(){
  var txs = txForMonth(MONTH).slice().sort(function(a,b){ return (b.data || '').localeCompare(a.data || ''); });
  if (lancFiltro.texto) {
    var q = lancFiltro.texto.toLowerCase();
    txs = txs.filter(function(t){ return (t.descricao || '').toLowerCase().indexOf(q) !== -1; });
  }
  if (lancFiltro.categoria) txs = txs.filter(function(t){ return t.categoria === lancFiltro.categoria; });
  if (lancFiltro.responsavel) txs = txs.filter(function(t){ return t.responsavel === lancFiltro.responsavel; });

  var rows = txs.length ? txs.map(function(t){
    return '<tr>' +
      '<td>' + fmtDate(t.data) + '</td>' +
      '<td>' + escapeHtml(t.descricao) + '<div style="font-size:11.5px;color:var(--text-muted)">' + escapeHtml(t.categoria) + (t.subcategoria ? ' · ' + escapeHtml(t.subcategoria) : '') + '</div></td>' +
      '<td><span class="badge badge-' + (t.responsavel || '').toLowerCase() + '">' + escapeHtml(t.responsavel || '-') + '</span></td>' +
      '<td>' + escapeHtml(t.formaPagamento || '-') + '</td>' +
      '<td><span class="badge badge-' + (t.status || '').toLowerCase() + '">' + escapeHtml(t.status || '-') + '</span></td>' +
      '<td class="num">' + fmtMoney(t.valor) + '</td>' +
      '<td>' +
        '<button class="btn btn-ghost btn-sm" data-act="tx-edit" data-id="' + t.id + '" type="button">Editar</button>' +
        '<button class="btn btn-ghost btn-sm critical-text" data-act="tx-del" data-id="' + t.id + '" type="button">Excluir</button>' +
      '</td>' +
    '</tr>';
  }).join('') : '<tr><td colspan="7"><div class="empty">Nenhum lançamento encontrado para este mês/filtro.</div></td></tr>';

  var html =
    '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px">' +
      '<div><h2 style="margin-bottom:2px">Lançamentos</h2><p style="color:var(--text-muted);margin:0;font-size:13px">' + escapeHtml(monthLabel(MONTH)) + '</p></div>' +
      (READONLY ? '' : '<button class="btn btn-primary" data-act="tx-new" type="button">+ Novo lançamento</button>') +
    '</div>' +
    renderReadonlyBanner() +
    '<div class="card" style="margin-bottom:16px"><div class="filtro-grid">' +
      '<div class="field"><label>Buscar</label><input type="text" id="filtro-texto" placeholder="Descrição..." value="' + escapeHtml(lancFiltro.texto) + '"></div>' +
      '<div class="field"><label>Categoria</label>' + selectHtml('filtro-categoria', CATEGORIAS, lancFiltro.categoria) + '</div>' +
      '<div class="field"><label>Responsável</label>' + selectHtml('filtro-responsavel', RESPONSAVEL_OPTS, lancFiltro.responsavel) + '</div>' +
    '</div></div>' +
    '<div class="table-wrap"><table><thead><tr>' +
      '<th>Data</th><th>Descrição</th><th>Resp.</th><th>Forma</th><th>Status</th><th style="text-align:right">Valor</th><th></th>' +
    '</tr></thead><tbody>' + rows + '</tbody></table></div>';
  document.getElementById('app').innerHTML = html;

  document.getElementById('filtro-texto').addEventListener('input', function(e){ lancFiltro.texto = e.target.value; renderLancamentos(); });
  document.getElementById('filtro-categoria') && document.querySelector('select[name="filtro-categoria"]').addEventListener('change', function(e){ lancFiltro.categoria = e.target.value; renderLancamentos(); });
  document.querySelector('select[name="filtro-responsavel"]').addEventListener('change', function(e){ lancFiltro.responsavel = e.target.value; renderLancamentos(); });
}

function txFormHtml(tx){
  tx = tx || {data: MONTH + '-01', descricao:'', categoria:'', subcategoria:'', formaPagamento:'', responsavel:'', tipo:'', parcela:'', valor:'', status:'Pago'};
  return '<form class="formcard" id="tx-form">' +
    '<div class="field-row">' +
      '<div class="field"><label>Data</label><input type="date" name="data" value="' + escapeHtml(tx.data) + '" required></div>' +
      '<div class="field"><label>Valor (R$)</label><input type="number" step="0.01" min="0" name="valor" value="' + escapeHtml(tx.valor) + '" required></div>' +
    '</div>' +
    '<div class="field"><label>Descrição</label><input type="text" name="descricao" value="' + escapeHtml(tx.descricao) + '" placeholder="Ex: Supermercado Zaffari" required></div>' +
    '<div class="field-row">' +
      '<div class="field"><label>Categoria</label>' + selectHtml('categoria', CATEGORIAS, tx.categoria, 'required') + '</div>' +
      '<div class="field"><label>Subcategoria</label>' + selectHtml('subcategoria', SUBCATEGORIAS, tx.subcategoria) + '</div>' +
    '</div>' +
    '<div class="field-row">' +
      '<div class="field"><label>Forma de pagamento</label>' + selectHtml('formaPagamento', FORMA_PGTO_OPTS, tx.formaPagamento) + '</div>' +
      '<div class="field"><label>Responsável</label>' + selectHtml('responsavel', RESPONSAVEL_OPTS, tx.responsavel, 'required') + '</div>' +
    '</div>' +
    '<div class="field-row">' +
      '<div class="field"><label>Tipo</label>' + selectHtml('tipo', TIPO_OPTS, tx.tipo, 'required') + '</div>' +
      '<div class="field"><label>Status</label>' + selectHtml('status', STATUS_OPTS, tx.status) + '</div>' +
    '</div>' +
    '<div class="field"><label>Parcela (opcional)</label><input type="text" name="parcela" value="' + escapeHtml(tx.parcela) + '" placeholder="Ex: 3/12"></div>' +
    '<div class="actions"><button type="button" class="btn" data-act="modal-close">Cancelar</button><button type="submit" class="btn btn-primary">Salvar</button></div>' +
  '</form>';
}
function openTxModal(tx){
  editingTxId = tx ? tx.id : null;
  openModal(tx ? 'Editar lançamento' : 'Novo lançamento', txFormHtml(tx));
  document.getElementById('tx-form').addEventListener('submit', function(e){
    e.preventDefault();
    var fd = new FormData(e.target);
    var payload = {
      data: fd.get('data'), descricao: (fd.get('descricao') || '').trim(),
      categoria: fd.get('categoria'), subcategoria: fd.get('subcategoria') || '',
      formaPagamento: fd.get('formaPagamento') || '', responsavel: fd.get('responsavel'),
      tipo: fd.get('tipo'), status: fd.get('status') || 'Pago', parcela: fd.get('parcela') || '',
      valor: Number(fd.get('valor')) || 0
    };
    mutate(function(next){
      if (editingTxId) {
        var idx = next.transacoes.findIndex(function(t){ return t.id === editingTxId; });
        if (idx !== -1) next.transacoes[idx] = Object.assign({id: editingTxId}, payload);
      } else {
        payload.id = uid('tx');
        next.transacoes.push(payload);
      }
    });
    closeModal();
    showToast('Lançamento salvo.');
  });
}

/* ================= RENDER: RECORRENTES ================= */
function renderRecorrentes(){
  var txs = txForMonth(MONTH);
  var rows = STATE.recorrentes.map(function(rec){
    var real = valorRealRecorrente(rec, txs);
    var esperado = Number(rec.valorEsperado) || 0;
    var diff = real - esperado;
    var diffCls = diff > 0.005 ? 'critical-text' : 'good-text';
    return '<tr>' +
      '<td>' + escapeHtml(rec.item) + '<div style="font-size:11.5px;color:var(--text-muted)">' + escapeHtml(rec.categoria) + ' · ' + escapeHtml(rec.subcategoria) + '</div></td>' +
      '<td><span class="badge badge-' + (rec.responsavel || '').toLowerCase() + '">' + escapeHtml(rec.responsavel || '-') + '</span></td>' +
      '<td>' + escapeHtml(rec.forma || '-') + '</td>' +
      '<td class="num">' + (READONLY ?
        fmtMoney(esperado) :
        '<input type="number" step="0.01" min="0" class="num" style="width:110px" data-act="rec-esperado" data-id="' + rec.id + '" value="' + esperado + '">') + '</td>' +
      '<td class="num">' + fmtMoney(real) + '</td>' +
      '<td class="num ' + diffCls + '">' + (diff > 0 ? '+' : '') + fmtMoney(diff) + '</td>' +
    '</tr>';
  }).join('');
  var html =
    '<h2 style="margin-bottom:2px">Despesas recorrentes &amp; cartão</h2>' +
    '<p style="color:var(--text-muted);margin:0 0 16px;font-size:13px">' + escapeHtml(monthLabel(MONTH)) + ' — valor real calculado a partir dos lançamentos do mês.</p>' +
    renderReadonlyBanner() +
    '<div class="table-wrap"><table><thead><tr>' +
      '<th>Item</th><th>Resp.</th><th>Forma</th><th style="text-align:right">Esperado</th><th style="text-align:right">Real do mês</th><th style="text-align:right">Diferença</th>' +
    '</tr></thead><tbody>' + rows + '</tbody></table></div>';
  document.getElementById('app').innerHTML = html;
}

/* ================= RENDER: METAS ================= */
function renderMetas(){
  var txs = txForMonth(MONTH);
  var cards = STATE.metas.map(function(m){
    var pct = m.valorAlvo > 0 ? clamp((m.valorAtual / m.valorAlvo) * 100, 0, 100) : 0;
    var contrib = contribMeta(m, txs);
    var restantes = mesesRestantes(m.prazo);
    var faltante = Math.max(0, (Number(m.valorAlvo) || 0) - (Number(m.valorAtual) || 0));
    var aporteNecessario = (restantes && restantes > 0) ? (faltante / restantes) : null;
    return '<div class="card" style="margin-bottom:16px">' +
      '<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">' +
        '<h3 style="margin:0">' + escapeHtml(m.nome) + '</h3>' +
        '<span class="mono" style="font-size:13px;color:var(--text-muted)">' + pct.toFixed(0) + '% concluído</span>' +
      '</div>' +
      '<div class="progress" style="margin:10px 0 14px"><span style="width:' + pct + '%"></span></div>' +
      '<div class="field-row">' +
        '<div class="field"><label>Valor atual</label><input type="number" step="0.01" min="0" data-act="meta-field" data-field="valorAtual" data-id="' + m.id + '" value="' + (m.valorAtual != null ? m.valorAtual : '') + '"' + (READONLY?' disabled':'') + '></div>' +
        '<div class="field"><label>Valor alvo</label><input type="number" step="0.01" min="0" data-act="meta-field" data-field="valorAlvo" data-id="' + m.id + '" value="' + (m.valorAlvo != null ? m.valorAlvo : '') + '"' + (READONLY?' disabled':'') + '></div>' +
      '</div>' +
      '<div class="field-row" style="margin-top:12px">' +
        '<div class="field"><label>Prazo</label><input type="date" data-act="meta-field" data-field="prazo" data-id="' + m.id + '" value="' + escapeHtml(m.prazo || '') + '"' + (READONLY?' disabled':'') + '></div>' +
        '<div class="field"><label>Contribuição planejada/mês</label><input type="number" step="0.01" min="0" data-act="meta-field" data-field="contribPlanejada" data-id="' + m.id + '" value="' + (m.contribPlanejada != null ? m.contribPlanejada : '') + '"' + (READONLY?' disabled':'') + '></div>' +
      '</div>' +
      '<div style="display:flex;gap:22px;flex-wrap:wrap;margin-top:14px;font-size:12.5px;color:var(--text-2)">' +
        '<span>Contribuição no mês: <b class="mono">' + fmtMoney(contrib) + '</b></span>' +
        '<span>Faltam: <b class="mono">' + fmtMoney(faltante) + '</b></span>' +
        (restantes != null ? '<span>Meses restantes: <b class="mono">' + Math.max(0,restantes) + '</b></span>' : '') +
        (aporteNecessario != null ? '<span>Aporte necessário/mês: <b class="mono">' + fmtMoney(aporteNecessario) + '</b></span>' : '') +
      '</div>' +
    '</div>';
  }).join('');
  document.getElementById('app').innerHTML =
    '<h2 style="margin-bottom:2px">Metas &amp; investimentos</h2>' +
    '<p style="color:var(--text-muted);margin:0 0 16px;font-size:13px">' + escapeHtml(monthLabel(MONTH)) + '</p>' +
    renderReadonlyBanner() + cards;
}

/* ================= RENDER: AJUSTES ================= */
function renderAjustes(){
  document.getElementById('app').innerHTML =
    '<h2 style="margin-bottom:2px">Ajustes</h2>' +
    '<p style="color:var(--text-muted);margin:0 0 16px;font-size:13px">Renda mensal e preferências de exibição.</p>' +
    renderReadonlyBanner() +
    '<div class="card" style="max-width:480px;margin-bottom:16px"><div class="section-title">Renda mensal</div>' +
      '<div class="field-row">' +
        '<div class="field"><label>Henrique</label><input type="number" step="0.01" min="0" data-act="renda-field" data-field="henrique" value="' + (STATE.renda.henrique != null ? STATE.renda.henrique : '') + '"' + (READONLY?' disabled':'') + '></div>' +
        '<div class="field"><label>Carol</label><input type="number" step="0.01" min="0" data-act="renda-field" data-field="carol" value="' + (STATE.renda.carol != null ? STATE.renda.carol : '') + '"' + (READONLY?' disabled':'') + '></div>' +
      '</div>' +
    '</div>' +
    '<div class="card" style="max-width:480px"><div class="section-title">Aparência</div>' +
      '<div class="field"><label>Tema</label><select id="theme-select">' +
        '<option value="system"' + (THEME==='system'?' selected':'') + '>Automático (sistema)</option>' +
        '<option value="light"' + (THEME==='light'?' selected':'') + '>Claro</option>' +
        '<option value="dark"' + (THEME==='dark'?' selected':'') + '>Escuro</option>' +
      '</select></div>' +
    '</div>';
  document.getElementById('theme-select').addEventListener('change', function(e){
    THEME = e.target.value; lsSet('ofc_theme', THEME); applyTheme(THEME);
  });
}

/* ================= ROUTER ================= */
function renderApp(){
  renderShell();
  if (ACTIVE_TAB === 'dashboard') renderDashboard();
  else if (ACTIVE_TAB === 'lancamentos') renderLancamentos();
  else if (ACTIVE_TAB === 'recorrentes') renderRecorrentes();
  else if (ACTIVE_TAB === 'metas') renderMetas();
  else renderAjustes();
}

/* ================= EVENTS (delegated) ================= */
document.addEventListener('click', function(e){
  var el = e.target.closest('[data-act]');
  if (!el) return;
  var act = el.getAttribute('data-act');
  if (act === 'nav') {
    ACTIVE_TAB = el.getAttribute('data-tab'); lsSet('ofc_tab', ACTIVE_TAB); renderApp();
  } else if (act === 'modal-close' || act === 'modal-backdrop') {
    if (act === 'modal-backdrop' && e.target !== el) return;
    closeModal();
  } else if (act === 'tx-new') {
    openTxModal(null);
  } else if (act === 'tx-edit') {
    var id = el.getAttribute('data-id');
    var tx = STATE.transacoes.find(function(t){ return t.id === id; });
    if (tx) openTxModal(tx);
  } else if (act === 'tx-del') {
    var did = el.getAttribute('data-id');
    openConfirm('Excluir este lançamento? Esta ação não pode ser desfeita.', function(){
      mutate(function(next){ next.transacoes = next.transacoes.filter(function(t){ return t.id !== did; }); });
      showToast('Lançamento excluído.');
    });
  } else if (act === 'retry-publish') {
    queuePublish();
  }
});
document.addEventListener('change', function(e){
  var el = e.target;
  if (el.id === 'month-input') {
    MONTH = el.value || currentMonthStr(); lsSet('ofc_month', MONTH); renderApp(); return;
  }
  var act = el.getAttribute && el.getAttribute('data-act');
  if (act === 'rec-esperado') {
    var rid = el.getAttribute('data-id'); var v = Number(el.value) || 0;
    mutate(function(next){
      var r = next.recorrentes.find(function(x){ return x.id === rid; });
      if (r) r.valorEsperado = v;
    });
  } else if (act === 'meta-field') {
    var mid = el.getAttribute('data-id'); var field = el.getAttribute('data-field');
    var val = (field === 'prazo') ? el.value : (Number(el.value) || 0);
    mutate(function(next){
      var m = next.metas.find(function(x){ return x.id === mid; });
      if (m) m[field] = val;
    });
  } else if (act === 'renda-field') {
    var field2 = el.getAttribute('data-field'); var val2 = Number(el.value) || 0;
    mutate(function(next){ next.renda[field2] = val2; });
  }
});

/* ================= INIT ================= */
function init(){
  document.getElementById('app').innerHTML = '<div class="empty">Carregando…</div>';
  fetch(API_STATE_URL).then(function(r){
    if (r.status === 401 || r.status === 403) { var e = new Error('auth'); e.code = 'auth'; throw e; }
    if (!r.ok) throw new Error('load_failed');
    return r.json();
  }).then(function(d){
    STATE = d.state; STATE_VERSION = d.version; window.__STATE__ = STATE;
    renderApp();
    setSyncBadge('saved');
    setInterval(pollState, 6000);
  }).catch(function(e){
    console.error('cowhand init failed:', e);
    if (e && e.code === 'auth') { READONLY = true; }
    document.getElementById('app').innerHTML = '<div class="empty"><div class="big">⚠️</div>Não foi possível carregar os dados. Recarregue a página.</div>';
    setSyncBadge('pending');
  });
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
else init();

})();
'''

# =====================================================================================
# CORE HTML TEMPLATE
# =====================================================================================
CORE = r'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Orçamento Henrique &amp; Carol</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Public+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>__APP_CSS__</style>
</head>
<body>
<div id="shell">
  <nav id="sidebar">
    <div class="brand"><div class="brand-mark">H&amp;C</div>Orçamento</div>
    <div class="navlist" id="navlist-desktop"></div>
    <div class="sidebar-foot" id="sidebar-foot"></div>
  </nav>
  <main id="main">
    <header id="topbar">
      <div class="month-field"><label for="month-input">Mês</label><input type="month" id="month-input"></div>
      <div class="spacer"></div>
      <div id="topbar-actions"></div>
    </header>
    <div id="appwrap"><div id="app"></div></div>
  </main>
</div>
<nav id="mobiletabs"></nav>
<div id="modal-root"></div>
<div class="toast-wrap" id="toast-wrap"></div>
<script>__APP_JS__</script>
</body>
</html>'''

# =====================================================================================
# BUILD
# =====================================================================================
def build_final(core_src):
    # bake in static taxonomy + CSS + JS. index.html no longer embeds any state —
    # state lives server-side and is fetched/saved via /api/state (see server.js).
    src = core_src.replace('__APP_CSS__', CSS, 1)
    js = APP_JS
    js = js.replace('__CATEGORIAS_JSON__', json.dumps(CATEGORIAS, ensure_ascii=False))
    js = js.replace('__SUBCATEGORIAS_JSON__', json.dumps(SUBCATEGORIAS, ensure_ascii=False))
    js = js.replace('__RESPONSAVEL_OPTS_JSON__', json.dumps(RESPONSAVEL_OPTS, ensure_ascii=False))
    js = js.replace('__TIPO_OPTS_JSON__', json.dumps(TIPO_OPTS, ensure_ascii=False))
    js = js.replace('__FORMA_PGTO_OPTS_JSON__', json.dumps(FORMA_PGTO_OPTS, ensure_ascii=False))
    js = js.replace('__STATUS_OPTS_JSON__', json.dumps(STATUS_OPTS, ensure_ascii=False))
    src = src.replace('__APP_JS__', js, 1)
    return src

final_html = build_final(CORE)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(OUT_DIR, 'index.html')
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(final_html)
print("Written", OUT_PATH, "length:", len(final_html))

SEED_PATH = os.path.join(OUT_DIR, 'seed_data.json')
with open(SEED_PATH, 'w', encoding='utf-8') as f:
    json.dump(INITIAL_STATE, f, ensure_ascii=False, indent=2)
print("Written", SEED_PATH)
