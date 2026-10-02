# pyrefly: ignore [missing-import]
from odoo import api, fields, models


class CrmDashboard(models.Model):
    _name = "my.first.crm.dashboard"
    _description = "CRM Dashboard"

    name = fields.Char(default="CRM Dashboard", readonly=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        compute="_compute_kpis",
    )
    customer_count = fields.Integer(compute="_compute_kpis")
    active_customer_count = fields.Integer(compute="_compute_kpis")
    open_activity_count = fields.Integer(compute="_compute_kpis")
    overdue_activity_count = fields.Integer(compute="_compute_kpis")
    unpaid_invoice_count = fields.Integer(compute="_compute_kpis")
    outstanding_amount = fields.Monetary(
        string="Outstanding Amount",
        currency_field="currency_id",
        compute="_compute_kpis",
    )
    document_count = fields.Integer(
        string="Documents",
        compute="_compute_kpis",
    )
    email_count = fields.Integer(
        string="Emails",
        compute="_compute_kpis",
    )
    total_invoiced_amount = fields.Monetary(
        string="Total Invoiced",
        currency_field="currency_id",
        compute="_compute_kpis",
    )
    total_paid_amount = fields.Monetary(
        string="Total Collected",
        currency_field="currency_id",
        compute="_compute_kpis",
    )
    recent_activity_ids = fields.Many2many(
        "my.first.customer.activity",
        compute="_compute_kpis",
    )
    upcoming_activity_ids = fields.Many2many(
        "my.first.customer.activity",
        compute="_compute_kpis",
    )
    recent_email_ids = fields.Many2many(
        "my.first.customer.email",
        compute="_compute_kpis",
    )
    recent_document_ids = fields.Many2many(
        "my.first.customer.document",
        compute="_compute_kpis",
    )

    @api.depends()
    def _compute_kpis(self):
        Customer = self.env["my.first.customer"]
        Activity = self.env["my.first.customer.activity"]
        Invoice = self.env["my.first.customer.invoice"]
        Document = self.env["my.first.customer.document"]
        Email = self.env["my.first.customer.email"]

        customer_count = Customer.search_count([])
        active_customer_count = Customer.search_count([("status", "=", "active")])
        open_activity_count = Activity.search_count([("status", "=", "planned")])
        overdue_activity_count = Activity.search_count(
            [
                ("status", "=", "planned"),
                ("due_date", "<", fields.Date.today()),
            ]
        )
        unpaid_invoices = Invoice.search(
            [("payment_status", "in", ["not_paid", "partially_paid"])]
        )
        non_cancelled_invoices = Invoice.search([("state", "!=", "cancelled")])
        total_invoiced_amount = sum(
            non_cancelled_invoices.mapped("amount_total_company")
        )
        total_paid_amount = sum(non_cancelled_invoices.mapped("amount_paid_company"))

        document_count = Document.search_count([])
        email_count = Email.search_count([])

        recent_activities = Activity.search(
            [], order="create_date desc, id desc", limit=5
        )
        upcoming_activities = Activity.search(
            [
                ("status", "=", "planned"),
                ("due_date", ">=", fields.Date.today()),
            ],
            order="due_date, id",
            limit=5,
        )
        recent_emails = Email.search([], order="date desc, id desc", limit=5)
        recent_documents = Document.search(
            [], order="created_at desc, id desc", limit=5
        )

        for dashboard in self:
            dashboard.currency_id = self.env.company.currency_id
            dashboard.customer_count = customer_count
            dashboard.active_customer_count = active_customer_count
            dashboard.open_activity_count = open_activity_count
            dashboard.overdue_activity_count = overdue_activity_count
            dashboard.unpaid_invoice_count = len(unpaid_invoices)
            dashboard.outstanding_amount = sum(
                unpaid_invoices.mapped("amount_due_company")
            )
            dashboard.document_count = document_count
            dashboard.email_count = email_count
            dashboard.total_invoiced_amount = total_invoiced_amount
            dashboard.total_paid_amount = total_paid_amount
            dashboard.recent_activity_ids = recent_activities
            dashboard.upcoming_activity_ids = upcoming_activities
            dashboard.recent_email_ids = recent_emails
            dashboard.recent_document_ids = recent_documents

    def _open_action(self, model, name):
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model,
            "view_mode": "list,form",
            "target": "current",
        }

    def action_open_customers(self):
        return self._open_action("my.first.customer", "Customers")

    def action_open_active_customers(self):
        action = self._open_action("my.first.customer", "Active Customers")
        action["domain"] = [("status", "=", "active")]
        return action

    def action_open_activities(self):
        return self._open_action("my.first.customer.activity", "Activities")

    def action_open_overdue_activities(self):
        action = self._open_action("my.first.customer.activity", "Overdue Activities")
        action["domain"] = [
            ("status", "=", "planned"),
            ("due_date", "<", fields.Date.today()),
        ]
        return action

    def action_open_unpaid_invoices(self):
        action = self._open_action("my.first.customer.invoice", "Unpaid Invoices")
        action["domain"] = [("payment_status", "in", ["not_paid", "partially_paid"])]
        return action

    def action_open_paid_invoices(self):
        action = self._open_action("my.first.customer.invoice", "Paid Invoices")
        action["domain"] = [("payment_status", "=", "paid")]
        return action

    def action_open_documents(self):
        return self._open_action("my.first.customer.document", "Documents")

    def action_open_emails(self):
        return self._open_action("my.first.customer.email", "Email Communications")

    def action_create_customer(self):
        return {
            "type": "ir.actions.act_window",
            "name": "New Customer",
            "res_model": "my.first.customer",
            "view_mode": "form",
            "target": "current",
        }

    def action_create_activity(self):
        return {
            "type": "ir.actions.act_window",
            "name": "New Activity",
            "res_model": "my.first.customer.activity",
            "view_mode": "form",
            "target": "current",
        }

    def action_create_invoice(self):
        return {
            "type": "ir.actions.act_window",
            "name": "New Invoice",
            "res_model": "my.first.customer.invoice",
            "view_mode": "form",
            "target": "current",
        }

    def action_create_document(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Upload Document",
            "res_model": "my.first.customer.document",
            "view_mode": "form",
            "target": "new",
        }

    def action_send_email(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Compose Email",
            "res_model": "my.first.customer.email",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_direction": "outgoing",
                "default_state": "sent",
            },
        }
