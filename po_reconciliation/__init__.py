"""
po_reconciliation
=================
Module for transforming the SAP PO history dataset (documents2) into a
one-row-per-transaction aggregated view with GR/IR reconciliation status.

Entry point: build_final_dataset.py
Output dataset: final_documents2_aggregated
"""

from .build_final_dataset import build_final_dataset, load_documents2

__all__ = ["build_final_dataset", "load_documents2"]
