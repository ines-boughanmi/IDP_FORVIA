# Phase 4B Frontend Documentation

## Purpose

This React frontend provides an enterprise UI for the backend intelligence platform.

It consumes the existing backend APIs directly and does not modify backend behavior.

## Architecture

### Core layers

- `frontend/src/services/apiClient.ts`: low-level fetch wrapper, token handling, error normalization.
- `frontend/src/services/backendApi.ts`: typed backend API surface.
- `frontend/src/context/AuthContext.tsx`: JWT login, token persistence, auto logout, restored session bootstrap.
- `frontend/src/components/layout/*`: app shell, sidebar, topbar.
- `frontend/src/components/ui/*`: reusable enterprise UI components.
- `frontend/src/components/charts/*`: chart widgets.
- `frontend/src/pages/*`: route-level business pages.
- `frontend/src/features/chatbot/chatbotContracts.ts`: future chatbot integration contracts.

### State management

- Authentication state is held in React context.
- Server state is handled with TanStack Query.
- JWT tokens are stored in `localStorage` and cleared on expiry.

## Routes

- `/login`
- `/dashboard`
- `/alerts`
- `/suppliers`
- `/supplier/:supplierId`
- `/transactions`
- `/transaction/:transactionId`
- `/analytics`

## Backend endpoints used

- `POST /auth/login`
- `GET /auth/me`
- `GET /api/executive/dashboard`
- `GET /api/alerts`
- `GET /api/alerts/transactions`
- `GET /api/alerts/suppliers`
- `GET /api/search/transactions`
- `GET /api/search/suppliers`
- `GET /api/supplier/{supplier_id}/overview`
- `GET /api/transaction/{transaction_id}/overview`
- `GET /api/analytics/risk-distribution`
- `GET /api/analytics/top-risk-suppliers`
- `GET /api/analytics/cluster-distribution`
- `GET /api/analytics/anomaly-summary`

## UI pages

### Login

- JWT login
- token persistence
- auto logout through token expiry
- route protection

### Executive dashboard

- KPI cards
- risk distribution chart
- supplier risk ranking
- cluster breakdown
- anomaly summary

### Alert center

- alert tables for all / transaction / supplier alerts
- search and filtering
- local pagination

### Supplier intelligence

- supplier search
- risk filtering
- cluster filtering
- supplier 360 view with behavior, anomaly and transaction statistics

### Transaction investigation

- transaction search
- risk filtering
- transaction 360 view with supplier context and alerts

### Analytics center

- risk distribution
- top risk suppliers
- cluster distribution
- anomaly breakdown

## Chatbot preparation

The frontend already exposes a contract layer for future RAG/chatbot integration:

- executive context
- supplier narrative context
- transaction narrative context

These are intentionally separated so a future chatbot panel can consume them without changing the current dashboard routes.

## Validation notes

- Frontend structure is created and wired.
- API client and auth context are implemented.
- Responsive theme is implemented for desktop and mobile.
- Final build should be run after installing npm dependencies.
