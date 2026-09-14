"""PDF export for Eye of Abyss case files — reportlab.

Generates a court-ready case PDF with:
  - Case header (ID, status, dates, loss, complainant)
  - Evidence cards per module (verdict, confidence, hash, tx)
  - Convergence report table
  - Blockchain proof block
  - Audit log table
  - Footer with generation timestamp
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Optional


# ── Colours / styles ──────────────────────────────────────────────────────────

_DARK  = (0.06, 0.07, 0.10)    # near-black header bg
_ACCENT= (0.42, 0.26, 0.90)    # violet
_LIGHT = (0.95, 0.96, 0.98)    # light row bg
_RED   = (0.85, 0.15, 0.15)
_GREEN = (0.10, 0.65, 0.35)
_GREY  = (0.40, 0.42, 0.45)


def generate(
    case: dict,
    evidence_list: list[dict],
    audit_log: list[dict],
    freeze_mode: bool = False,
) -> bytes:
    """Return PDF bytes for the case file (or freeze-request variant)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"Eye of Abyss — {'Freeze Request' if freeze_mode else 'Case File'}",
        author="Eye of Abyss Platform",
    )

    styles   = getSampleStyleSheet()
    h1_style = ParagraphStyle("H1", parent=styles["Heading1"], textColor=colors.Color(*_DARK),   fontSize=16, spaceAfter=4)
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.Color(*_ACCENT),  fontSize=11, spaceBefore=8, spaceAfter=3)
    body     = ParagraphStyle("Body", parent=styles["Normal"],  fontSize=8.5, leading=12)
    mono     = ParagraphStyle("Mono", parent=styles["Normal"],  fontName="Courier", fontSize=7.5, leading=10)
    caption  = ParagraphStyle("Cap",  parent=styles["Normal"],  fontSize=7, textColor=colors.Color(*_GREY))

    W = A4[0] - 36 * mm   # usable width

    story = []

    # ── Cover / header ────────────────────────────────────────────────────────
    doc_type = "FREEZE REQUEST DRAFT" if freeze_mode else "CASE FILE"
    story.append(Paragraph(f"EYE OF ABYSS — {doc_type}", h1_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.Color(*_ACCENT)))
    story.append(Spacer(1, 4 * mm))

    case_id   = case.get("case_id", "—")
    status    = case.get("status", "—")
    loss      = case.get("reported_loss") or "—"
    c_type    = case.get("complainant_type") or "—"
    created   = case.get("created_at") or "—"
    updated   = case.get("updated_at") or "—"
    anchors   = case.get("anchor_tx_hashes") or []
    conv      = case.get("convergence") or {}

    header_data = [
        ["Case ID",         str(case_id)],
        ["Status",          status],
        ["Complainant",     c_type],
        ["Reported Loss",   loss],
        ["Created",         str(created)[:19]],
        ["Last Updated",    str(updated)[:19]],
    ]
    if freeze_mode:
        header_data.append(["Request Type", "Asset Freeze / Account Hold"])

    header_table = Table(header_data, colWidths=[45 * mm, W - 45 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.Color(*_LIGHT)),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8.5),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.Color(0.8, 0.8, 0.8)),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.Color(*_LIGHT)]),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6 * mm))

    # ── Evidence cards ────────────────────────────────────────────────────────
    if evidence_list:
        story.append(Paragraph("EVIDENCE SUMMARY", h2_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.Color(*_GREY)))
        story.append(Spacer(1, 2 * mm))

        for ev in evidence_list:
            module   = (ev.get("module_id") or "unknown").upper()
            verdict  = ev.get("verdict") or "—"
            conf     = ev.get("confidence", 0.0)
            tier     = ev.get("confidence_tier") or "—"
            ev_hash  = ev.get("hash_sha256") or "—"
            anchor   = ev.get("chain_anchor") or "not anchored"
            ipfs     = ev.get("ipfs_cid") or "—"

            conf_color = colors.Color(*_GREEN) if conf >= 0.75 else (
                colors.orange if conf >= 0.45 else colors.Color(*_RED)
            )

            ev_data = [
                [Paragraph(f"<b>{module}</b>", body), Paragraph(verdict, body)],
                ["Confidence",       f"{conf:.1%}  [{tier.upper()}]"],
                ["SHA-256",          Paragraph(ev_hash, mono)],
                ["Chain Anchor",     Paragraph(anchor, mono)],
                ["IPFS CID",         Paragraph(ipfs, mono)],
            ]
            ev_table = Table(ev_data, colWidths=[38 * mm, W - 38 * mm])
            ev_table.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, 0), colors.Color(*_DARK)),
                ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
                ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",     (0, 0), (-1, -1), 8),
                ("GRID",         (0, 0), (-1, -1), 0.3, colors.Color(0.85, 0.85, 0.85)),
                ("ROWBACKGROUNDS", (1, 0), (-1, -1), [colors.white, colors.Color(*_LIGHT)]),
                ("LEFTPADDING",  (0, 0), (-1, -1), 5),
                ("SPAN",         (0, 0), (0, 0)),
            ]))
            story.append(ev_table)
            story.append(Spacer(1, 3 * mm))

    # ── Convergence report ────────────────────────────────────────────────────
    if conv:
        story.append(Paragraph("CROSS-MODULE CONVERGENCE REPORT", h2_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.Color(*_GREY)))
        story.append(Spacer(1, 2 * mm))

        def _pct(v) -> str:
            return f"{float(v):.1%}" if v is not None else "—"

        conv_data = [
            ["Signal",               "Score"],
            ["Timezone Match",       _pct(conv.get("timezone_match"))],
            ["Activity Overlap",     _pct(conv.get("activity_overlap"))],
            ["Actor Graph Link",     conv.get("actor_graph_link") or "None"],
            ["Convergence Confidence", _pct(conv.get("convergence_confidence"))],
        ]
        conv_table = Table(conv_data, colWidths=[80 * mm, W - 80 * mm])
        conv_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), colors.Color(*_ACCENT)),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 8.5),
            ("GRID",         (0, 0), (-1, -1), 0.3, colors.Color(0.85, 0.85, 0.85)),
            ("ROWBACKGROUNDS", (1, 0), (-1, -1), [colors.white, colors.Color(*_LIGHT)]),
            ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ]))
        story.append(conv_table)
        story.append(Spacer(1, 4 * mm))

    # ── Blockchain proof ──────────────────────────────────────────────────────
    if anchors:
        story.append(Paragraph("BLOCKCHAIN ANCHORING PROOFS", h2_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.Color(*_GREY)))
        story.append(Spacer(1, 2 * mm))
        for tx in anchors:
            story.append(Paragraph(f"• {tx}", mono))
        story.append(Spacer(1, 4 * mm))

    # ── Audit log ─────────────────────────────────────────────────────────────
    if audit_log:
        story.append(Paragraph("AUDIT LOG", h2_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.Color(*_GREY)))
        story.append(Spacer(1, 2 * mm))

        audit_data = [["Timestamp", "Actor", "Action"]]
        for entry in audit_log:
            audit_data.append([
                str(entry.get("ts") or entry.get("timestamp") or "")[:19],
                str(entry.get("actor") or "—")[:40],
                str(entry.get("action") or "—"),
            ])
        col_w = [45 * mm, 55 * mm, W - 100 * mm]
        audit_table = Table(audit_data, colWidths=col_w)
        audit_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), colors.Color(*_DARK)),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 7.5),
            ("GRID",         (0, 0), (-1, -1), 0.3, colors.Color(0.85, 0.85, 0.85)),
            ("ROWBACKGROUNDS", (1, 0), (-1, -1), [colors.white, colors.Color(*_LIGHT)]),
            ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ]))
        story.append(audit_table)
        story.append(Spacer(1, 4 * mm))

    # ── Footer ────────────────────────────────────────────────────────────────
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.Color(*_GREY)))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f"Generated by Eye of Abyss Platform · {now} · Court-admissible chain of custody",
        caption,
    ))
    if freeze_mode:
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            "DRAFT — Pending supervisor signature. This document constitutes a formal request "
            "to financial institutions to freeze assets linked to the above case.",
            ParagraphStyle("warn", parent=body, textColor=colors.Color(*_RED)),
        ))

    doc.build(story)
    return buf.getvalue()


def generate_freeze_json(case: dict, evidence_list: list[dict]) -> dict:
    """Structured JSON freeze-request draft."""
    wallets = []
    accounts = []
    for ev in evidence_list:
        p = ev.get("payload") or {}
        if w := p.get("wallet_address") or p.get("top_wallet"):
            wallets.append(w)
        if a := p.get("bank_account"):
            accounts.append(a)

    return {
        "request_type":    "ASSET_FREEZE",
        "case_id":         case.get("case_id"),
        "status":          case.get("status"),
        "reported_loss":   case.get("reported_loss"),
        "complainant":     case.get("complainant_type"),
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "assets_to_freeze": {
            "crypto_wallets":   list(set(wallets)),
            "bank_accounts":    list(set(accounts)),
        },
        "blockchain_proofs": case.get("anchor_tx_hashes") or [],
        "convergence_score": (case.get("convergence") or {}).get("convergence_confidence"),
        "note": "DRAFT — Requires supervisor countersignature before submission to court.",
    }
