"""
build_final_dataset.py
======================
Transforms the SAP PO history dataset (documents2 / Contracts.csv) from a
multi-row-per-transaction layout into a single-row-per-transaction aggregated
dataset named `final_documents2_aggregated`.

Each transaction is identified by the composite key:
    (purchasing_document_|_ebeln, item_|_ebelp)

Steps performed
---------------
1. Load `documents2` (Contracts.csv) — handles UTF-8 BOM transparently.
2. Classify each row as a Goods Receipt (GR) or Invoice Receipt (IR).
3. Apply the debit/credit sign to quantity and amount.
4. Aggregate original columns with semantically appropriate functions.
5. Compute GR/IR totals.
6. Compute boolean flags: has_gr, has_ir, has_delivery.
7. Compute reconciliation status (overridden to 'DELIVERED' when has_delivery=1).
8. Rename columns to business-friendly names (RENAME_MAP).
9. Save the result as `final_documents2_aggregated.xlsx` (or .csv).

Usage (standalone)
------------------
    python -m po_reconciliation.build_final_dataset
    # or
    python po_reconciliation/build_final_dataset.py

Usage (as a library)
--------------------
    from po_reconciliation.build_final_dataset import build_final_dataset
    df = build_final_dataset(input_file="...", output_file="...")
"""

import logging
import re
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column name constants  (match the actual Documents1.csv header exactly)
# ---------------------------------------------------------------------------
COL_EBELN = "purchasing_document_|_ebeln"
COL_EBELP = "item_|_ebelp"
COL_BEWTP = "po_history_category_|_bewtp"
COL_MENGE = "quantity_|_menge"
COL_DMBTR = "amtin_loccur_|_dmbtr"   # local-currency amount — only column used for $
COL_SHKZG = "debitcredit_ind_|_shkzg"  # S = debit (+), H = credit (−)
COL_ELIKZ_EKPO = "delivery_completed_|_elikz_ekpo"  # 'X' = delivery completed (item)

GROUP_KEYS = [COL_EBELN, COL_EBELP]

# ---------------------------------------------------------------------------
# Business constants
# ---------------------------------------------------------------------------
GR_CATEGORY = "Q"             # po_history_category value that flags a Goods Receipt
IR_CATEGORIES = ["E", "K", "N"]  # values that flag an Invoice Receipt

# ---------------------------------------------------------------------------
# Column-level aggregation rules for ALL 59 original columns
#
# Rationale per bucket:
#   • 'first'  — field is static for a given PO item (master / header data)
#   • 'sum'    — field is additive across movement rows (financial flows)
#   • 'max'    — field is a date or flag where the latest / highest matters
#   • 'last'   — movement-level field; take the most recent row seen
# ---------------------------------------------------------------------------
ORIG_COLUMN_AGG: dict = {
    # ── Header / master data (one value per PO item) ──────────────────────
    "source":                                          "first",
    "plant_|_werks":                                   "first",
    "supplier_|_lifnr":                                "first",
    "purchasing_doc_type_|_bsart":                     "first",
    "purch_organization_|_ekorg":                      "first",
    "purchasing_group_|_ekgrp":                        "first",
    "document_date_|_bedat":                           "first",  # PO creation date
    "material_|_matnr":                                "first",
    "material_group_|_matkl":                          "first",
    "short_text_|_txz01":                              "first",
    "order_unit_|_meins":                              "first",
    "order_price_unit_|_bprme":                        "first",
    "price_unit_|_peinh":                              "first",
    "net_order_price_|_netpr":                         "first",
    "currency_|_waers":                                "first",
    "outline_agreement_|_konnr":                       "first",
    "terms_of_payment_|_zterm":                        "first",
    "tax_code_|_mwskz":                                "first",
    "incoterms_|_inco1":                               "first",
    "incoterms_part_2_|_inco2":                        "first",
    "planned_deliv_time_|_plifz":                      "first",
    "gr_processing_time_|_webaz":                      "first",
    "item_category_|_pstyp":                           "first",
    "created_by_|_ernam":                              "first",
    "vendor_material_no_|_idnlf":                      "first",
    "purchasing_info_rec_|_infnr":                     "first",
    "storage_location":                                "first",
    "batch_|_charg":                                   "first",
    "valuation_type_|_bwtar":                          "first",
    "reason_for_movement_|_grund":                     "first",
    # ── Physical attributes (static per PO item) ──────────────────────────
    "net_weight_|_ntgew":                              "first",
    "gross_weight_|_brgew":                            "first",
    "unit_of_weight_|_gewei":                          "first",
    "volume_|_volum":                                  "first",
    # ── Financial flows (additive across GR / IR rows) ────────────────────
    "quantity_|_menge":                                "sum",  # raw (unsigned) qty total
    "amount_|_wrbtr":                                  "sum",  # foreign-currency amount
    "amtin_loccur_|_dmbtr":                            "sum",  # local-currency amount
    "grir_clearing_value_in_local_currency_|_arewr":   "sum",
    "invoice_value_|_reewr":                           "sum",
    # ── Movement-level fields (take the last movement seen) ───────────────
    "movement_type_|_bwart":                           "last",
    "po_history_category_|_bewtp":                     "last",
    "debitcredit_ind_|_shkzg":                         "last",
    "reference_document_|_lfbnr":                      "last",
    "reference_doc_item_|_lfpos":                      "last",
    # ── Operational / status flags (take the most advanced state) ─────────
    "deletion_indicator_|_loekz":                      "max",
    "delivery_completed_|_elikz_ekpo":                 "max",
    # ── Dates: latest posting / change date is the most meaningful ─────────
    "posting_date_|_budat":                            "max",
    "document_date_|_bldat":                           "max",
    "last_changed_on_|_aedat":                         "max",
    "entry_date_|_cpudt":                              "max",
    "time_of_entry_|_cputm":                           "max",
    "ekko_data_ingestion_freshness_timestamp_utc":     "max",
    "ekpo_data_ingestion_freshness_timestamp_utc":     "max",
    # ── Supplier enrichment columns (same per supplier) ───────────────────
    "supplier_id":                                     "first",
    "supplier_name":                                   "first",
    "city":                                            "first",
    "region":                                          "first",
}

# ---------------------------------------------------------------------------
# Final column renaming (business-friendly names for the output dataset)
#
# Mirrors a Power Query Table.RenameColumns step with MissingField.Ignore:
# any key not present in the dataframe is silently skipped (pandas .rename
# already behaves this way for unmatched keys).
# ---------------------------------------------------------------------------
RENAME_MAP: dict = {
    "purchasing_document_|_ebeln":     "Purchasing Document",
    "item_|_ebelp":                    "Item",
    "supplier_|_lifnr":                "Supplier",
    "purchasing_doc_type_|_bsart":     "Document Type",
    "document_date_|_bedat":           "Document Date",
    "created_by_|_ernam":              "Created By",
    "material_|_matnr":                "Material",
    "material_group_|_matkl":          "Material Group",
    "short_text_|_txz01":              "Description",
    "movement_type_|_bwart":           "Movement Type",
    "delivery_completed_|_elikz":      "Delivery Completed (Header)",
    "delivery_completed_|_elikz_ekpo": "Delivery Completed (Item)",
    "net_order_price_|_netpr":         "Net Order Price",
    "quantity_|_menge":                "Quantity",
    "amount_|_wrbtr":                  "Amount",
    "currency_|_waers":                "Currency",
    "plant_|_werks":                   "Plant",
    "purch_organization_|_ekorg":      "Purch Organization",
    "purchasing_group_|_ekgrp":        "Purchasing Group",
}


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Apply RENAME_MAP; columns not present in df are ignored (no error)."""
    return df.rename(columns=RENAME_MAP)


# ===========================================================================
# Step 1 – Load
# ===========================================================================

def load_documents2(file_path: str | Path) -> pd.DataFrame:
    """
    Load the raw SAP PO history file.

    Uses utf-8-sig encoding so the BOM on the first column name
    (﻿ purchasing_document_|_ebeln) is stripped automatically.
    """
    file_path = Path(file_path)
    logger.info("Loading documents2 from: %s", file_path)
    df = pd.read_csv(file_path, encoding="utf-8-sig", low_memory=False)
    # Defensive BOM strip in case the encoding flag alone is not enough
    df.columns = [c.lstrip("﻿").strip() for c in df.columns]
    logger.info("  → Loaded %d rows × %d columns", *df.shape)
    return df


# ===========================================================================
# Step 2 – Classify GR / IR
# ===========================================================================

def classify_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add `transaction_type` column:
        'GR'    when po_history_category_|_bewtp = 'Q'
        'IR'    when po_history_category_|_bewtp ∈ {E, K, N}
        'OTHER' for anything else (kept for traceability, excluded from metrics)
    """
    conditions = [
        df[COL_BEWTP] == GR_CATEGORY,
        df[COL_BEWTP].isin(IR_CATEGORIES),
    ]
    df["transaction_type"] = np.select(conditions, ["GR", "IR"], default="OTHER")
    return df


# ===========================================================================
# Step 3 – Sign adjustment
# ===========================================================================

def apply_debitcredit_sign(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the debit/credit sign to quantity and amount:
        S (Soll / debit)  →  +1
        H (Haben / credit) → −1

    Creates two new columns:
        signed_quantity  =  quantity_|_menge  × sign
        signed_amount    =  amtin_loccur_|_dmbtr × sign
    """
    sign = np.where(df[COL_SHKZG] == "S", 1, -1)
    df["signed_quantity"] = df[COL_MENGE] * sign
    df["signed_amount"]   = df[COL_DMBTR] * sign
    return df


# ===========================================================================
# Step 4 – Aggregate original columns (one row per transaction)
# ===========================================================================

def aggregate_original_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group by (ebeln, ebelp) and reduce every original column to a single value
    using the rules defined in ORIG_COLUMN_AGG.

    Any column that is in the dataset but not in ORIG_COLUMN_AGG is aggregated
    with 'first' as a safe fallback, so new columns added upstream are never lost.
    """
    # Build the final agg dict — only for columns actually present in the frame
    available = set(df.columns) - set(GROUP_KEYS) - {
        "transaction_type", "signed_quantity", "signed_amount"
    }
    agg_dict = {}
    for col in available:
        agg_dict[col] = ORIG_COLUMN_AGG.get(col, "first")  # fallback: first

    logger.info("  → Aggregating %d original columns", len(agg_dict))
    return df.groupby(GROUP_KEYS, sort=False).agg(agg_dict).reset_index()


# ===========================================================================
# Step 5 – GR / IR totals
# ===========================================================================

def compute_gr_ir_totals(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute per-transaction GR and IR totals from the signed values.

    Returns two DataFrames (indexed by GROUP_KEYS):
        gr_totals  — total_gr_qty, total_gr_amt
        ir_totals  — total_ir_qty, total_ir_amt
    """
    gr = (
        df[df["transaction_type"] == "GR"]
        .groupby(GROUP_KEYS, sort=False)
        .agg(
            total_gr_qty=("signed_quantity", "sum"),
            total_gr_amt=("signed_amount",   "sum"),
        )
        .reset_index()
    )
    ir = (
        df[df["transaction_type"] == "IR"]
        .groupby(GROUP_KEYS, sort=False)
        .agg(
            total_ir_qty=("signed_quantity", "sum"),
            total_ir_amt=("signed_amount",   "sum"),
        )
        .reset_index()
    )
    return gr, ir


# ===========================================================================
# Step 6 – Flags
# ===========================================================================

def compute_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    has_gr = 1  if total_gr_qty ≠ 0
    has_ir = 1  if total_ir_qty ≠ 0
    has_delivery = 1  if delivery_completed_|_elikz_ekpo == 'X'
    """
    df["has_gr"] = (df["total_gr_qty"] != 0).astype(int)
    df["has_ir"] = (df["total_ir_qty"] != 0).astype(int)
    df["has_delivery"] = (df[COL_ELIKZ_EKPO] == "X").astype(int)
    return df


# ===========================================================================
# Step 7 – Reconciliation status
# ===========================================================================

def _row_status(row: pd.Series) -> str:
    """Determine the reconciliation status for a single transaction row."""
    has_gr, has_ir = row["has_gr"], row["has_ir"]

    if has_gr == 1 and has_ir == 0:
        return "ONLY_GR"
    if has_gr == 0 and has_ir == 1:
        return "ONLY_IR"
    if has_gr == 0 and has_ir == 0:
        return "NO_GR_NO_IR"

    qty_match = row["total_gr_qty"] == row["total_ir_qty"]
    amt_match = row["total_gr_amt"] == row["total_ir_amt"]

    if qty_match and amt_match:
        return "MATCH"
    if not qty_match and amt_match:
        return "QTY_MISMATCH"
    if qty_match and not amt_match:
        return "AMOUNT_MISMATCH"
    return "QTY_AND_AMOUNT_MISMATCH"


def compute_status(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the base GR/IR reconciliation status, then override it with
    'DELIVERED' for transactions where has_delivery == 1
    (delivery_completed_|_elikz_ekpo == 'X').
    """
    df["status"] = df.apply(_row_status, axis=1)
    df.loc[df["has_delivery"] == 1, "status"] = "DELIVERED"
    return df


# ===========================================================================
# Orchestrator
# ===========================================================================

def build_final_dataset(
    input_file: str | Path,
    output_file: str | Path,
) -> pd.DataFrame:
    """
    Full pipeline: load → classify → sign → aggregate → flags → status → save.

    Parameters
    ----------
    input_file  : Path to the raw SAP PO history CSV (documents2 / Documents1.csv).
    output_file : Destination path for final_documents2_aggregated.csv.

    Returns
    -------
    pd.DataFrame  The aggregated dataset (also written to output_file).
    """
    input_file  = Path(input_file)
    output_file = Path(output_file)

    # ── 1. Load ─────────────────────────────────────────────────────────────
    documents2 = load_documents2(input_file)

    # ── 2. Classify GR / IR ─────────────────────────────────────────────────
    logger.info("Step 2 – Classifying transaction types (GR / IR) …")
    documents2 = classify_transactions(documents2)
    logger.info(
        "  → %s",
        documents2["transaction_type"].value_counts().to_dict(),
    )

    # ── 3. Apply debit/credit sign ───────────────────────────────────────────
    logger.info("Step 3 – Applying debit/credit sign …")
    documents2 = apply_debitcredit_sign(documents2)

    # ── 4. Aggregate original columns ────────────────────────────────────────
    logger.info("Step 4 – Aggregating original columns (one row per transaction) …")
    base = aggregate_original_columns(documents2)
    logger.info("  → Base shape after aggregation: %d rows × %d cols", *base.shape)

    # ── 5. GR / IR totals ────────────────────────────────────────────────────
    logger.info("Step 5 – Computing GR / IR totals …")
    gr_totals, ir_totals = compute_gr_ir_totals(documents2)
    logger.info("  → %d transactions with GR activity", len(gr_totals))
    logger.info("  → %d transactions with IR activity", len(ir_totals))

    # Merge totals; fill 0 where a transaction has no GR or no IR
    result = base.merge(gr_totals, on=GROUP_KEYS, how="left")
    result = result.merge(ir_totals, on=GROUP_KEYS, how="left")
    for col in ("total_gr_qty", "total_gr_amt", "total_ir_qty", "total_ir_amt"):
        result[col] = result[col].fillna(0)

    # ── 6. Flags ─────────────────────────────────────────────────────────────
    logger.info("Step 6 – Computing has_gr / has_ir / has_delivery flags …")
    result = compute_flags(result)
    logger.info("  → %d transactions with delivery completed", result["has_delivery"].sum())

    # ── 7. Reconciliation status ─────────────────────────────────────────────
    logger.info("Step 7 – Computing reconciliation status …")
    result = compute_status(result)
    logger.info(
        "  → Status distribution:\n%s",
        result["status"].value_counts().to_string(),
    )

    # ── 8. Rename columns to business-friendly names ────────────────────────
    logger.info("Step 8 – Renaming columns …")
    result = rename_columns(result)

    # ── 9. Save ──────────────────────────────────────────────────────────────
    output_file.parent.mkdir(parents=True, exist_ok=True)
    save_dataset(result, output_file)
    logger.info(
        "Saved final_documents2_aggregated → %s  (%d rows × %d cols)",
        output_file,
        *result.shape,
    )

    return result


def save_dataset(df: pd.DataFrame, output_file: Path) -> None:
    """
    Save the result to disk. The output format is inferred from the file
    extension:
        .csv          → CSV (utf-8-sig, Excel-friendly)
        .xlsx / .xls  → Excel workbook (sheet name: final_documents2_aggregated)

    For .xlsx, prefers openpyxl/xlsxwriter if installed, otherwise falls back
    to a dependency-free OOXML writer (write_xlsx) so the script works even
    without internet access to install extra packages.
    """
    suffix = output_file.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        for engine in ("openpyxl", "xlsxwriter"):
            try:
                df.to_excel(
                    output_file,
                    index=False,
                    sheet_name="final_documents2_aggregated",
                    engine=engine,
                )
                return
            except ImportError:
                continue
        logger.info("  → openpyxl/xlsxwriter not available, using built-in XLSX writer")
        write_xlsx(df, output_file, sheet_name="final_documents2_aggregated")
    else:
        df.to_csv(output_file, index=False, encoding="utf-8-sig")


# ---------------------------------------------------------------------------
# Dependency-free XLSX writer (OOXML / SpreadsheetML, stdlib zipfile + xml only)
# ---------------------------------------------------------------------------

_INVALID_XML_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")

_CONTENT_TYPES_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    "</Types>"
)

_ROOT_RELS_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
    "</Relationships>"
)

_WORKBOOK_RELS_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
    "</Relationships>"
)


def _col_letter(idx: int) -> str:
    """0-based column index → Excel column letter (0→A, 25→Z, 26→AA, ...)."""
    letters = ""
    idx += 1
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _xml_text(value) -> str:
    """Escape a value for use inside an XML text node, stripping invalid chars."""
    return _INVALID_XML_CHARS.sub("", escape(str(value)))


def write_xlsx(df: pd.DataFrame, output_path: str | Path, sheet_name: str = "Sheet1") -> None:
    """
    Write a DataFrame to a single-sheet .xlsx file using only the standard
    library (zipfile + minimal SpreadsheetML XML). Numbers are written as
    numeric cells; everything else (incl. dates already stored as strings)
    is written as inline strings.
    """
    output_path = Path(output_path)
    n_rows, n_cols = df.shape
    col_letters = [_col_letter(i) for i in range(n_cols)]

    rows_xml = []

    # Header row
    header_cells = "".join(
        f'<c r="{col_letters[ci]}1" t="inlineStr"><is><t>{_xml_text(col)}</t></is></c>'
        for ci, col in enumerate(df.columns)
    )
    rows_xml.append(f'<row r="1">{header_cells}</row>')

    # Data rows
    for ri, row in enumerate(df.itertuples(index=False, name=None), start=2):
        cells = []
        for ci, val in enumerate(row):
            if pd.isna(val):
                continue
            ref = f"{col_letters[ci]}{ri}"
            if isinstance(val, (int, np.integer, float, np.floating)) and not isinstance(val, bool):
                cells.append(f'<c r="{ref}" t="n"><v>{val}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{_xml_text(val)}</t></is></c>')
        rows_xml.append(f'<row r="{ri}">{"".join(cells)}</row>')

    dimension = f"A1:{col_letters[-1]}{n_rows + 1}"
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="{dimension}"/>'
        f'<sheetData>{"".join(rows_xml)}</sheetData>'
        "</worksheet>"
    )

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{_xml_text(sheet_name)}" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES_XML)
        zf.writestr("_rels/.rels", _ROOT_RELS_XML)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", _WORKBOOK_RELS_XML)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Paths resolved relative to this file so the script is location-agnostic
    _MODULE_DIR   = Path(__file__).parent
    _PROJECT_ROOT = _MODULE_DIR.parent

    INPUT_FILE  = _PROJECT_ROOT / "Contracts.csv"
    OUTPUT_FILE = _MODULE_DIR / "outputs" / "final_documents2_aggregated.xlsx"

    final_df = build_final_dataset(
        input_file=INPUT_FILE,
        output_file=OUTPUT_FILE,
    )

    print("\n" + "=" * 60)
    print("final_documents2_aggregated — summary")
    print("=" * 60)
    print(f"  Rows    : {len(final_df):,}")
    print(f"  Columns : {final_df.shape[1]}")
    print(f"\n  Status distribution:")
    print(final_df["status"].value_counts().to_string(index=True))
    print(f"\n  has_gr  :  {final_df['has_gr'].sum():,}  transactions")
    print(f"  has_ir  :  {final_df['has_ir'].sum():,}  transactions")
    print("=" * 60)
