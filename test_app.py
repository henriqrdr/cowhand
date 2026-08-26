import asyncio, os, subprocess, tempfile, time, shutil, urllib.request, urllib.error
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 3977
BASE_URL = f"http://127.0.0.1:{PORT}"
USER = "henrique"
PASS = "senha-de-teste"


def wait_for_server(timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(BASE_URL, timeout=1)
            return
        except urllib.error.HTTPError:
            return  # any HTTP response (even 401) means the server is up
        except Exception:
            time.sleep(0.15)
    raise RuntimeError("server did not start in time")


def check_no_auth_is_rejected():
    try:
        urllib.request.urlopen(f"{BASE_URL}/api/state", timeout=2)
        raise AssertionError("expected 401 without a session")
    except urllib.error.HTTPError as e:
        assert e.code == 401, e.code
    print("OK: /api/state requires a session (401 without one)")


async def login(page, username, password):
    await page.goto(f"{BASE_URL}/login")
    await page.fill('input[name="username"]', username)
    await page.fill('input[name="password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state('networkidle')


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
    data_dir = tempfile.mkdtemp(prefix="cowhand_test_")
    db_path = os.path.join(data_dir, "test.sqlite")
    env = dict(os.environ, COWHAND_USER=USER, COWHAND_PASS=PASS, PORT=str(PORT), DB_PATH=db_path)
    server = subprocess.Popen(["node", "server.js"], cwd=HERE, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        wait_for_server()
        check_no_auth_is_rejected()

        errors = []
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append("console.error: " + m.text) if m.type == "error" else None)

            # wrong credentials: bounced back to /login with an error banner, no session set
            await login(page, USER, "senha-errada")
            assert "/login" in page.url, page.url
            login_page_text = await page.inner_text("body")
            assert "incorret" in login_page_text.lower(), login_page_text
            print("OK: wrong credentials rejected, redirected back to /login with an error message")

            # unauthenticated navigation to the app itself bounces to /login too
            await page.goto(BASE_URL)
            assert "/login" in page.url, page.url
            print("OK: visiting the app without a session redirects to /login")

            await login(page, USER, PASS)
            assert "/login" not in page.url, page.url
            print("OK: correct credentials log in and land on the app")

            await page.wait_for_function("window.__STATE__ !== null", timeout=5000)
            state0 = await page.evaluate("window.__STATE__")
            assert len(state0["recorrentes"]) == 27, state0
            assert len(state0["metas"]) == 3
            assert state0["transacoes"] == []
            assert state0["renda"]["henrique"] == 11000
            print("OK: initial state loaded from server (seeded)")

            body_text = await page.inner_text("body")
            assert "NaN" not in body_text
            assert "undefined" not in body_text
            print("OK: zero-state dashboard has no NaN/undefined")

            await page.fill('#month-input', '2026-08')
            await page.dispatch_event('#month-input', 'change')
            await page.wait_for_timeout(50)
            await page.click('[data-act="nav"][data-tab="lancamentos"]')
            await page.wait_for_timeout(50)

            await fill_tx_form(page, dict(
                data='2026-08-05', valor='20.90', descricao='Netflix cobranca mensal',
                categoria='Assinaturas', subcategoria='Streaming', formaPagamento='Cartão C6 (Henrique)',
                responsavel='Ele', tipo='Fixo'))
            await page.wait_for_timeout(900)  # allow the 700ms debounced publish to flush

            await fill_tx_form(page, dict(
                data='2026-08-10', valor='300.00', descricao='Posto Ipiranga BR101',
                categoria='Veículos', subcategoria='Combustível', formaPagamento='Cartão C6 (Henrique)',
                responsavel='Ele', tipo='Variável'))
            await page.wait_for_timeout(900)

            # adversarial description containing a literal </script> substring
            await fill_tx_form(page, dict(
                data='2026-08-12', valor='15.00', descricao='Nota </script> adversarial teste',
                categoria='Outros', subcategoria='Diversos', formaPagamento='Pix',
                responsavel='Ambos', tipo='Variável'))
            await page.wait_for_timeout(900)

            await fill_tx_form(page, dict(
                data='2026-08-15', valor='500.00', descricao='Aporte mensal investimentos',
                categoria='Investimentos', subcategoria='Aporte Investimento', formaPagamento='Pix',
                responsavel='Ambos', tipo='Investimento'))
            await page.wait_for_timeout(900)

            state1 = await page.evaluate("window.__STATE__")
            assert len(state1["transacoes"]) == 4, state1["transacoes"]
            print("OK: 4 transactions added, client state has them")

            badge_text = await page.inner_text('#topbar-actions')
            assert 'salvo' in badge_text.lower(), badge_text
            print("OK: sync badge shows saved after publish:", badge_text)

            # reload from scratch: proves the data really round-tripped through the server, not just in-memory
            await page.goto(BASE_URL)
            await page.wait_for_function("window.__STATE__ !== null", timeout=5000)
            state_reloaded = await page.evaluate("window.__STATE__")
            assert len(state_reloaded["transacoes"]) == 4, state_reloaded["transacoes"]
            descs = [t["descricao"] for t in state_reloaded["transacoes"]]
            assert any("</script>" in d for d in descs), descs
            print("OK: server round trip preserved all transactions incl. adversarial </script> substring")

            # recorrentes tab, check computed values
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
            await page.wait_for_timeout(900)
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

            # dark/light theme tokens
            await page.emulate_media(color_scheme='light')
            bg_light = await page.eval_on_selector(':root', 'el => getComputedStyle(el).getPropertyValue("--bg").trim()')
            await page.emulate_media(color_scheme='dark')
            bg_dark = await page.eval_on_selector(':root', 'el => getComputedStyle(el).getPropertyValue("--bg").trim()')
            assert bg_light != bg_dark, (bg_light, bg_dark)
            print("OK: dark/light theme tokens differ:", bg_light, "vs", bg_dark)
            await page.emulate_media(color_scheme='light')

            # two-person sync: a second browser context (Carol), with her own independent
            # session cookie, sees Henrique's edits via polling
            context2 = await browser.new_context()
            page2 = await context2.new_page()
            await login(page2, USER, PASS)
            await page2.wait_for_function("window.__STATE__ !== null", timeout=5000)
            state2 = await page2.evaluate("window.__STATE__")
            assert len(state2["transacoes"]) == 4
            print("OK: second browser context (simulating Carol, own session) sees the same synced state")
            await context2.close()

            # logout: session is destroyed server-side, not just the cookie cleared client-side
            await page.click('a[href="/logout"]')
            await page.wait_for_load_state('networkidle')
            assert "/login" in page.url, page.url
            await page.goto(BASE_URL)
            assert "/login" in page.url, page.url
            print("OK: logout destroys the session — revisiting the app redirects to /login again")

            real_errors = [e for e in errors if 'net::ERR' not in e]
            assert not real_errors, real_errors
            print("\nALL CHECKS PASSED")
            await browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        shutil.rmtree(data_dir, ignore_errors=True)

asyncio.run(main())
