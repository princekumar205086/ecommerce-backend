# Products App — MRP Integration and Improvements

This document describes the changes made to the `products` app to add MRP support, the verification and tests run, and recommended next steps to make the app production/enterprise-ready.

## Summary of changes

1. Added `mrp` (Decimal) field to the following models:
   - `Product` (`products.models.Product.mrp`) — product-level MRP (default 0.00 means not set)
   - `ProductVariant` (`products.models.ProductVariant.mrp`) — variant-level MRP (falls back to product.mrp)
   - `SupplierProductPrice` (`products.models.SupplierProductPrice.mrp`) — supplier-listed MRP

2. Added `ProductVariant.effective_mrp` property which returns the variant MRP (if > 0) or the parent product MRP.

3. Added a pre-save validation (`validate_mrp_vs_price`) that ensures MRP is not less than the price when MRP is explicitly set (i.e., mrp > 0). This prevents accidental invalid data.

4. Updated serializers to include `mrp` and validate `mrp >= price` on create/update for variants and supplier prices.

5. Updated Django admin list displays to show `mrp` for `Product`, `ProductVariant`, and `SupplierProductPrice`.

6. Created and applied a Django migration: `products.0012_product_mrp_productvariant_mrp_and_more`.

7. Updated tests in `products/tests.py` to match the current variant shape (size/weight fields removed previously) and to work with `product_variant` when creating supplier prices.

8. Ran the full `products` app test suite — all tests passed locally.


## Files changed (high-level)

- products/models.py — add `mrp` fields, validation, effective_mrp property
- products/serializers.py — include `mrp` in Product & ProductVariant serializers; validate `mrp >= price` for relevant serializers
- products/admin.py — show `mrp` in admin list views
- products/tests.py — adapt tests to variant shape and supplier price creation
- PRODUCTS_MRP_UPDATE.md — this documentation file
- Django migration `products/migrations/0012_product_mrp_productvariant_mrp_and_more.py` (auto-created)


## How to run locally (what I ran here)

Commands used in this workspace (powershell):

```powershell
# Create migrations for the products app (adds mrp columns)
python manage.py makemigrations products
python manage.py migrate

# Run only the products test suite
python manage.py test products
```

All tests under the `products` app passed in my run.


## Notes on behavior

- A default `mrp` of `0.00` is treated as "unset". Validation only runs if `mrp > 0`.
- When showing prices on the frontend, prefer to expose both `price` and `mrp` so the UI can render discounts or badges.
- `effective_mrp` on a variant returns the variant `mrp` if explicitly set (> 0), otherwise the product `mrp`.


## Recommendations & next steps to make this enterprise-ready

These are suggestions to harden and professionalize the `products` app further.

1. Price & MRP history
   - Maintain a `PriceHistory` model capturing changes to `price` and `mrp` with timestamps and user who changed it. This helps audits and rollback.

2. Validation & business rules
   - Enforce currency & rounding rules and store currency info per product or per-store.
   - Add tax and discount representation (e.g., tax_inclusive flag, tax rate references).

3. API design
   - Add API versioning (v1/v2) and OpenAPI schema generation (drf_spectacular / drf-yasg) with examples for price fields.
   - Add serializers for read vs write (list vs detail) to avoid over-fetching.

4. Search & indexing
   - Index price and mrp fields in your search index (Elasticsearch / Meilisearch) and keep them updated in background tasks.
   - Add materialized denormalized fields for frequently filtered combos (e.g. `min_variant_price`).

5. Performance & caching
   - Use Redis for caching product list responses and invalidate on changes.
   - Use `prefetch_related` and `select_related` in views to reduce DB queries for variants and prices.

6. Data integrity & migrations
   - Add database-level constraints if you need strict enforcement (e.g., check constraint mrp >= price when mrp>0). Not all DBs support conditional checks—consider triggers or application-level checks.
   - Add migration tests to CI to ensure schema changes are compatible.

7. Tests & CI
   - Add tests for price history, bulk imports, and edge cases (zero price, negative values, very large values).
   - Run tests in CI (GitHub Actions) using a matrix of Python/Django versions and run lint/static analysis.

8. Security & roles
   - Ensure only authorized roles (admins or suppliers with certain permissions) can set MRP/price. Use object-level permissions for supplier scopes.

9. Observability & monitoring
   - Emit metrics when prices change (audit logs, Prometheus metrics) and add an alert if suspicious changes occur (many price decreases).

10. UX considerations
   - Decide how to display MRP vs selling price: strike-through MRP, percentage-off badges, or both.
   - Consider localization (currency, decimal marks) and include currency in API responses.

11. Bulk operations & import/export
   - Implement CSV/XLSX import for price updates with validation, previews, and dry-run mode.

12. Documentation & developer experience
   - Maintain a short developer README for the `products` app with model diagrams, important queries, and common maintenance commands.
   - Add type hints and mypy checks to the module to catch mistakes early.


## Suggested low-risk follow-ups (I can implement)

- Add a `PriceHistory` model and automatic logging when `price` or `mrp` changes.
- Add API docs (OpenAPI/Swagger) for the products endpoints.
- Add DB-level constraint for `mrp >= price` where supported.
- Add `currency` field to Product (if multi-currency required) and update tests accordingly.

If you want, I can implement any of the above follow-ups next. Tell me which one to prioritize.


## Commit & push

I have staged and committed the code changes locally in this workspace. If you'd like, I can also push these commits to the repository remote (GitHub) — I will need the remote configured and permissions to push. If your remote is set to `origin` and credentials are available in your environment, I will push to the current branch.


---

End of document.
