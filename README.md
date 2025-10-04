# Steam Scraper

Este projeto é um **web scraper** que coleta informações da loja da Steam, listando jogos em **promoção** ou da lista de **mais vendidos**. Os dados coletados incluem:

* Nome do jogo
* Link para a página
* Desconto (se houver)
* Preço final

Os resultados são salvos em um arquivo CSV e também exibidos no terminal.

---

## Requisitos

Instale as dependências com:

```bash
pip install -r requirements.txt
```

O arquivo `requirements.txt` deve conter:

```txt
requests
beautifulsoup4
lxml
```

---

## Como usar

1. Clone este repositório e entre na pasta do projeto.

2. Execute o script principal:

```bash
python scraper.py
```

3. Por padrão, o código vai buscar **200 jogos em promoção** (modo `specials`). Os resultados ficam salvos em um CSV com nome no formato:

```
steam_specials_YYYYMMDD_HHMMSS.csv
```

4. Se quiser alterar o modo para **topsellers**, edite o arquivo `scraper.py` na seção final:

```python
LIMIT = 200           # quantidade de jogos a coletar
MODE = "topsellers"   # opções: "specials" ou "topsellers"
```

---

## Saída no terminal

O programa também mostra um resumo dos jogos coletados no terminal, no formato:

```
Nome do Jogo 1 (-50% R$ 49,99), Nome do Jogo 2 (Sem desconto R$ 199,90), ...
```

E no final exibe estatísticas:

```
Total coletado: 200 — Com desconto: 150
```

---

## Observações

* Pode haver bloqueios ocasionais da Steam se muitas requisições forem feitas rapidamente.
* Use `MODE = "specials"` para promoções e `MODE = "topsellers"` para os mais vendidos.
* O scraper já faz pequenas pausas automáticas para evitar sobrecarga.
