# RX Verifier — Endpoints & Implementation Reference

This document describes the RX Verifier subsystem in this repository: the endpoints, flows, models, services, tests, configuration options, and troubleshooting notes. It's intended for backend engineers and QA to understand, run, and validate the verifier → order → invoice → email workflow.

---

**Last updated:** 2025-11-08

**Primary locations of interest (modified/created during recent work):**
- `rx_upload/` (core views, endpoints, tests)
  - `rx_upload/views.py` — verifier actions (assign/approve/reject/clarify), dashboard, order integration endpoints.
  - `rx_upload/order_integration.py` — service that converts an approved `PrescriptionUpload` into an `Order`, creates an `Invoice`, generates PDF, and sends a confirmation email.
  - `rx_upload/comprehensive_rx_test.py` — enterprise-grade end-to-end test harness for the verifier flow.
  - `rx_upload/urls.py` — router listing all verifier endpoints.
  - `rx_upload/serializers.py` / `rx_upload/models.py` — prescription-related models and serialization (unchanged here but central to flow).

- `orders/models.py` — `Order`, `OrderItem`, and supporting logic used by RX order creation.
- `invoice/models.py` — Reworked `Invoice` model, `InvoiceLineItem`, `InvoicePayment`, and `Invoice.generate_pdf()` (ReportLab Platypus). This file was fixed and stabilized.
- `products/enterprise_cache.py` — Enterprise cache manager used by product lookups (fallback invalidation handling added).
- `scripts/generate_sample_invoice.py` — small utility script that creates a sample `Order` + `Invoice` and writes a sample PDF to `generated_invoices/` for manual inspection.

---

## 1. Purpose & High-level flow

Primary goal: provide a reliable end-to-end flow where a verified prescription can be converted into an order for the customer, generate a professional invoice PDF, and send a confirmation email with the invoice attached.

Flow (simplified):
1. Customer uploads a prescription (via customer endpoints in `rx_upload/customer_views.py`).
2. RX verifier (human) logs into the verifier UI/API (`/api/rx-upload/auth/login/`) and sees pending prescriptions in the dashboard.
3. Verifier assigns, reviews and either approves or rejects a prescription using endpoints in `rx_upload/views.py`.
4. On approval, the verifier can call `/api/rx-upload/prescriptions/<id>/create-order/` to create an `Order` from prescription contents.
5. The order creation service (`PrescriptionOrderManager` in `rx_upload/order_integration.py`) handles product matching, creates `OrderItem`s, decrements stock, creates an `Invoice` via `Invoice.create_from_order()`, populates `InvoiceLineItem`s, calls `invoice.generate_pdf()` to generate a professional PDF and attempts to save it to the `Invoice.pdf_file` FileField, and finally sends a transactional HTML email with the invoice attached.
6. Tests and scripts validate the flow: `rx_upload/comprehensive_rx_test.py` covers login, dashboard, assign, approve, create-order and email/invoice checks. `scripts/generate_sample_invoice.py` can generate a sample invoice PDF locally for manual inspection.

---

## 2. Key endpoints (rx_upload `urls.py`)

NOTE: All endpoints are mounted under `/api/` in the project. `app_name = 'rx_upload'`.

- Authentication & profile
  - `POST /api/rx-upload/auth/login/` — login for verifier
  - `POST /api/rx-upload/auth/logout/` — logout
  - `GET /api/rx-upload/auth/profile/` — verifier profile

- Prescription management (verifier)
  - `GET|POST /api/rx-upload/prescriptions/` — create/list
  - `GET /api/rx-upload/prescriptions/<uuid:pk>/` — detail
  - `POST /api/rx-upload/prescriptions/<uuid:prescription_id>/assign/` — assign to current verifier
  - `POST /api/rx-upload/prescriptions/<uuid:prescription_id>/approve/` — approve
  - `POST /api/rx-upload/prescriptions/<uuid:prescription_id>/reject/` — reject
  - `POST /api/rx-upload/prescriptions/<uuid:prescription_id>/clarification/` — request clarification

- Order integration
  - `POST /api/rx-upload/prescriptions/<uuid:prescription_id>/create-order/` — convert approved prescription to `Order` (body may supply mapped `medications` list)
  - `GET /api/rx-upload/prescriptions/<uuid:prescription_id>/orders/` — list orders created for prescription

- Dashboard & workflow
  - `GET /api/rx-upload/dashboard/` — verifier dashboard counts and workload
  - `GET /api/rx-upload/pending/` — list pending prescriptions (supports paginated and non-paginated responses)
  - `POST /api/rx-upload/availability/` — set verifier availability
  - `GET|POST /api/rx-upload/workloads/` — workload endpoints

- Admin & verifier account management
  - `POST /api/rx-upload/admin/verifiers/create/` — create verifier account (Admin)
  - `GET /api/rx-upload/admin/verifiers/` — list verifiers
  - `POST /api/rx-upload/admin/test/email-notification/` — quick test email endpoint

See `rx_upload/urls.py` for the full list and exact path names.

---

## 3. Important modules & responsibilities

- `rx_upload/order_integration.py` — PrescriptionOrderManager
  - Methods:
    - `create_order_from_prescription(prescription_id, medications_data=None, notes="")` — Main transactional function that:
      - Validates prescription status (`approved` required).
      - Ensures customer has address fields.
      - Extracts medication-product mapping (uses `_extract_medications_from_prescription` and `_find_matching_product` to match names to `Product` records).
      - Creates `Order` and `OrderItem`s, reduces product stock, calculates totals.
      - Creates `Invoice` via `Invoice.create_from_order`, populates `InvoiceLineItem`s, calls `invoice.generate_pdf()` and attempts to attach/save.
      - Sends an HTML transactional email to the customer with the invoice attached if available.
    - `_send_order_confirmation_email(order, prescription, invoice)` — builds enterprise-grade HTML and plain-text email content and sends `EmailMultiAlternatives`, attaching PDF (if generated).

- `invoice/models.py` — Invoice model & PDF generator
  - `Invoice` fields: `order` (OneToOne), `invoice_number`, `status`, `issued_date`, `due_date`, `payment_terms`, `subtotal`, `tax_amount`, `shipping_charge`, `discount_amount`, `total_amount`, `amount_paid`, `balance_due`, `notes`, `pdf_file` (FileField), timestamps.
  - `generate_pdf()` uses ReportLab Platypus to render a professional PDF (logo if provided via `settings.INVOICE_LOGO_PATH`, header, metadata, billing/shipping addresses, items table, totals, notes, footer). It returns PDF bytes and tries to save to `pdf_file`.
  - `create_from_order(order)` classmethod creates an `Invoice` linked to an order and returns it.
  - `InvoiceLineItem` model stores item-level details and computes totals.
  - `InvoicePayment` model records payments and calls `invoice.mark_as_paid()` on save.

- `orders/models.py` — Order and OrderItem
  - `Order.create_from_cart(...)` exists for generic cart-based orders.
  - For prescription orders, `PrescriptionOrderManager` creates `Order` using `Order.objects.create(...)` and populates `OrderItem` rows.
  - `Order.calculate_totals()` computes `subtotal`, `tax` (10% example), `coupon_discount`, and `total`.

- `products/enterprise_cache.py` — caching utilities
  - `EnterpriseCacheManager` provides `generate_cache_key`, `get/set` convenience wrappers, and `invalidate_cache_pattern` that attempts a backend-native `delete_pattern` or falls back to inspecting `cache._cache` for LocMemCache.
  - Signal handlers call invalidation helpers on `post_save`/`post_delete` of `Product`, `ProductCategory`, `Brand` etc.

- Tests & scripts
  - `rx_upload/comprehensive_rx_test.py` — enterprise-grade end-to-end tests, covers creating test accounts, sample products, prescription lifecycle, create-order flow and email attachment behavior. The script uses Django test `Client` and obtains JWT token optionally via `/api/token/` if available.
  - `scripts/generate_sample_invoice.py` — convenience script that creates a sample order/invoice and writes a PDF to `generated_invoices/` for manual inspection.

---

## 4. Models referenced (quick overview)

- Prescription & verification
  - `PrescriptionUpload` (rx_upload.models) — core prescription record, contains `customer` (FK to `User`), `medications_prescribed`, `prescription_number`, `verification_status`, `verified_by`, `medications` relation (optional), `customer_notes`, etc.
  - `VerificationActivity` — audit trail for verifier actions (approve/create/reject/etc.).

- Orders & items
  - `Order` — `user` (FK to `User`), `order_number`, `status`, `payment_status`, `payment_method`, `subtotal`, `tax`, `shipping_charge`, `discount`, `total`, `shipping_address` (JSON), `billing_address` (JSON), `notes`.
  - `OrderItem` — `order` (FK), `product` (FK), `variant` (nullable), `quantity`, `price`, `total_price` property.

- Invoices
  - `Invoice` — OneToOne to `Order`, `invoice_number`, amounts, `pdf_file` FileField, `generate_pdf()`.
  - `InvoiceLineItem` — FK to `Invoice`, `product_name`, `quantity`, `unit_price`, `tax_rate`, `discount`, `total_price`.
  - `InvoicePayment` — FK to `Invoice`, `amount`, `payment_method`, `transaction_id`, `payment_date`.

---

## 5. How to run & validate locally

Preconditions:
- Python environment with project dependencies installed (`requirements.txt` should include `reportlab`, Django, DRF, etc.)
- Django settings configured for email sending (for dev you can use `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` to see emails in console)
- Database migrated: `python manage.py migrate`

1. Run the sample invoice generator (quick manual smoke test):

```powershell
python scripts\generate_sample_invoice.py
```

- Output: `generated_invoices/sample_invoice_<invoice_number>.pdf` — open this PDF for layout inspection.

2. Run the comprehensive RX verifier test suite (end-to-end checks):

```powershell
python rx_upload\comprehensive_rx_test.py
```

- The script will create sample users, products, and prescriptions, run through login/assign/approve/create-order, and validate that emails and invoices are produced.
- The script tries to obtain and attach a JWT token for DRF endpoints. If your installation uses session auth only, the script falls back to Django `Client.login()`.

3. Run server and exercise endpoints manually via Postman or curl:
- `POST /api/rx-upload/auth/login/` — obtain session or JWT.
- `GET /api/rx-upload/pending/` — check pending list.
- `POST /api/rx-upload/prescriptions/<id>/approve/` — approve.
- `POST /api/rx-upload/prescriptions/<id>/create-order/` — create order and trigger invoice/email.

4. Check the `Invoice.pdf_file` field in the DB (or inspect the saved file under MEDIA if using file system storage). The `generate_pdf()` function attempts to save `pdf_file` automatically.

---

## 6. Configuration & tuning

- Email settings (Django settings)
  - `DEFAULT_FROM_EMAIL`, `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` — ensure these are set for production email delivery.
  - For dev, use `django.core.mail.backends.console.EmailBackend`.

- Invoice appearance
  - `INVOICE_LOGO_PATH` — if set to a filesystem path accessible by Django, the PDF generator will include the logo in the header.
  - `APP_NAME` — used for header/title in the invoice PDF when present.

- Cache
  - `EnterpriseCacheManager` uses Django `cache` configured in settings. For production, use Redis or Memcached for full `delete_pattern` support.

- ReportLab
  - The PDF generator uses ReportLab Platypus; confirm `reportlab` is installed in your environment: `pip install reportlab`.

---

## 7. Common Troubleshooting

- Django import-time syntax error after editing `invoice/models.py`:
  - Symptom: `IndentationError` or `SyntaxError` prevents `manage.py` commands and server from starting.
  - Fix: Ensure `invoice/models.py` is syntactically valid (the repository already contains a corrected version). Run `python -m py_compile invoice/models.py` to validate.

- Invoice PDF generation returns `None`:
  - The generator logs exceptions and returns `None` on failure; check project logs for the exception trace. Common causes: missing ReportLab, non-readable `INVOICE_LOGO_PATH`, or unexpected shapes in `order` fields.

- Emails not delivered / no attachment:
  - Use console backend to inspect email content locally. If PDF failed to attach, the email path still sends plain HTML; investigate `invoice.generate_pdf()` errors for details.

- Products not found during product matching:
  - The product matching uses `Product.objects.filter(name__icontains=...)` and requires `is_publish=True`. Ensure test products are created with `is_publish=True`.

---

## 8. Tests and CI suggestions

- The `rx_upload/comprehensive_rx_test.py` is a helpful script for local manual/CI runs; add it to CI pipeline as a smoke/integration job after migrations and server readiness checks.
- Add a separate unit test suite for `PrescriptionOrderManager` to cover these cases:
  - Approved prescription with valid mapped products → order + invoice created, PDF generated.
  - Prescription lacking address → expected failure.
  - Product out-of-stock during order creation → skip item and return appropriate message.
  - PDF generation failure gracefully handled (returns `None` and still sends email without attachment).

---

## 9. File map (modified/created during recent work)

- `invoice/models.py` — Reworked Invoice model; PDF generator using ReportLab Platypus; `InvoiceLineItem` and `InvoicePayment` added.
- `rx_upload/order_integration.py` — `PrescriptionOrderManager` service for creating orders from prescriptions and emailing invoices.
- `rx_upload/comprehensive_rx_test.py` — end-to-end verifier + order + invoice test harness.
- `products/enterprise_cache.py` — cache manager with robust invalidation fallback.
- `scripts/generate_sample_invoice.py` — small script to produce `generated_invoices/sample_invoice_*.pdf`.

---

## 10. Next improvements & optional items

- Add unit tests specifically targeting invoice PDF content and structure (e.g., assert table headers, totals, presence of invoice number) using a PDF parser library.
- Add configuration-driven invoice templates (switchable header, colors, localized currency formatting).
- Add retry/queued email sending (via Celery/RQ) for production reliability.
- Improve product matching (fuzzy matching service or mapping table between medication names and product SKUs).
- Add logging metrics and alerts for invoice generation failures.

---

If you'd like, I can:
- commit these docs and open a PR with a summary message,
- run the comprehensive test suite and paste a test report into this doc,
- or extend `scripts/generate_sample_invoice.py` to accept CLI parameters (logo, product counts, tax percentage) for more variations.

