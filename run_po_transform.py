"""
run_po_transform.py
===================
Script complet à exécuter — lit Contracts.csv, applique toutes les
transformations métier SAP PO History et sauvegarde le résultat.

Prérequis
---------
  pip install pyspark

Usage
-----
  spark-submit run_po_transform.py
  # ou directement dans un notebook / shell Python avec Spark installé :
  # python run_po_transform.py
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import Window
import pyspark.sql.types as T

# ══════════════════════════════════════════════════════════════════════
# 0.  CONFIGURATION — adapter ces 2 chemins si nécessaire
# ══════════════════════════════════════════════════════════════════════

# Dossier où se trouvent Contracts.csv ET ce script
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV   = os.path.join(BASE_DIR, "Contracts.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "Contracts_enriched")   # dossier parquet

# ══════════════════════════════════════════════════════════════════════
# 1.  DÉMARRAGE SPARK
# ══════════════════════════════════════════════════════════════════════

spark = (
    SparkSession.builder
    .appName("SAP_PO_History_Transform")
    .config("spark.sql.legacy.timeParserPolicy", "LEGACY")   # tolérance formats date
    .config("spark.driver.memory", "4g")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# ══════════════════════════════════════════════════════════════════════
# 2.  SCHÉMA COMPLET
# ══════════════════════════════════════════════════════════════════════

SCHEMA = T.StructType([
    T.StructField("purchasing_document_|_ebeln",                      T.StringType()),
    T.StructField("item_|_ebelp",                                     T.StringType()),
    T.StructField("source",                                           T.StringType()),
    T.StructField("plant_|_werks",                                    T.StringType()),
    T.StructField("supplier_|_lifnr",                                 T.StringType()),
    T.StructField("purchasing_doc_type_|_bsart",                      T.StringType()),
    T.StructField("purch_organization_|_ekorg",                       T.StringType()),
    T.StructField("purchasing_group_|_ekgrp",                         T.StringType()),
    T.StructField("document_date_|_bedat",                            T.DateType()),
    T.StructField("material_|_matnr",                                 T.StringType()),
    T.StructField("material_group_|_matkl",                           T.StringType()),
    T.StructField("short_text_|_txz01",                               T.StringType()),
    T.StructField("order_unit_|_meins",                               T.StringType()),
    T.StructField("order_price_unit_|_bprme",                         T.StringType()),
    T.StructField("price_unit_|_peinh",                               T.DecimalType(5,  0)),
    T.StructField("net_order_price_|_netpr",                          T.DecimalType(11, 2)),
    T.StructField("quantity_|_menge",                                 T.DecimalType(13, 3)),
    T.StructField("amount_|_wrbtr",                                   T.DecimalType(13, 2)),
    T.StructField("amtin_loccur_|_dmbtr",                             T.DecimalType(13, 2)),
    T.StructField("currency_|_waers",                                 T.StringType()),
    T.StructField("movement_type_|_bwart",                            T.StringType()),
    T.StructField("po_history_category_|_bewtp",                      T.StringType()),
    T.StructField("debitcredit_ind_|_shkzg",                          T.StringType()),
    T.StructField("posting_date_|_budat",                             T.DateType()),
    T.StructField("reference_document_|_lfbnr",                       T.StringType()),
    T.StructField("reference_doc_item_|_lfpos",                       T.StringType()),
    T.StructField("reason_for_movement_|_grund",                      T.StringType()),
    T.StructField("deletion_indicator_|_loekz",                       T.StringType()),
    T.StructField("delivery_completed_|_elikz_ekpo",                  T.StringType()),
    T.StructField("invoice_value_|_reewr",                            T.DecimalType(13, 2)),
    T.StructField("outline_agreement_|_konnr",                        T.StringType()),
    T.StructField("terms_of_payment_|_zterm",                         T.StringType()),
    T.StructField("tax_code_|_mwskz",                                 T.StringType()),
    T.StructField("incoterms_|_inco1",                                T.StringType()),
    T.StructField("incoterms_part_2_|_inco2",                         T.StringType()),
    T.StructField("net_weight_|_ntgew",                               T.DecimalType(13, 3)),
    T.StructField("gross_weight_|_brgew",                             T.DecimalType(13, 3)),
    T.StructField("unit_of_weight_|_gewei",                           T.StringType()),
    T.StructField("volume_|_volum",                                   T.DecimalType(13, 3)),
    T.StructField("storage_location",                                 T.StringType()),
    T.StructField("batch_|_charg",                                    T.StringType()),
    T.StructField("grir_clearing_value_in_local_currency_|_arewr",    T.DecimalType(13, 2)),
    T.StructField("valuation_type_|_bwtar",                           T.StringType()),
    T.StructField("document_date_|_bldat",                            T.DateType()),
    T.StructField("planned_deliv_time_|_plifz",                       T.DecimalType(3,  0)),
    T.StructField("gr_processing_time_|_webaz",                       T.DecimalType(3,  0)),
    T.StructField("last_changed_on_|_aedat",                          T.DateType()),
    T.StructField("vendor_material_no_|_idnlf",                       T.StringType()),
    T.StructField("purchasing_info_rec_|_infnr",                      T.StringType()),
    T.StructField("item_category_|_pstyp",                            T.StringType()),
    T.StructField("entry_date_|_cpudt",                               T.DateType()),
    T.StructField("time_of_entry_|_cputm",                            T.StringType()),
    T.StructField("created_by_|_ernam",                               T.StringType()),
    T.StructField("ekko_data_ingestion_freshness_timestamp_utc",       T.TimestampType()),
    T.StructField("ekpo_data_ingestion_freshness_timestamp_utc",       T.TimestampType()),
    T.StructField("supplier_id",                                      T.StringType()),
    T.StructField("supplier_name",                                    T.StringType()),
    T.StructField("city",                                             T.StringType()),
    T.StructField("region",                                           T.StringType()),
])

# ══════════════════════════════════════════════════════════════════════
# 3.  LECTURE DU CSV
# ══════════════════════════════════════════════════════════════════════

print(f"\n📂 Lecture : {INPUT_CSV}")

raw_df = (
    spark.read
    .option("header",          "true")
    .option("inferSchema",     "false")       # on impose le schéma
    .option("sep",             ",")
    .option("quote",           "\"")
    .option("escape",          "\"")
    .option("multiLine",       "true")        # gestion des champs multi-lignes
    .option("dateFormat",      "yyyy-MM-dd")  # adapter si ton CSV utilise dd/MM/yyyy
    .option("timestampFormat", "yyyy-MM-dd HH:mm:ss")
    .option("nullValue",       "")
    .option("emptyValue",      "")
    .schema(SCHEMA)
    .csv(INPUT_CSV)
)

print(f"   Lignes brutes : {raw_df.count():,}")
print(f"   Colonnes      : {len(raw_df.columns)}")

# ══════════════════════════════════════════════════════════════════════
# 4.  ALIASES (noms de colonnes raccourcis)
# ══════════════════════════════════════════════════════════════════════

PO_DOC   = "purchasing_document_|_ebeln"
ITEM     = "item_|_ebelp"
BEWTP    = "po_history_category_|_bewtp"
BWART    = "movement_type_|_bwart"
QUANTITY = "quantity_|_menge"
AMOUNT   = "amount_|_wrbtr"
LOEKZ    = "deletion_indicator_|_loekz"
ELIKZ    = "delivery_completed_|_elikz_ekpo"
POST_DT  = "posting_date_|_budat"

# ══════════════════════════════════════════════════════════════════════
# 5.  ÉTAPE 1 — AGRÉGATIONS PAR (purchasing_document, item)
# ══════════════════════════════════════════════════════════════════════

print("\n⚙️  Étape 1 — Agrégations métier...")

agg_df = raw_df.groupBy(PO_DOC, ITEM).agg(

    # Quantité livrée nette : 101 ajoute / 102 annule
    F.sum(
        F.when((F.col(BEWTP) == "E") & (F.col(BWART) == "101"),  F.col(QUANTITY))
         .when((F.col(BEWTP) == "E") & (F.col(BWART) == "102"), -F.col(QUANTITY))
         .otherwise(F.lit(0))
    ).alias("gr_quantity_received"),

    # Montant total facturé
    F.sum(
        F.when(F.col(BEWTP) == "Q", F.col(AMOUNT))
         .otherwise(F.lit(0))
    ).alias("invoice_amount_total"),

    # Flag : au moins 1 GR
    F.max(
        F.when(F.col(BEWTP) == "E", F.lit(1)).otherwise(F.lit(0))
    ).alias("has_gr"),

    # Flag : au moins 1 facture
    F.max(
        F.when(F.col(BEWTP) == "Q", F.lit(1)).otherwise(F.lit(0))
    ).alias("has_invoice"),

    # Quantité et montant commandés (valeur stable par ligne)
    F.first(F.col(QUANTITY), ignorenulls=True).alias("ordered_quantity"),
    F.first(F.col(AMOUNT),   ignorenulls=True).alias("ordered_amount"),
)

# ══════════════════════════════════════════════════════════════════════
# 6.  ÉTAPE 2 — LIGNE REPRÉSENTATIVE (toutes colonnes source)
#     row_number() sur posting_date DESC → 1 ligne par (doc, item)
# ══════════════════════════════════════════════════════════════════════

print("⚙️  Étape 2 — Sélection ligne représentative + jointure...")

w = Window.partitionBy(PO_DOC, ITEM).orderBy(
    F.col(POST_DT).desc_nulls_last()
)

df_deduped = (
    raw_df
    .withColumn("_rn", F.row_number().over(w))
    .filter(F.col("_rn") == 1)
    .drop("_rn")
)

# Jointure : toutes colonnes source + agrégats
enriched = df_deduped.join(agg_df, on=[PO_DOC, ITEM], how="inner")

# ══════════════════════════════════════════════════════════════════════
# 7.  ÉTAPE 3 — STATUTS MÉTIER
# ══════════════════════════════════════════════════════════════════════

print("⚙️  Étape 3 — Calcul des statuts métier...")

# ── Statut livraison ──────────────────────────────────────────────────
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

# ── Statut facturation ────────────────────────────────────────────────
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

# ── Statut commande ───────────────────────────────────────────────────
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

# ══════════════════════════════════════════════════════════════════════
# 8.  APERÇU DANS LA CONSOLE
# ══════════════════════════════════════════════════════════════════════

total = enriched.count()
print(f"\n✅ Dataset final : {total:,} lignes  |  {len(enriched.columns)} colonnes")
print("\n── Aperçu des colonnes calculées ──")

enriched.select(
    PO_DOC,
    ITEM,
    "ordered_quantity",
    "gr_quantity_received",
    "ordered_amount",
    "invoice_amount_total",
    "has_gr",
    "has_invoice",
    "delivery_status",
    "invoice_status",
    "order_status",
).show(20, truncate=False)

print("\n── Distribution delivery_status ──")
enriched.groupBy("delivery_status").count().orderBy("count", ascending=False).show()

print("\n── Distribution invoice_status ──")
enriched.groupBy("invoice_status").count().orderBy("count", ascending=False).show()

print("\n── Distribution order_status ──")
enriched.groupBy("order_status").count().orderBy("count", ascending=False).show()

# ══════════════════════════════════════════════════════════════════════
# 9.  SAUVEGARDE
#     → Parquet (recommandé pour Spark)
#     → CSV commenté ci-dessous si tu préfères
# ══════════════════════════════════════════════════════════════════════

print(f"\n💾 Sauvegarde parquet → {OUTPUT_PATH}")
(
    enriched
    .write
    .mode("overwrite")
    .option("compression", "snappy")
    .parquet(OUTPUT_PATH)
)

# ── Option CSV (décommenter si besoin) ───────────────────────────────
# OUTPUT_CSV = os.path.join(BASE_DIR, "Contracts_enriched_csv")
# (
#     enriched
#     .coalesce(1)                     # 1 seul fichier CSV
#     .write
#     .mode("overwrite")
#     .option("header", "true")
#     .option("sep", ",")
#     .csv(OUTPUT_CSV)
# )
# print(f"💾 Sauvegarde CSV    → {OUTPUT_CSV}")

print("\n🎉 Transformation terminée avec succès.")
spark.stop()
