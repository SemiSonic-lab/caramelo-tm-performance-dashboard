from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
EXCEL_FILE = ROOT / "Caramelo TM.xlsx"
HISTORY_FILE = ROOT / "historico_indicadores.csv"

# Indicadores actuales que se conservarán en cada captura.
METRICS = {
    "IGP total": "IGP TOTAL",
    "Carreras completadas": "Carreras Completadas",
    "Puntos de carrera": "Puntos Carrera",
    "Promedio de puntos por carrera": "Promedio Puntos por Carrera",
    "Carreras ganadas": "Carreras Ganadas",
    "Podios": "Podios",
}
HISTORY_COLUMNS = ["snapshot_id", "Fecha captura", "Integrante", "Indicador", "Valor"]


def main():
    if not EXCEL_FILE.exists():
        raise FileNotFoundError(f"No se encontró {EXCEL_FILE.name}")

    data = pd.read_excel(EXCEL_FILE, sheet_name="Caramelo")
    data.columns = [str(column).strip() for column in data.columns]
    if "Integrante" not in data.columns:
        raise ValueError("La hoja Caramelo no contiene la columna Integrante.")

    data = data.dropna(subset=["Integrante"]).copy()
    data["Integrante"] = data["Integrante"].astype(str).str.strip()
    data = data[
        data["Integrante"].ne("")
        & data["Integrante"].str.casefold().ne("nan")
    ]
    data = data.drop_duplicates(subset=["Integrante"], keep="last")

    selected_columns = {}
    for label, prefix in METRICS.items():
        matches = [
            column for column in data.columns
            if column.casefold().startswith(prefix.casefold())
        ]
        if matches:
            selected_columns[label] = matches[0]

    if not selected_columns:
        raise ValueError("No se encontraron indicadores reconocidos para guardar.")

    normalized = []
    rows = []
    for _, player in data.sort_values("Integrante").iterrows():
        for label, column in selected_columns.items():
            value = pd.to_numeric(pd.Series([player[column]]), errors="coerce").iloc[0]
            if pd.notna(value):
                numeric_value = float(value)
                normalized.append({
                    "Integrante": player["Integrante"],
                    "Indicador": label,
                    "Valor": round(numeric_value, 6),
                })
                rows.append({
                    "Integrante": player["Integrante"],
                    "Indicador": label,
                    "Valor": numeric_value,
                })

    if not rows:
        raise ValueError("No hay valores numéricos para registrar en el histórico.")

    canonical = json.dumps(
        normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    snapshot_id = sha256(canonical.encode("utf-8")).hexdigest()

    if HISTORY_FILE.exists():
        existing = pd.read_csv(HISTORY_FILE)
        if "snapshot_id" not in existing.columns:
            raise ValueError("El histórico existente no contiene snapshot_id.")
        if snapshot_id in existing["snapshot_id"].astype(str).values:
            print("Captura omitida: los indicadores no han cambiado desde la última captura.")
            return

    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new_rows = pd.DataFrame([
        {
            "snapshot_id": snapshot_id,
            "Fecha captura": captured_at,
            **row,
        }
        for row in rows
    ], columns=HISTORY_COLUMNS)

    if HISTORY_FILE.exists():
        existing = pd.read_csv(HISTORY_FILE)
        combined = pd.concat([existing[HISTORY_COLUMNS], new_rows], ignore_index=True)
    else:
        combined = new_rows

    combined.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")
    print(
        f"Captura guardada: {captured_at} | "
        f"{data['Integrante'].nunique()} integrantes | "
        f"{len(selected_columns)} indicadores | {len(new_rows)} registros."
    )


if __name__ == "__main__":
    main()
