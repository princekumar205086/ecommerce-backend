# RX Verifier — Comprehensive Documentation

Last updated: 2025-11-08

This single reference consolidates the RX Upload & Verification API documentation, implementation report, endpoints reference, testing guide, and operational notes into one authoritative document for engineers, QA, and DevOps.

---

## Table of Contents
1. Overview
2. System Architecture
3. Data Models (Key)
4. Authentication & Roles
5. API Endpoints (summary)
6. End-to-end Workflow
7. Order Integration & Invoice Flow
8. Invoice PDF Generation (ReportLab)
9. Email Notifications
10. Caching & Performance
11. Testing & Validation
12. Local Development & Runbook
13. Troubleshooting
14. Deployment & Production Checklist
15. File Map (recently modified/created)
16. Next Improvements
17. Contacts & Support

---

## 1. Overview

The RX Verifier subsystem provides a complete, enterprise-grade prescription upload, verification, and fulfillment pipeline. It enables customers to upload prescriptions, allows trained RX verifiers to review and approve/reject/clarify prescriptions, converts approved prescriptions into orders, generates professional invoices (PDF), and sends confirmation emails with invoice attachments.

Goals:
- Secure, auditable verification workflow
- Reliable order creation from approved prescriptions
- Professional invoice generation and email delivery
- Enterprise features: caching, monitoring, audit trails, rate limiting


## 2. System Architecture

High-level components:
- API Layer (Django REST endpoints under `/api/rx-upload/`)
- Business Logic: `PrescriptionOrderManager`, validators, audit logger
- Data Layer: `PrescriptionUpload`, `VerifierWorkload`, `Order`, `Invoice` and related models
- External Services: ImageKit (file storage), SMTP (email), Redis (cache)

Architecture diagram (conceptual):
```
Customer -> API -> Verifier UI/API -> Business Logic -> Database
                                    \-> Email Service
                                    \-> ImageKit CDN
                                    \-> Cache (Redis)
```


## 3. Data Models (Key)

- PrescriptionUpload
  - id (UUID), prescription_number, customer (FK), patient fields, medications_prescribed (text), verification_status (pending/in_review/approved/rejected/clarification_needed), verified_by (FK to User), uploaded_at, priority, etc.

- VerifierWorkload
  - verifier (OneToOne User), pending_count, in_review_count, total_verified, is_available, max_daily_capacity

- VerificationActivity
  - prescription (FK), verifier, action, description, timestamp

- Order
  - user, order_number, status, payment_status, payment_method, subtotal, tax, shipping_charge, discount, coupon_discount, total, shipping_address (JSON), billing_address (JSON), notes

- OrderItem
  - order (FK), product (FK), variant (nullable FK), quantity, price, created_at; property `total_price`

- Invoice
  - order (OneToOne), invoice_number, amounts (subtotal, tax, shipping, discount, total), amount_paid, balance_due, pdf_file (FileField), issued_date, due_date, status, notes

- InvoiceLineItem
  - invoice (FK), product_name, quantity, unit_price, tax_rate, discount, total_price

- InvoicePayment
  - invoice (FK), amount, payment_method, transaction_id, payment_date


## 4. Authentication & Roles

- Roles supported: `user` (customer), `rx_verifier`, `admin`, `supplier`.
- Verifier endpoints require `rx_verifier` role (or admin access for management endpoints).
- Authentication: supports session auth and JWT (Simple JWT). Tests attempt to obtain access token at `/api/token/` and fall back to session login.


## 5. API Endpoints (summary)

Base namespace: `/api/rx-upload/`

Authentication & profile:
- POST `auth/login/` — verifier login
- POST `auth/logout/` — logout
- GET `auth/profile/` — profile + workload

Prescription management:
- GET|POST `prescriptions/` — list/create
- GET `prescriptions/<uuid:pk>/` — detail
- POST `prescriptions/<id>/assign/` — assign to current verifier
- POST `prescriptions/<id>/approve/` — approve
- POST `prescriptions/<id>/reject/` — reject
- POST `prescriptions/<id>/clarification/` — request clarification

Order integration:
- POST `prescriptions/<id>/create-order/` — convert approved prescription to order (optionally provide `medications` mapping)
- GET `prescriptions/<id>/orders/` — list orders associated with prescription

Additional:
- GET `dashboard/` — verifier dashboard counts
- GET `pending/` — pending prescriptions
- POST `availability/` — set verifier availability
- Admin endpoints for verifier account management under `/admin/` prefix

For full path listing, see `rx_upload/urls.py`.


## 6. End-to-end Workflow

1. Customer uploads a prescription via `POST /api/rx-upload/prescriptions/` (multipart/form-data). Prescription is created with `verification_status = pending`.
2. Verifier views pending items via `GET /api/rx-upload/pending/` or dashboard `GET /api/rx-upload/dashboard/`.
3. Verifier assigns to themselves with `POST /prescriptions/<id>/assign/` (status -> `in_review`).
4. Verifier approves (`POST /prescriptions/<id>/approve/`) or rejects (`POST /prescriptions/<id>/reject/`) or requests clarification (`POST /prescriptions/<id>/clarification/`). Notifications are sent accordingly.
5. If approved, verifier may call `POST /prescriptions/<id>/create-order/` to create an `Order` from the prescription. The service will match medication names to `Product` records, create `OrderItem`s, decrement stock, calculate totals, create an `Invoice`, generate a PDF, and send a confirmation email with the invoice attached.
6. Order lifecycle continues (processing, shipping, delivery, payment).


## 7. Order Integration & Invoice Flow

Core service: `PrescriptionOrderManager` in `rx_upload/order_integration.py`.

Main responsibilities:
- Validate prescription (must be `approved`).
- Ensure customer has shipping/billing address.
- Map medications to published `Product`s (uses `_find_matching_product` with `name__icontains` and `name__iexact`).
- Create `Order` & `OrderItem` rows within a transaction. Decrement stock safely.
- After order creation, call `Invoice.create_from_order(order)` to create `Invoice` instance.
- Populate `InvoiceLineItem`s from order items and call `invoice.generate_pdf()` to produce PDF bytes and attempt to save to `Invoice.pdf_file`.
- Send an enterprise-grade order confirmation email to the customer; attach PDF if available.

Error handling:
- If no valid products found, the order is rolled back and an error returned.
- PDF generation errors are logged and do not block email sending (email will still be sent without attachment).


## 8. Invoice PDF Generation (ReportLab)

- Implemented in `invoice/models.py` — `Invoice.generate_pdf()` uses ReportLab Platypus to create a professional invoice.
- Features:
  - Optional logo inclusion (`settings.INVOICE_LOGO_PATH`).
  - Header with company name (`settings.APP_NAME`) and contact email (`settings.DEFAULT_FROM_EMAIL`).
  - Invoice metadata (invoice number, date, order number, due date).
  - Billing and shipping address blocks (uses `order.billing_address` and `order.shipping_address` JSON fields).
  - Line items table (item name, qty, unit price, total).
  - Totals box (subtotal, tax, shipping, discount, total).
  - Notes and footer.
- The method returns PDF bytes and attempts to save to `pdf_file` FileField using Django storage. If saving fails, it swallows the error (so invoice generation does not crash order creation flow).

Requirements & tuning:
- `reportlab` must be installed in the environment.
- `INVOICE_LOGO_PATH` should be a local filesystem path accessible by Django if you want a logo in the PDF.


## 9. Email Notifications

Types of emails implemented:
- Prescription approved — sends verification confirmation to customer.
- Prescription rejected — sends rejection reason and resubmission guidance.
- Clarification requested — requests extra info from customer.
- Order confirmation (important) — professional HTML email with order summary and invoice PDF attachment when available.

Implementation details:
- Uses Django's `EmailMultiAlternatives` for HTML + plain text fallbacks.
- Order confirmation HTML is built with inline styles for reliable rendering across clients and includes order items, totals, shipping address, and CTAs.
- In `PrescriptionOrderManager._send_order_confirmation_email`, the code attempts to attach `Invoice.generate_pdf()` output and will log attachment errors without failing the email send.

Local dev tip: set `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` to see outgoing emails in the console during dev.


## 10. Caching & Performance

- `products/enterprise_cache.py` provides `EnterpriseCacheManager` with key generation helpers, `get/set` wrappers and `invalidate_cache_pattern()`.
- Invalidation supports backends with `delete_pattern`; falls back to best-effort inspection for LocMemCache by checking `cache._cache`.
- Signal handlers invalidate product/category/brand cache on `post_save` and `post_delete` events.
- `Order.calculate_totals()` and other heavy operations use `select_related` and transaction semantics to optimize DB usage.


## 11. Testing & Validation

- `rx_upload/comprehensive_rx_test.py` is an end-to-end test harness that:
  - Creates test users (customer, verifier, admin), test products and prescriptions
  - Simulates verifier login, obtains JWT token if available, and runs through assign/approve/create-order flows
  - Validates that emails are sent and invoices generated (PDF saved to storage)

How to run tests locally:

```powershell
python manage.py migrate
python rx_upload\comprehensive_rx_test.py
```

The harness will print a summary and colored output for pass/fail per test.

Additional scripts:
- `scripts/generate_sample_invoice.py` — creates a sample user, product, order, and generates `generated_invoices/sample_invoice_<invoice_number>.pdf` for manual inspection.


## 12. Local Development & Runbook

Essential commands:

```powershell
# Install deps (ensure virtualenv active)
pip install -r requirements.txt

# Migrate DB
python manage.py migrate

# Run sample invoice generator
python scripts\generate_sample_invoice.py

# Run the test harness
python rx_upload\comprehensive_rx_test.py

# Run dev server
python manage.py runserver
```

Notes:
- If you encounter import-time syntax errors after editing `invoice/models.py`, run `python -m py_compile invoice/models.py` to find syntax problems.
- Use `django.core.mail.backends.console.EmailBackend` for dev email debugging.


## 13. Troubleshooting

Common issues and fixes:

- PDF generation returns `None` or fails:
  - Check that `reportlab` is installed.
  - Verify `INVOICE_LOGO_PATH` points to a valid file if used.
  - Inspect application logs — `generate_pdf()` logs exceptions to the project logger.

- Emails not delivered:
  - Check email settings in `ecommerce/settings.py`.
  - For dev, use console backend to confirm email content and attachments.

- Products not matched during order creation:
  - Ensure products exist and `is_publish=True`.
  - Matching uses `name__icontains` and `name__iexact`. For better accuracy, consider mapping SKU/IDs or fuzzy matching service.

- Cache not invalidating on dev (LocMemCache):
  - `EnterpriseCacheManager` attempts a best-effort fallback; for production use Redis for robust pattern delete support.


## 14. Deployment & Production Checklist

Before pushing to production:
- [ ] Confirm `EMAIL_BACKEND` configured for SMTP and credentials are set in environment.
- [ ] Set `CACHES` to Redis or Memcached for robust invalidation.
- [ ] Ensure `INVOICE_LOGO_PATH` (if used) is available on all app instances or use S3 and fetch locally during PDF generation (or switch to wkhtmltopdf/WeasyPrint with remote assets).
- [ ] Add background processing for email/PDF generation (Celery or RQ) for reliability at scale.
- [ ] Review logs & monitoring for invoice generation failures and set up alerts.
- [ ] Add CI job to run `rx_upload/comprehensive_rx_test.py` as an integration smoke test after migrations.


## 15. File Map (recently modified/created)

- `invoice/models.py` — Reworked Invoice model with `generate_pdf()` (ReportLab) and `InvoiceLineItem` / `InvoicePayment`.
- `rx_upload/order_integration.py` — `PrescriptionOrderManager` service for converting prescriptions to orders and emailing invoices.
- `rx_upload/comprehensive_rx_test.py` — end-to-end verifier-to-order test harness.
- `products/enterprise_cache.py` — cache manager with invalidation fallback.
- `scripts/generate_sample_invoice.py` — creates sample order/invoice and writes a PDF to `generated_invoices/`.
- `rx_upload/RX_VERIFIER_ENDPOINTS.md` and `RX_VERIFICATION_API_DOCUMENTATION.md` — original docs (consolidated into this file).


## 16. Next Improvements (recommended)

- Add unit tests for `PrescriptionOrderManager` covering edge cases (missing address, out-of-stock, partial matches, pdf failure).
- Add a PDF unit test that inspects content structure (using a PDF parsing library) to assert invoice number and totals.
- Integrate background job queue for PDF generation & email sending (Celery + Redis).
- Implement a medication-to-product mapping table for guaranteed matching and faster order creation.
- Localize currency and date formatting in invoices for multi-region support.


## 17. Contacts & Support

- RX Support: `rx-support@medixmall.com`
- Developer / Repo Owner: `princekumar205086` (local Maintainer)

---

If you want, I can:
- commit this combined doc and open a PR with a summary message,
- add CLI flags to `scripts/generate_sample_invoice.py` (logo, item count, tax) for richer manual testing,
- add a CI job definition (GitHub Actions) to run the comprehensive test harness after migrations.

Tell me which next step you'd like and I'll proceed.