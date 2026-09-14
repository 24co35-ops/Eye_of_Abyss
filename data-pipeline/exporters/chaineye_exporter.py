"""ChainEye training data and complaints exporter."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List


def export_chaineye_data(
    transactions: List[Dict[str, any]],
    complaints: List[Dict[str, any]],
    output_dir: str = "./output",
) -> tuple[Path, Path]:
    """
    Exports:
      - output/chaineye/transactions.csv
      - output/chaineye/complaints.csv
    """
    chaineye_dir = Path(output_dir) / "chaineye"
    chaineye_dir.mkdir(parents=True, exist_ok=True)

    tx_path = chaineye_dir / "transactions.csv"
    tx_fields = [
        "tx_hash",
        "from_address",
        "to_address",
        "amount",
        "amount_usd",
        "token",
        "timestamp",
        "chain",
        "actor_id",
        "vasp_attribution",
        "is_mixer",
        "data_source",
    ]

    with open(tx_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=tx_fields)
        writer.writeheader()
        for tx in transactions:
            row = {k: tx.get(k, "") for k in tx_fields}
            row["data_source"] = "synthetic"
            writer.writerow(row)

    complaints_path = chaineye_dir / "complaints.csv"
    complaints_fields = [
        "complaint_id",
        "case_id",
        "actor_id",
        "complainant_category",
        "reported_loss_inr",
        "reported_loss_usd",
        "suspect_wallet",
        "tx_hash",
        "timestamp",
        "data_source",
    ]

    with open(complaints_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=complaints_fields)
        writer.writeheader()
        for comp in complaints:
            row = {k: comp.get(k, "") for k in complaints_fields}
            row["data_source"] = "synthetic"
            writer.writerow(row)

    return tx_path, complaints_path
