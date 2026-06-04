# Dictionnaire des Données - IDP Monitoring

Ce document décrit les colonnes du fichier source (`Documents1.csv`) et leur signification métier (SAP).

## 📌 Identification & Structure
| Nom Technique (SAP) | Nom Renommé (FR) | Description | Exemples de Valeurs |
| :--- | :--- | :--- | :--- |
| `purchasing_document_\|_ebeln` | **Numéro_PO** | Numéro unique de la commande d'achat (Purchasing Order). | `4501608110` |
| `item_\|_ebelp` | **Ligne_PO** | Numéro de la ligne dans la commande (incrément de 10 généralement). | `00010`, `00020` |
| `plant_\|_werks` | **Usine** | Code de l'usine ou du site logistique concerné. | `1385` (Ben Arous) | `1474` (FIT) |
| `supplier_\|_lifnr` | **Fournisseur** | Code unique identifiant le fournisseur. | `0000108870` |

## 📅 Dates Clés
| Nom Technique (SAP) | Nom Renommé (FR) | Description | Exemples de Valeurs |
| :--- | :--- | :--- | :--- |
| `document_date_\|_bedat` | **Date_Document** | Date de création de la commande d'achat. | `2020-03-24` |
| `posting_date_\|_budat` | **Date_Comptable** | Date à laquelle l'opération est enregistrée en comptabilité. | `2024-03-14` |
| `entry_date_\|_cpudt` | **Date_Saisie** | Date système de la saisie de l'information. | `2024-03-14` |

## 📦 Matériel & Quantités
| Nom Technique (SAP) | Nom Renommé (FR) | Description | Exemples de Valeurs |
| :--- | :--- | :--- | :--- |
| `material_\|_matnr` | **Matériel** | Code article (si renseigné). Souvent vide pour les services/achats indirects. | `9920--` |
| `short_text_\|_txz01` | **Description** | Description courte de la commande ou du service. | `AUDIT`, `Traitement Paie` |
| `quantity_\|_menge` | **Quantité** | Quantité commandée ou réceptionnée. | `1`, `11500` |
| `order_unit_\|_meins` | **Unité_Commande** | Unité de mesure pour la commande. | **EA** (Each/Pièce), **MON** (Mois), **H** (Heure), **KG** (Kilogramme), **ST** (Pièce) |

## 💰 Montants & Prix
| Nom Technique (SAP) | Nom Renommé (FR) | Description | Exemples de Valeurs |
| :--- | :--- | :--- | :--- |
| `net_order_price_\|_netpr` | **Prix_Net** | Prix unitaire net de l'article/service. | `11500.0` |
| `amount_\|_wrbtr` | **Montant** | Montant total de la ligne (Quantité x Prix). | `18826.2` |
| `currency_\|_waers` | **Devise** | Devise de la transaction. | `EUR`, `TND`, `USD` |

## 🔄 Historique & Flux (BEWTP / BWART)
Ces colonnes sont cruciales pour le monitoring du cycle de vie (Procure-to-Pay).

| Nom Technique (SAP) | Nom Renommé (FR) | Description | Valeurs Clés & Signification |
| :--- | :--- | :--- | :--- |
| `po_history_category_\|_bewtp` | **Catégorie_Historique_PO** | Type d'événement dans l'historique de la commande. | **E** = Goods Receipt (Réception Marchandise)<br>**Q** = Invoice Receipt (Facture)<br>**K** = Account Maintenance (Régularisation)<br>**N** = Subsequent Debit (Coût additionnel) |
| `movement_type_\|_bwart` | **Type_Mouvement** | Code mouvement de stock (si applicable). | **101** = Entrée sur commande<br>**102** = Annulation entrée<br>**122** = Retour fournisseur |
| `debitcredit_ind_\|_shkzg` | **Débit_Crédit** | Sens de l'opération comptable. | **S** = Débit (Debit)<br>**H** = Crédit (Credit) |

## ⚙️ Autres Indicateurs
| Nom Technique (SAP) | Nom Renommé (FR) | Description | Exemples de Valeurs |
| :--- | :--- | :--- | :--- |
| `purchasing_doc_type_\|_bsart` | **Type_PO** | Type de document d'achat (Standard, Cadre, Service, etc.) | `ECPO` (Commande standard), `NB` |
| `delivery_completed_\|_elikz_ekpo` | **Livraison_Clôturée** | Indicateur si la livraison est considérée comme terminée. | `X` = Oui, Vide = Non |
| `deletion_indicator_\|_loekz` | **Indicateur_Suppression** | Indique si la ligne a été supprimée ou annulée. | `L` = Supprimé |
