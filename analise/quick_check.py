import os
import re
import sys
import math
import pandas as pd
from typing import List

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, 'dados', 'processed')


def _norm(s: str) -> str:
    try:
        s = str(s).lower()
    except Exception:
        return ''
    table = str.maketrans(
        'áàãâäéêëèíïîìóõôöòúüûùç',
        'aaaaaeeeeiiiiooooouuuuc'
    )
    return s.translate(table)


def _best_date_columns(df: pd.DataFrame) -> List[str]:
    norm_cols = {col: _norm(col) for col in df.columns}
    date_cols = [c for c, n in norm_cols.items() if any(k in n for k in ['data', 'dt', 'ano', 'mes', 'mês', 'periodo', 'ano_mes', 'ano/mes'])]
    return date_cols


def _derive_year_month(df: pd.DataFrame) -> pd.DataFrame:
    date_cols = _best_date_columns(df)

    year = None
    month = None

    # 1) Ano explícito
    for col in date_cols:
        if 'ano' in _norm(col):
            try:
                cand = pd.to_numeric(df[col], errors='coerce')
                if cand.notna().sum() > 0:
                    year = cand
                    break
            except Exception:
                pass

    # 2) Mês explícito
    for col in date_cols:
        if any(k in _norm(col) for k in ['mes', 'mês']):
            try:
                cand = pd.to_numeric(df[col], errors='coerce')
                cand = cand.where((cand >= 1) & (cand <= 12))
                if cand.notna().sum() > 0:
                    month = cand
                    break
            except Exception:
                pass

    # 3) Datas completas
    if year is None or month is None:
        best_dt = None
        best_count = -1
        for col in date_cols:
            try:
                dt = pd.to_datetime(df[col], errors='coerce', dayfirst=True, infer_datetime_format=True)
                cnt = dt.notna().sum()
                if cnt > best_count:
                    best_dt = dt
                    best_count = cnt
            except Exception:
                continue
        if best_dt is not None:
            if year is None:
                year = best_dt.dt.year
            if month is None:
                month = best_dt.dt.month

    df = df.copy()
    if year is not None:
        df['__year'] = year
    if month is not None:
        df['__month'] = month
    if '__year' in df.columns and '__month' in df.columns:
        try:
            df['__year_month'] = df['__year'].astype('Int64').astype(str).str.zfill(4) + '-' + df['__month'].astype('Int64').astype(str).str.zfill(2)
        except Exception:
            df['__year_month'] = None
    return df


def _build_qty(df: pd.DataFrame) -> pd.Series:
    norm_cols = {col: _norm(col) for col in df.columns}
    qty_patterns = ['qtd_container', 'qtd cont', 'qtde', 'qtd', 'quantidade', 'containers', 'teus', 'qtde_total', 'qtd total', 'volumes', 'qtde conteiner']
    qty_cols = [c for c, n in norm_cols.items() if any(p in n for p in qty_patterns)]
    if not qty_cols:
        return pd.Series([math.nan] * len(df))
    try:
        qdf = df[qty_cols].apply(pd.to_numeric, errors='coerce')
        return qdf.bfill(axis=1).iloc[:, 0]
    except Exception:
        return pd.Series([math.nan] * len(df))


def _is_import_mask(df: pd.DataFrame) -> pd.Series:
    norm_cols = {col: _norm(col) for col in df.columns}
    ie_cols = [c for c, n in norm_cols.items() if any(k in n for k in ['i/e', 'ie', 'operacao', 'opera', 'tipo', 'natureza'])]
    if not ie_cols:
        return pd.Series([False] * len(df))
    mask = None
    for col in ie_cols:
        try:
            s = df[col].astype(str).apply(_norm)
            m = s.str.contains('^i$', na=False) | s.str.contains('import', na=False)
            mask = m if mask is None else (mask | m)
        except Exception:
            continue
    return mask if mask is not None else pd.Series([False] * len(df))


def load_processed() -> pd.DataFrame:
    files = []
    if not os.path.isdir(PROCESSED_DIR):
        return pd.DataFrame()
    for name in os.listdir(PROCESSED_DIR):
        if name.lower().endswith(('.xlsx', '.xls', '.csv')):
            files.append(os.path.join(PROCESSED_DIR, name))
    dfs = []
    for fp in files:
        try:
            if fp.lower().endswith('.csv'):
                df = pd.read_csv(fp)
            else:
                df = pd.read_excel(fp)
            if df is not None and not df.empty:
                df = df.copy()
                df['arquivo_origem'] = os.path.basename(fp)
                dfs.append(df)
        except Exception as e:
            print(f"[WARN] Falha ao ler {fp}: {e}")
    if not dfs:
        return pd.DataFrame()
    combined = pd.concat(dfs, ignore_index=True, sort=False)
    return combined


def main():
    df = load_processed()
    if df.empty:
        print('Sem dados em dados/processed/.')
        sys.exit(0)

    # Derivar colunas auxiliares
    df['__qty'] = _build_qty(df)
    df = _derive_year_month(df)

    # Coluna de cliente/consignatário
    norm_cols = {col: _norm(col) for col in df.columns}
    client_cols = [c for c, n in norm_cols.items() if any(k in n for k in ['cliente', 'consignat', 'importador', 'exportador'])]
    client_col = client_cols[0] if client_cols else None

    # 1) ACCUMED 2024
    if client_col is not None and '__year' in df.columns:
        accumed_mask = df[client_col].astype(str).str.contains('ACCUMED', case=False, na=False)
        y2024_mask = df['__year'] == 2024
        df_acc_2024 = df[accumed_mask & y2024_mask]
        total_acc_2024 = pd.to_numeric(df_acc_2024['__qty'], errors='coerce').sum()
        print(f"ACCUMED 2024 - Total containers (soma __qty): {int(total_acc_2024) if not math.isnan(total_acc_2024) else 0}")
        if not df_acc_2024.empty:
            by_file = df_acc_2024.groupby('arquivo_origem')['__qty'].sum().sort_values(ascending=False)
            print('ACCUMED 2024 - Por arquivo:')
            for f, v in by_file.items():
                print(f"  - {f}: {int(v) if not math.isnan(v) else 0}")
    else:
        print('ACCUMED 2024 - Não foi possível detectar coluna de cliente/ano.')

    # 2) Importações em Março/2025 (todos os portos)
    is_import = _is_import_mask(df)
    if '__year' in df.columns and '__month' in df.columns and is_import is not None:
        mar_2025 = (df['__year'] == 2025) & (df['__month'] == 3)
        df_imp_mar_2025 = df[mar_2025 & is_import]
        total_imp_mar_2025 = pd.to_numeric(df_imp_mar_2025['__qty'], errors='coerce').sum()
        print(f"Importações 03/2025 - Total containers (soma __qty): {int(total_imp_mar_2025) if not math.isnan(total_imp_mar_2025) else 0}")
        if not df_imp_mar_2025.empty:
            by_file2 = df_imp_mar_2025.groupby('arquivo_origem')['__qty'].sum().sort_values(ascending=False)
            print('Importações 03/2025 - Por arquivo:')
            for f, v in by_file2.items():
                print(f"  - {f}: {int(v) if not math.isnan(v) else 0}")
    else:
        print('Importações 03/2025 - Não foi possível detectar ano/mês ou coluna I/E.')


if __name__ == '__main__':
    main()
