"""
SAP PO History — Dataset enrichi avec statuts métier
=====================================================
Granularité finale : 1 ligne par (purchasing_document, item)
Colonnes ajoutées :
  - gr_quantity_received     : quantité totale livrée (GR nets)
  - invoice_amount_total     : montant total facturé
  - has_gr                   : flag 0/1 — au moins 1 livraison
  - has_invoice              : flag 0/1 — au moins 1 facture
  - delivery_status          : Not Delivered / Partially Delivered / Fully Delivered
  - invoice_status           : Not Invoiced / Partially Invoiced / Fully Invoiced
  - order_status             : Active / Closed
"""

from pyspark.sql import functions as F
from pyspark.sql import Window

# ─────────────────────────────────────────────
# Aliases de colonnes (noms longs → courts)
# ─────────────────────────────────────────────
PO_DOC   = "purchasing_document_|_ebeln"
ITEM     = "item_|_ebelp"
BEWTP    = "po_history_category_|_bewtp"
BWART    = "movement_type_|_bwart"
QUANTITY = "quantity_|_menge"
AMOUNT   = "amount_|_wrbtr"
LOEKZ    = "deletion_indicator_|_loekz"
ELIKZ    = "delivery_completed_|_elikz_ekpo"
NETPR    = "net_order_price_|_netpr"
PEINH    = "price_unit_|_peinh"


def build_po_status(df):
    """
    Enrichit le dataset SAP EKBE avec des colonnes de statut métier.

    Paramètre
    ---------
    df : DataFrame PySpark brut (1 ligne = 1 événement PO History)

    Retour
    ------
    DataFrame agrégé : 1 ligne par (purchasing_document, item)
    avec toutes les colonnes source + colonnes calculées.
    """

    # ─────────────────────────────────────────────
    # ÉTAPE 1 — Agrégations métier par clé unique
    # ─────────────────────────────────────────────
    agg_df = df.groupBy(PO_DOC, ITEM).agg(

        # ── Livraison nette (101 ajoute, 102 soustrait) ──────────────────
        F.sum(
            F.when(
                (F.col(BEWTP) == "E") & (F.col(BWART) == "101"),
                F.col(QUANTITY)
            ).when(
                (F.col(BEWTP) == "E") & (F.col(BWART) == "102"),
                -F.col(QUANTITY)
            ).otherwise(F.lit(0))
        ).alias("gr_quantity_received"),

        # ── Montant facturé total ─────────────────────────────────────────
        F.sum(
            F.when(
                F.col(BEWTP) == "Q",
                F.col(AMOUNT)
            ).otherwise(F.lit(0))
        ).alias("invoice_amount_total"),

        # ── Flags présence événements ─────────────────────────────────────
        F.max(
            F.when(F.col(BEWTP) == "E", F.lit(1)).otherwise(F.lit(0))
        ).alias("has_gr"),

        F.max(
            F.when(F.col(BEWTP) == "Q", F.lit(1)).otherwise(F.lit(0))
        ).alias("has_invoice"),

        # ── Colonnes de référence (valeur stable par ligne de commande) ───
        # On prend la dernière valeur non-nulle pour les champs statiques
        F.first(F.col(QUANTITY),     ignorenulls=True).alias("ordered_quantity"),
        F.first(F.col(AMOUNT),       ignorenulls=True).alias("ordered_amount"),
        F.first(F.col(LOEKZ),        ignorenulls=True).alias("_loekz"),
        F.first(F.col(ELIKZ),        ignorenulls=True).alias("_elikz"),
    )

    # ─────────────────────────────────────────────
    # ÉTAPE 2 — Jointure avec toutes les colonnes source
    # On conserve 1 ligne représentative par (doc, item)
    # via Window (row_number sur posting_date desc)
    # ─────────────────────────────────────────────
    w = Window.partitionBy(PO_DOC, ITEM).orderBy(
        F.col("posting_date_|_budat").desc_nulls_last()
    )

    df_deduped = (
        df
        .withColumn("_rn", F.row_number().over(w))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )

    # Jointure : on récupère toutes les colonnes source + les agrégats
    enriched = df_deduped.join(
        agg_df,
        on=[PO_DOC, ITEM],
        how="inner"
    )

    # ─────────────────────────────────────────────
    # ÉTAPE 3 — Calcul des statuts métier
    # ─────────────────────────────────────────────

    # ── Statut livraison ─────────────────────────
    enriched = enriched.withColumn(
        "delivery_status",
        F.when(
            (F.col(ELIKZ) == "X") |
            (F.col("gr_quantity_received") >= F.col("ordered_quantity")),
            F.lit("Fully Delivered")
        ).when(
            (F.col("gr_quantity_received") > 0) &
            (F.col("gr_quantity_received") < F.col("ordered_quantity")),
            F.lit("Partially Delivered")
        ).otherwise(
            F.lit("Not Delivered")
        )
    )

    # ── Statut facturation ───────────────────────
    enriched = enriched.withColumn(
        "invoice_status",
        F.when(
            F.col("invoice_amount_total") >= F.col("ordered_amount"),
            F.lit("Fully Invoiced")
        ).when(
            (F.col("invoice_amount_total") > 0) &
            (F.col("invoice_amount_total") < F.col("ordered_amount")),
            F.lit("Partially Invoiced")
        ).otherwise(
            F.lit("Not Invoiced")
        )
    )

    # ── Statut commande (Active / Closed) ────────
    enriched = enriched.withColumn(
        "order_status",
        F.when(
            (F.col(LOEKZ).isNotNull() & (F.col(LOEKZ) != "")) |
            (F.col(ELIKZ) == "X") |
            (
                (F.col("gr_quantity_received") >= F.col("ordered_quantity")) &
                (F.col("invoice_amount_total") >= F.col("ordered_amount"))
            ),
            F.lit("Closed")
        ).otherwise(
            F.lit("Active")
        )
    )

    # ─────────────────────────────────────────────
    # ÉTAPE 4 — Nettoyage des colonnes temporaires
    # ─────────────────────────────────────────────
    enriched = enriched.drop("_loekz", "_elikz")

    return enriched


# ─────────────────────────────────────────────
# UTILISATION
# ─────────────────────────────────────────────
# Remplacer `raw_df` par votre DataFrame source

# final_df = build_po_status(raw_df)

# Afficher les nouvelles colonnes calculées
# final_df.select(
#     "purchasing_document_|_ebeln",
#     "item_|_ebelp",
#     "ordered_quantity",
#     "gr_quantity_received",
#     "ordered_amount",
#     "invoice_amount_total",
#     "has_gr",
#     "has_invoice",
#     "delivery_status",
#     "invoice_status",
#     "order_status",
# ).show(20, truncate=False)

# Sauvegarder
# final_df.write.mode("overwrite").parquet("/path/to/output/po_enriched")
