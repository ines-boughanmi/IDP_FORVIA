# Phase 4A API Documentation

## Overview

Phase 4A adds an enterprise business API layer on top of the existing FastAPI backend.

All new business endpoints use the shared response envelope:

```json
{
  "status": "success",
  "data": {},
  "metadata": {}
}
```

## Authentication

All Phase 4A business endpoints require a JWT access token.

Header:

```http
Authorization: Bearer <access_token>
```

Token acquisition:

`POST /auth/login`

Example:

```json
{
  "username": "admin",
  "password": "adminpass"
}
```

## Endpoints

### 1. Executive KPI API

#### `GET /api/executive/dashboard`

Returns the executive dashboard summary.

Example response:

```json
{
  "status": "success",
  "data": {
    "total_transactions": 294722,
    "total_suppliers": 2293,
    "avg_transaction_risk": 9.84,
    "avg_supplier_risk": 31.12,
    "critical_transactions": 103148,
    "high_transactions": 0,
    "critical_suppliers": 0,
    "high_risk_suppliers": 0,
    "anomaly_rate": 12.41,
    "top_risk_supplier": {
      "supplier_id": 163806,
      "risk_score": 48.37,
      "risk_level": "LOW",
      "cluster_label": "STANDARD_SUPPLIERS"
    }
  },
  "metadata": {}
}
```

### 2. Advanced Search API

#### `GET /api/search/transactions`

Filters:
- `supplier_id`
- `risk_level`
- `min_score`
- `max_score`
- `date_from`
- `date_to`
- `keyword`
- `page`
- `page_size`

Example:

```http
GET /api/search/transactions?page=1&page_size=5&keyword=risk
```

Response example:

```json
{
  "status": "success",
  "data": {
    "transactions": [
      {
        "transaction_id": 4503462374,
        "supplier_id": 163806,
        "risk_score": 32.28,
        "risk_level": "CRITICAL",
        "explanation": "Multiple risk factors: aging (865 days), amount gap (88.5%)."
      }
    ]
  },
  "metadata": {
    "total": 294722,
    "count": 5,
    "page": 1,
    "page_size": 5
  }
}
```

#### `GET /api/search/suppliers`

Filters:
- `supplier_id`
- `cluster`
- `risk_level`
- `min_score`
- `max_score`
- `page`
- `page_size`

Example:

```http
GET /api/search/suppliers?page=1&page_size=5&cluster=STANDARD_SUPPLIERS
```

Response example:

```json
{
  "status": "success",
  "data": {
    "suppliers": [
      {
        "supplier_id": 163806,
        "risk_score": 48.37,
        "risk_level": "LOW",
        "cluster_label": "STANDARD_SUPPLIERS"
      }
    ]
  },
  "metadata": {
    "total": 2048,
    "count": 5,
    "page": 1,
    "page_size": 5
  }
}
```

### 3. Alert Center

#### `GET /api/alerts`

Returns all HIGH and CRITICAL entities.

#### `GET /api/alerts/transactions`

Returns transaction alerts only.

#### `GET /api/alerts/suppliers`

Returns supplier alerts only.

Alert shape:

```json
{
  "alert_id": "txn-4503462374",
  "entity_type": "transaction",
  "risk_score": 32.28,
  "risk_level": "CRITICAL",
  "explanation": "Multiple risk factors: aging (865 days), amount gap (88.5%).",
  "created_at": "2026-05-29T11:58:26.004438"
}
```

### 4. Supplier 360 View

#### `GET /api/supplier/{supplier_id}/overview`

Returns:
- supplier profile
- risk score
- risk level
- cluster
- behavior metrics
- anomaly metrics
- risk explanation
- transaction statistics

Example:

```http
GET /api/supplier/163806/overview
```

Example response excerpt:

```json
{
  "status": "success",
  "data": {
    "supplier_profile": {
      "supplier_id": 163806,
      "risk_score": 48.37,
      "risk_level": "LOW"
    },
    "cluster": {
      "cluster_id": 0,
      "cluster_label": "STANDARD_SUPPLIERS"
    },
    "behavior_metrics": {
      "transaction_frequency": 4737,
      "stability_score": 0.47
    },
    "transaction_statistics": {
      "total_transactions": 4737,
      "critical_transactions": 103,
      "high_transactions": 12
    }
  },
  "metadata": {}
}
```

### 5. Transaction 360 View

#### `GET /api/transaction/{transaction_id}/overview`

Returns:
- full transaction profile
- risk components
- supplier information
- explanation
- alerts

Example:

```http
GET /api/transaction/4503462374/overview
```

Example response excerpt:

```json
{
  "status": "success",
  "data": {
    "transaction_profile": {
      "transaction_id": 4503462374,
      "supplier_id": 163806,
      "risk_level": "CRITICAL"
    },
    "risk_components": {
      "amount_gap_pct": 88.5387,
      "days_in_system": 865,
      "supplier_risk_score": 25.0
    },
    "alerts": [
      {
        "alert_id": "txn-4503462374",
        "entity_type": "transaction",
        "risk_level": "CRITICAL"
      }
    ]
  },
  "metadata": {}
}
```

### 6. Chatbot Preparation

File: `api/services/chatbot_service.py`

Available functions:

```python
supplier_context_builder(supplier_id)
transaction_context_builder(transaction_id)
executive_context_builder()
```

These return narrative text for future RAG / chatbot consumption.

### 7. Analytics API

#### `GET /api/analytics/risk-distribution`

#### `GET /api/analytics/top-risk-suppliers`

Query params:
- `limit`

#### `GET /api/analytics/cluster-distribution`

#### `GET /api/analytics/anomaly-summary`

Response format is JSON only, wrapped in the standard response envelope.

Example integration response:

```json
{
  "status": "success",
  "data": {
    "clusters": [
      {
        "cluster_id": 0,
        "cluster_label": "STANDARD_SUPPLIERS",
        "suppliers": 2048
      }
    ]
  },
  "metadata": {}
}
```

## Frontend Integration Examples

### Fetch example

```javascript
const token = localStorage.getItem('access_token');

const response = await fetch('http://127.0.0.1:8000/api/executive/dashboard', {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

const json = await response.json();
console.log(json.data);
```

### Axios example

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
});

const { data } = await api.get('/api/supplier/163806/overview', {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
```

## Notes

- Pagination is supported on search endpoints.
- The alert center returns a large number of records because it includes all HIGH and CRITICAL entities from the datasets.
- Existing datasets, clustering, explainability and risk formulas were not modified.
