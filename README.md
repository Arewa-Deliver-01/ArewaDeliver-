# ArewaDeliver (Option 2 - Unified Auth Frontend)

This package contains a full frontend prototype for a unified login/register system with separate dashboards for Customer, Vendor and Rider.

Features:
- Register with role (customer/vendor/rider)
- Login (demo using localStorage)
- Role-based dashboards and pages: profile, wallet, KYC
- Demo wallet & transactions stored in the browser (localStorage)
- Prepared `app.js` placeholder to call a real backend API (replace API_BASE)

Next steps:
- Implement backend authentication (Flask + DB) and connect to Render
- Integrate payments (OPay, PalmPay) for vendor/rider registration fees
- Migrate wallet to server-side DB (Postgres)
