import asyncio, os, re, json
from playwright.async_api import async_playwright

APP_PATH = "/home/claude/orcamento_app/index.html"
GEN1_PATH = "/home/claude/orcamento_app/index_gen1.html"

async def fill_tx_form(page, data):
    await page.click('[data-act="tx-new"]')
    await page.wait_for_selector('#tx-form')
    await page.fill('input[name="data"]', data['data'])
    await page.fill('input[name="valor"]', str(data['valor']))
    await page.fill('input[name="descricao"]', data['descricao'])
    await page.select_option('select[name="categoria"]', data['categoria'])
    if data.get('subcategoria'):
        await page.select_option('select[name="subcategoria"]', data['subcategoria'])
    if data.get('formaPagamento'):
        await page.select_option('select[name="formaPagamento"]', data['formaPagamento'])
    await page.select_option('select[name="responsavel"]', data['responsavel'])
    await page.select_option('select[name="tipo"]', data['tipo'])
    await page.click('#tx-form button[type="submit"]')

async def main():
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append("console.error: " + m.text) if m.type == "error" else None)

        await page.goto(f"file://{APP_PATH}")
        state0 = await page.evaluate("window.__STATE__")
        assert len(state0["recorrentes"]) == 27, state0
        assert len(state0["metas"]) == 3
        assert state0["transacoes"] == []
        assert state0["renda"]["henrique"] == 11000
        print("OK: initial state shape")

        body_text = await page.inner_text("body")
        assert "NaN" not in body_text
        assert "undefined" not in body_text
        print("OK: zero-state dashboard has no NaN/undefined")

        # set month to a fixed test month
        await page.fill('#month-input', '2026-08')
        await page.dispatch_event('#month-input', 'change')
        await page.wait_for_timeout(50)
        await page.click('[data-act="nav"][data-tab="lancamentos"]')
        await page.wait_for_timeout(50)

        # add a Netflix transaction (matches recorrente via 'chave')
        await fill_tx_form(page, dict(
            data='2026-08-05', valor='20.90', descricao='Netflix cobranca mensal',
            categoria='Assinaturas', subcategoria='Streaming', formaPagamento='Cartão C6 (Henrique)',
            responsavel='Ele', tipo='Fixo'))
        await page.wait_for_timeout(80)

        # add a Combustivel transaction (matches by categoria+subcategoria only, no chave)
        await fill_tx_form(page, dict(
            data='2026-08-10', valor='300.00', descricao='Posto Ipiranga BR101',
            categoria='Veículos', subcategoria='Combustível', formaPagamento='Cartão C6 (Henrique)',
            responsavel='Ele', tipo='Variável'))
        await page.wait_for_timeout(80)

        # adversarial transaction containing a literal </script> substring
        await fill_tx_form(page, dict(
            data='2026-08-12', valor='15.00', descricao='Nota </script> adversarial teste',
            categoria='Outros', subcategoria='Diversos', formaPagamento='Pix',
            responsavel='Ambos', tipo='Variável'))
        await page.wait_for_timeout(80)

        # investment transaction toward meta m1
        await fill_tx_form(page, dict(
            data='2026-08-15', valor='500.00', descricao='Aporte mensal investimentos',
            categoria='Investimentos', subcategoria='Aporte Investimento', formaPagamento='Pix',
            responsavel='Ambos', tipo='Investimento'))
        await page.wait_for_timeout(80)

        state1 = await page.evaluate("window.__STATE__")
        assert len(state1["transacoes"]) == 4, state1["transacoes"]
        print("OK: 4 transactions added, state has them")

        # go to recorrentes tab, check computed values
        await page.click('[data-act="nav"][data-tab="recorrentes"]')
        await page.wait_for_timeout(50)
        rec_text = await page.inner_text("#app")
        assert "R$\xa020,90" in rec_text or "R$ 20,90" in rec_text, rec_text[:800]
        assert "R$\xa0300,00" in rec_text or "R$ 300,00" in rec_text, rec_text[:800]
        print("OK: recorrentes matching (Netflix via chave, Combustível via categoria+subcategoria) reflected")

        # metas tab: set alvo for m1 and check contribuição do mês
        await page.click('[data-act="nav"][data-tab="metas"]')
        await page.wait_for_timeout(50)
        alvo_inputs = await page.query_selector_all('input[data-field="valorAlvo"]')
        await alvo_inputs[0].fill('10000')
        await alvo_inputs[0].dispatch_event('change')
        await page.wait_for_timeout(80)
        metas_text = await page.inner_text("#app")
        assert "500,00" in metas_text
        print("OK: metas tab reflects investment contribution")

        # dashboard KPIs sanity
        await page.click('[data-act="nav"][data-tab="dashboard"]')
        await page.wait_for_timeout(50)
        dash_text = await page.inner_text("#app")
        assert "NaN" not in dash_text
        print("OK: dashboard after mutations has no NaN")

        # mobile layout check
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(50)
        sidebar_display = await page.eval_on_selector('#sidebar', 'el => getComputedStyle(el).display')
        mobiletabs_display = await page.eval_on_selector('#mobiletabs', 'el => getComputedStyle(el).display')
        assert sidebar_display == 'none', sidebar_display
        assert mobiletabs_display == 'flex', mobiletabs_display
        print("OK: mobile layout collapses sidebar, shows bottom tabs")
        await page.set_viewport_size({"width": 1280, "height": 900})

        # dark theme check via prefers-color-scheme
        await page.emulate_media(color_scheme='light')
        bg_light = await page.eval_on_selector(':root', 'el => getComputedStyle(el).getPropertyValue("--bg").trim()')
        await page.emulate_media(color_scheme='dark')
        bg_dark = await page.eval_on_selector(':root', 'el => getComputedStyle(el).getPropertyValue("--bg").trim()')
        assert bg_light != bg_dark, (bg_light, bg_dark)
        print("OK: dark/light theme tokens differ:", bg_light, "vs", bg_dark)
        await page.emulate_media(color_scheme='light')

        # sync badge should show local mode (no window.claude in bare browser)
        badge_text = await page.inner_text('#topbar-actions')
        assert 'local' in badge_text.lower() or 'modo local' in badge_text.lower(), badge_text
        print("OK: sync badge shows local-only mode:", badge_text)

        # self-publish round trip using the real, full app state
        gen1_html = await page.evaluate("window.__buildPublishHtml__(window.__STATE__)")
        assert gen1_html.startswith("<!doctype html>")
        with open(GEN1_PATH, "w", encoding="utf-8") as f:
            f.write(gen1_html)

        await page.goto(f"file://{GEN1_PATH}")
        state_gen1 = await page.evaluate("window.__STATE__")
        assert len(state_gen1["transacoes"]) == 4, state_gen1["transacoes"]
        descs = [t["descricao"] for t in state_gen1["transacoes"]]
        assert any("</script>" in d for d in descs), descs
        assert len(state_gen1["recorrentes"]) == 27
        print("OK: self-publish round trip preserved full state incl. adversarial </script> substring")

        # confirm gen1 still fully functional: nav still works, no console errors introduced
        await page.click('[data-act="nav"][data-tab="lancamentos"]')
        await page.wait_for_timeout(50)
        lanc_text = await page.inner_text("#app")
        assert "adversarial" in lanc_text
        print("OK: gen1 app still interactive and renders carried-over transactions")

        sizes = [os.path.getsize(APP_PATH), os.path.getsize(GEN1_PATH)]
        print("Sizes:", sizes)
        assert max(sizes) < 3 * min(sizes)

        # ignore network errors from Google Fonts (no egress in this sandbox; allowed on the real Artifact host)
        real_errors = [e for e in errors if 'ERR_TUNNEL_CONNECTION_FAILED' not in e and 'net::ERR' not in e]
        print("\nAll captured (incl. expected font-network noise):", errors)
        assert not real_errors, real_errors

        print("\nALL CHECKS PASSED")
        await browser.close()

asyncio.run(main())
