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
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
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

    def action_post(self):
        self.write({"state": "posted"})

    def action_cancel(self):
        self.with_context(allow_invoice_state_change=True).write({"state": "cancelled"})

    def action_reset_to_draft(self):
        self.with_context(allow_invoice_state_change=True).write({"state": "draft"})


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
    amount = fields.Monetary(
        string="Payment Amount",
        currency_field="currency_id",
        required=True,
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
