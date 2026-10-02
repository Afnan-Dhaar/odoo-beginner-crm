# pyrefly: ignore [missing-import]
from odoo.exceptions import ValidationError

from odoo import api, fields, models


class CustomerInvoice(models.Model):
    _name = "my.first.customer.invoice"
    _description = "Customer Invoice"
    _order = "invoice_date desc, id desc"

    name = fields.Char(
        string="Invoice Number",
        required=True,
        copy=False,
        readonly=True,
        default="New",
    )
    customer_id = fields.Many2one(
        "my.first.customer",
        string="Customer",
        required=True,
        ondelete="cascade",
    )
    company_currency_id = fields.Many2one(
        "res.currency",
        string="Company Currency",
        default=lambda self: self.env.company.currency_id,
        compute="_compute_company_currency",
        store=True,
        precompute=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self._default_currency_id(),
    )
    exchange_rate = fields.Float(
        string="Exchange Rate",
        digits=(12, 6),
        default=1.0,
        required=True,
        compute="_compute_exchange_rate",
        store=True,
        readonly=False,
        precompute=True,
    )
    is_foreign_currency = fields.Boolean(
        string="Is Foreign Currency",
        compute="_compute_is_foreign_currency",
        store=True,
    )
    invoice_date = fields.Date(
        string="Invoice Date",
        required=True,
        default=fields.Date.today,
    )
    due_date = fields.Date(string="Due Date")
    amount_total = fields.Monetary(
        string="Total Amount",
        currency_field="currency_id",
        required=True,
    )
    payment_ids = fields.One2many(
        "my.first.customer.payment",
        "invoice_id",
        string="Payments",
    )
    document_ids = fields.One2many(
        "my.first.customer.document",
        "invoice_id",
        string="Documents",
    )
    document_count = fields.Integer(
        string="Document Count",
        compute="_compute_document_count",
    )
    email_ids = fields.One2many(
        "my.first.customer.email",
        "invoice_id",
        string="Emails",
    )
    email_count = fields.Integer(
        string="Email Count",
        compute="_compute_email_count",
    )
    amount_paid = fields.Monetary(
        string="Amount Paid",
        currency_field="currency_id",
        compute="_compute_payment_amounts",
        store=True,
    )
    amount_due = fields.Monetary(
        string="Amount Due",
        currency_field="currency_id",
        compute="_compute_payment_amounts",
        store=True,
    )
    amount_total_company = fields.Monetary(
        string="Total (Company)",
        currency_field="company_currency_id",
        compute="_compute_company_amounts",
        store=True,
    )
    amount_paid_company = fields.Monetary(
        string="Paid (Company)",
        currency_field="company_currency_id",
        compute="_compute_company_amounts",
        store=True,
    )
    amount_due_company = fields.Monetary(
        string="Due (Company)",
        currency_field="company_currency_id",
        compute="_compute_company_amounts",
        store=True,
    )
    payment_status = fields.Selection(
        [
            ("not_paid", "Not Paid"),
            ("partially_paid", "Partially Paid"),
            ("paid", "Paid"),
        ],
        string="Payment Status",
        compute="_compute_payment_status",
        store=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("posted", "Posted"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        required=True,
        default="draft",
    )
    notes = fields.Text(string="Notes")

    def _default_currency_id(self):
        customer_id = self.env.context.get("default_customer_id")
        if customer_id:
            customer = self.env["my.first.customer"].browse(customer_id)
            if customer.preferred_currency_id:
                return customer.preferred_currency_id
        return self.env.company.currency_id

    @api.onchange("customer_id")
    def _onchange_customer_id(self):
        if self.customer_id and self.customer_id.preferred_currency_id:
            self.currency_id = self.customer_id.preferred_currency_id

    @api.depends_context("company")
    def _compute_company_currency(self):
        comp_curr = self.env.company.currency_id
        for invoice in self:
            invoice.company_currency_id = comp_curr

    @api.depends("currency_id", "company_currency_id")
    def _compute_is_foreign_currency(self):
        for invoice in self:
            comp_curr = invoice.company_currency_id or self.env.company.currency_id
            invoice.is_foreign_currency = bool(
                invoice.currency_id and invoice.currency_id != comp_curr
            )

    @api.depends("currency_id", "invoice_date")
    def _compute_exchange_rate(self):
        for invoice in self:
            comp_curr = invoice.company_currency_id or self.env.company.currency_id
            if not invoice.currency_id or invoice.currency_id == comp_curr:
                invoice.exchange_rate = 1.0
            else:
                date = invoice.invoice_date or fields.Date.today()
                rate = invoice.currency_id._get_conversion_rate(
                    invoice.currency_id, comp_curr, self.env.company, date
                )
                invoice.exchange_rate = rate or 1.0

    @api.depends(
        "amount_total",
        "amount_paid",
        "amount_due",
        "exchange_rate",
        "currency_id",
        "company_currency_id",
    )
    def _compute_company_amounts(self):
        for invoice in self:
            comp_curr = invoice.company_currency_id or self.env.company.currency_id
            is_foreign = bool(invoice.currency_id and invoice.currency_id != comp_curr)
            rate = invoice.exchange_rate if is_foreign else 1.0
            if not rate or rate <= 0:
                rate = 1.0
            invoice.amount_total_company = comp_curr.round(invoice.amount_total * rate)
            invoice.amount_paid_company = comp_curr.round(invoice.amount_paid * rate)
            invoice.amount_due_company = (
                invoice.amount_total_company - invoice.amount_paid_company
            )

    @api.depends("payment_ids.amount")
    def _compute_payment_amounts(self):
        for invoice in self:
            invoice.amount_paid = sum(invoice.payment_ids.mapped("amount"))
            invoice.amount_due = invoice.amount_total - invoice.amount_paid

    @api.depends("amount_total", "amount_paid")
    def _compute_payment_status(self):
        for invoice in self:
            if not invoice.amount_paid:
                invoice.payment_status = "not_paid"
            elif invoice.amount_due <= 0:
                invoice.payment_status = "paid"
            else:
                invoice.payment_status = "partially_paid"

    @api.constrains("amount_total")
    def _check_amount_total(self):
        for invoice in self:
            if invoice.amount_total <= 0:
                raise ValidationError("Invoice total must be greater than zero.")

    @api.constrains("exchange_rate")
    def _check_exchange_rate(self):
        for invoice in self:
            if invoice.exchange_rate <= 0:
                raise ValidationError("Exchange rate must be greater than zero.")

    @api.constrains("invoice_date", "due_date")
    def _check_due_date(self):
        for invoice in self:
            if invoice.due_date and invoice.due_date < invoice.invoice_date:
                raise ValidationError("Due date cannot be before the invoice date.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "my.first.customer.invoice"
                )
        return super().create(vals_list)

    def write(self, vals):
        if (
            self.filtered(lambda invoice: invoice.state == "posted")
            and vals
            and not self.env.context.get("allow_invoice_state_change")
        ):
            raise ValidationError("Posted invoices cannot be edited.")
        return super().write(vals)

    @api.depends("document_ids")
    def _compute_document_count(self):
        for invoice in self:
            invoice.document_count = len(invoice.document_ids)

    def action_view_documents(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Documents - {self.name}",
            "res_model": "my.first.customer.document",
            "view_mode": "list,form",
            "domain": [("invoice_id", "=", self.id)],
            "context": {
                "default_customer_id": self.customer_id.id,
                "default_invoice_id": self.id,
            },
        }

    @api.depends("email_ids")
    def _compute_email_count(self):
        for invoice in self:
            invoice.email_count = len(invoice.email_ids)

    def action_view_emails(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Emails - {self.name}",
            "res_model": "my.first.customer.email",
            "view_mode": "list,form",
            "domain": [("invoice_id", "=", self.id)],
            "context": {
                "default_customer_id": self.customer_id.id,
                "default_invoice_id": self.id,
                "default_recipient": self.customer_id.email,
            },
        }

    def action_send_email(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Compose Email - {self.name}",
            "res_model": "my.first.customer.email",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_customer_id": self.customer_id.id,
                "default_invoice_id": self.id,
                "default_recipient": self.customer_id.email,
                "default_subject": f"Invoice {self.name} - {self.customer_id.name}",
                "default_sender": self.env.user.email or self.env.user.name,
                "default_direction": "outgoing",
                "default_state": "sent",
            },
        }

    def action_post(self):
        self.write({"state": "posted"})

    def action_cancel(self):
        self.with_context(allow_invoice_state_change=True).write({"state": "cancelled"})

    def action_reset_to_draft(self):
        self.with_context(allow_invoice_state_change=True).write({"state": "draft"})

    def action_print_invoice(self):
        self.ensure_one()
        return self.env.ref(
            "my_first_module.action_report_customer_invoice"
        ).report_action(self)


class CustomerPayment(models.Model):
    _name = "my.first.customer.payment"
    _description = "Customer Payment"
    _order = "payment_date desc, id desc"

    invoice_id = fields.Many2one(
        "my.first.customer.invoice",
        string="Invoice",
        required=True,
        ondelete="cascade",
    )
    customer_id = fields.Many2one(
        related="invoice_id.customer_id",
        string="Customer",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        related="invoice_id.currency_id",
        string="Currency",
        readonly=True,
    )
    company_currency_id = fields.Many2one(
        related="invoice_id.company_currency_id",
        string="Company Currency",
        readonly=True,
    )
    amount = fields.Monetary(
        string="Payment Amount",
        currency_field="currency_id",
        required=True,
    )
    amount_company = fields.Monetary(
        string="Payment (Company)",
        currency_field="company_currency_id",
        compute="_compute_amount_company",
        store=True,
    )
    payment_date = fields.Date(
        string="Payment Date",
        required=True,
        default=fields.Date.today,
    )
    payment_method = fields.Selection(
        [
            ("cash", "Cash"),
            ("bank", "Bank Transfer"),
            ("card", "Card"),
            ("other", "Other"),
        ],
        string="Payment Method",
        required=True,
        default="bank",
    )
    reference = fields.Char(string="Payment Reference")
    notes = fields.Text(string="Notes")

    @api.depends(
        "amount",
        "invoice_id.exchange_rate",
        "invoice_id.currency_id",
        "invoice_id.company_currency_id",
    )
    def _compute_amount_company(self):
        for payment in self:
            comp_curr = payment.company_currency_id or self.env.company.currency_id
            inv = payment.invoice_id
            is_foreign = bool(inv.currency_id and inv.currency_id != comp_curr)
            rate = inv.exchange_rate if is_foreign else 1.0
            payment.amount_company = comp_curr.round(payment.amount * (rate or 1.0))

    @api.model_create_multi
    def create(self, vals_list):
        invoice_ids = {
            vals.get("invoice_id") for vals in vals_list if vals.get("invoice_id")
        }
        cancelled_invoices = (
            self.env["my.first.customer.invoice"]
            .browse(list(invoice_ids))
            .filtered(lambda invoice: invoice.state == "cancelled")
        )
        if cancelled_invoices:
            raise ValidationError("Cancelled invoices cannot receive payments.")
        return super().create(vals_list)

    def write(self, vals):
        invoices = self.mapped("invoice_id")
        if vals.get("invoice_id"):
            invoices |= self.env["my.first.customer.invoice"].browse(vals["invoice_id"])
        if invoices.filtered(lambda invoice: invoice.state == "cancelled"):
            raise ValidationError("Cancelled invoices cannot receive payments.")
        return super().write(vals)

    @api.constrains("amount", "invoice_id")
    def _check_payment_amount(self):
        for payment in self:
            if payment.amount <= 0:
                raise ValidationError("Payment amount must be greater than zero.")
            other_payments = payment.invoice_id.payment_ids - payment
            if (
                sum(other_payments.mapped("amount")) + payment.amount
                > payment.invoice_id.amount_total
            ):
                raise ValidationError(
                    "Payments cannot be greater than the invoice total."
                )
