import requests, re, json, os
from datetime import date
from bs4 import BeautifulSoup

SCHOLAR_ID = "TxioLDYAAAAJ"
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.json")

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

resp = requests.get(
    f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en",
    headers=headers,
    timeout=30,
)
soup = BeautifulSoup(resp.text, "html.parser")

tbl = soup.find("table", id="gsc_rsb_st")
if not tbl:
    raise Exception("Could not find stats table; Google may have blocked the request.")

cells = tbl.find_all("td", class_="gsc_rsb_sc")
nums = {}
for td in cells:
    label_el = td.find("span", class_="gsc_rsb_a1")
    val_el = td.find("span", class_="gsc_rsb_a2")
    if label_el and val_el:
        nums[label_el.get_text(strip=True)] = int(val_el.get_text(strip=True))

citations = nums.get("Citations", 0)
hindex = nums.get("h-index", 0)
i10index = nums.get("i10-index", 0)

# Since 2021 values are in the second row
rows = tbl.find_all("tr")
if len(rows) >= 3:
    since_cells = rows[2].find_all("td")
    if len(since_cells) >= 3:
        citations_since = int(since_cells[0].get_text(strip=True))
        hindex_since = int(since_cells[1].get_text(strip=True))
        i10index_since = int(since_cells[2].get_text(strip=True))
    else:
        citations_since, hindex_since, i10index_since = citations, hindex, i10index
else:
    citations_since, hindex_since, i10index_since = citations, hindex, i10index

# Parse citation histogram (citations per year)
years = []
hist_div = soup.find("div", class_="gsc_md_hist_b")
if hist_div:
    bars = hist_div.find_all("a", class_=re.compile(r"gsc_g_a"))
    year_spans = hist_div.find_all("span", class_="gsc_g_t")
    for bar, yspan in zip(bars, year_spans):
        year = int(yspan.get_text(strip=True))
        count = int(bar.get_text(strip=True))
        years.append({"y": year, "c": count})
    years.sort(key=lambda x: x["y"])

out = {
    "citations": citations,
    "citations_since": citations_since,
    "hindex": hindex,
    "i10index": i10index,
    "updated": date.today().isoformat(),
    "years": years if years else [
        {"y": y, "c": 0} for y in range(2020, 2027)
    ],
}

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)

print(f"Updated: {json.dumps(out, ensure_ascii=False)}")
