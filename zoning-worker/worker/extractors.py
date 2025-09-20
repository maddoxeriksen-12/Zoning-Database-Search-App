import tempfile, requests, pandas as pd
import pdfplumber, camelot

def download_pdf(url: str) -> str:
    fp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(fp, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk: f.write(chunk)
    return fp

def extract_tables(pdf_path: str) -> list[pd.DataFrame]:
    dfs: list[pd.DataFrame] = []
    try:
        tables = camelot.read_pdf(pdf_path, flavor="lattice", pages="all")
        dfs += [t.df for t in tables] if tables.n > 0 else []
        if not dfs:
            tables = camelot.read_pdf(pdf_path, flavor="stream", pages="all")
            dfs += [t.df for t in tables] if tables.n > 0 else []
    except Exception:
        pass
    if not dfs:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                for t in page.extract_tables() or []:
                    df = pd.DataFrame(t)
                    if not df.empty: dfs.append(df)
    return dfs
