#!/usr/bin/env python3
# scraper_robusto.py
import requests
from bs4 import BeautifulSoup
import csv
import re
import time
from datetime import datetime

SEARCH_RESULTS_URL = "https://store.steampowered.com/search/results/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
}

def fetch_results_html(start=0, count=50, cc="BR", lang="portuguese", mode="specials"):
    params = {"start": start, "count": count, "cc": cc, "l": lang}
    if mode == "specials":
        params["specials"] = 1
    elif mode == "topsellers":
        params["filter"] = "topsellers"
    else:
        params["filter"] = mode
    resp = requests.get(SEARCH_RESULTS_URL, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    try:
        data = resp.json()
        html = data.get("results_html", resp.text)
    except ValueError:
        html = resp.text
    return html

def find_discount_in_text(text):
    """
    Procura por padrões tipo '-75%' em todo o texto e retorna o primeiro/último match.
    """
    if not text:
        return None
    # normaliza NBSP
    text = text.replace("\xa0", " ")
    m = re.findall(r'-\d{1,3}%+', text)
    if m:
        # prefere o primeiro/último? vamos pegar o primeiro relevante (normalmente único)
        return m[0]
    return None

def find_last_price_in_text(text):
    """
    Encontra o último padrão de preço (R$ 74,97 / $19.99 / 49,99) no bloco de texto.
    Retorna string ou None.
    """
    if not text:
        return None
    text = text.replace("\xa0", " ")
    # padrões: R$ 49,99 | R$49,99 | $19.99 | 49,99 | 1.234,56
    patterns = [
        r'R\$\s*[\d\.,]+',
        r'[\$\£\€]\s*[\d\.,]+',
        r'(?<![\d\.,])\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2}'
    ]
    matches = []
    for p in patterns:
        matches.extend(re.findall(p, text))
    if matches:
        # pegar o último preço encontrado (normalmente é o preço final)
        return matches[-1].strip()
    return None

def scrape_names_links(limit=100, mode="specials", per_page=50, cc="BR"):
    start = 0
    collected = []
    while True:
        html = fetch_results_html(start=start, count=per_page, cc=cc, mode=mode)
        soup = BeautifulSoup(html, "lxml")
        items = soup.select(".search_result_row")
        if not items:
            break

        for item in items:
            title_elem = item.select_one(".title")
            name = title_elem.get_text(strip=True) if title_elem else "N/A"
            link = item.get("href", "N/A").split("?")[0]

            # Tenta extrair desconto via seletor conhecido
            discount_elem = item.select_one(".search_discount span")
            discount = discount_elem.get_text(strip=True) if discount_elem else None

            # fallback: procura no texto do item
            item_text = item.get_text(" ", strip=True)
            if not discount:
                discount = find_discount_in_text(item_text)

            # tenta extrair preço final (último preço no bloco)
            final_price = None
            price_block = item.select_one(".search_price")
            if price_block:
                final_price = find_last_price_in_text(price_block.get_text(" ", strip=True))
            if not final_price:
                final_price = find_last_price_in_text(item_text)

            # Normaliza resultados
            if not discount:
                discount_label = "0%"
            else:
                discount_label = discount

            preco_label = final_price if final_price else "N/A"

            collected.append({
                "Nome": name,
                "Link": link,
                "Desconto": discount_label,
                "PrecoFinal": preco_label
            })

            if limit and len(collected) >= limit:
                return collected

        # paginação / "scroll"
        start += per_page
        # pausa leve
        time.sleep(0.6)

        # se limit == 0, só rodamos uma página (comportamento simples)
        if limit == 0:
            break

    return collected

def save_csv(games, prefix="steam_simple"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{ts}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Nome", "Link", "Desconto", "PrecoFinal"])
        writer.writeheader()
        for g in games:
            writer.writerow(g)
    return filename

def format_terminal_list(games):
    formatted = []
    for g in games:
        desconto = g.get("Desconto", "0%")
        preco = g.get("PrecoFinal", "N/A")
        if desconto.strip() in ("0%", "0 %", "", None):
            label = f"Sem desconto {preco}"
        else:
            label = f"{desconto} {preco}"
        formatted.append(f"{g.get('Nome')} ({label})")
    return ", ".join(formatted)

if __name__ == "__main__":
    # ajustes rápidos: limite desejado e modo
    LIMIT = 200           # quantos jogos coletar (troca aqui se quiser)
    MODE = "specials"     # "specials" ou "topsellers"
    PER_PAGE = 50
    CC = "BR"

    games = scrape_names_links(limit=LIMIT, mode=MODE, per_page=PER_PAGE, cc=CC)
    if not games:
        print("Nenhum jogo encontrado — pode ser bloqueio ou mudança de estrutura.")
        raise SystemExit(1)

    csv_file = save_csv(games, prefix=("steam_specials" if MODE=="specials" else "steam_topsellers"))
    print(f"Arquivo salvo: {csv_file}\n")

    resumo = format_terminal_list(games)
    print("Resumo (nomes):")
    print(resumo)
    total = len(games)
    with_discount = sum(1 for g in games if g.get("Desconto") and g.get("Desconto").strip() not in ("0%", "", None))
    print(f"\nTotal coletado: {total} — Com desconto: {with_discount}")
