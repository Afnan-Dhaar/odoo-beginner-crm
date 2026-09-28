# Odoo Beginner CRM

A beginner-friendly CRM application built as a custom Odoo 19 addon.

## Features

- Customers, companies, tags, and customer notes
- Customer attachments (proposals, contracts, receipts, documents) linked to customers and invoices
- Email communication log with compose actions and timeline tracking
- Activities with due dates, overdue tracking, and calendar view
- Customer invoices and payments with validation rules
- CRM dashboard with KPI cards and follow-up lists
- Customer, activity, and invoice graph/pivot reports
- CRM User and CRM Manager security groups
- Automated Odoo tests and GitHub Actions CI

## Local Setup

From `C:\odoo-dev`, activate the virtual environment and upgrade the module:

```powershell
.\venv\Scripts\python.exe odoo\odoo-bin -c odoo.conf -d odoo_dev -u my_first_module --stop-after-init
```

Start the server:

```powershell
.\venv\Scripts\python.exe odoo\odoo-bin -c odoo.conf
```

Open `http://localhost:8069` and assign yourself the **CRM Manager** group under **Settings > Users & Companies > Users**.

## Tests

Run the CRM tests locally:

```powershell
.\venv\Scripts\python.exe odoo\odoo-bin -c odoo.conf -d odoo_dev -u my_first_module --test-enable --test-tags=/my_first_module --stop-after-init
```

GitHub Actions runs the same CRM test suite on pushes and pull requests to `main`.

## Demo Data

Demo records are loaded only when the database is created with Odoo demo data enabled. They include sample companies, customers, tags, notes, activities, invoices, and payments.

## Security

- **CRM User**: standard CRM access, own activity visibility, and read-only invoices/payments.
- **CRM Manager**: full CRM access, including invoices and payments.

Do not commit `odoo.conf`, PostgreSQL credentials, the `venv` directory, or the Odoo framework checkout. These are excluded by the root `.gitignore`.