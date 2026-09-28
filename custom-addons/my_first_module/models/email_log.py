# pyrefly: ignore [missing-import]
from odoo.exceptions import ValidationError

from odoo import api, fields, models


class CustomerEmail(models.Model):
    _name = "my.first.customer.email"
    _description = "Customer Email Log"
    _order = "date desc, id desc"

    subject = fields.Char(string="Subject", required=True)
    customer_id = fields.Many2one(
        "my.first.customer",
        string="Customer",
        required=True,
        ondelete="cascade",
    )
    sender = fields.Char(
        string="From",
        required=True,
        default=lambda self: self.env.user.email or self.env.user.name,
    )
    recipient = fields.Char(string="To", required=True)
    cc = fields.Char(string="Cc")
    body = fields.Html(string="Message", required=True, sanitize=True)
    direction = fields.Selection(
        [
            ("outgoing", "Outgoing / Sent"),
            ("incoming", "Incoming / Received"),
        ],
        string="Direction",
        default="outgoing",
        required=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("received", "Received"),
        ],
        string="Status",
        default="sent",
        required=True,
    )
    date = fields.Datetime(
        string="Date",
        default=fields.Datetime.now,
        required=True,
    )
    invoice_id = fields.Many2one(
        "my.first.customer.invoice",
        string="Invoice",
        ondelete="set null",
        domain="[('customer_id', '=', customer_id)]",
    )
    author_id = fields.Many2one(
        "res.users",
        string="Logged By",
        default=lambda self: self.env.user,
        readonly=True,
    )

    @api.onchange("customer_id")
    def _onchange_customer_id(self):
        if self.customer_id and not self.recipient:
            self.recipient = self.customer_id.email

    @api.onchange("invoice_id")
    def _onchange_invoice_id(self):
        if self.invoice_id and not self.customer_id:
            self.customer_id = self.invoice_id.customer_id
        if self.invoice_id and not self.subject:
            self.subject = f"Invoice {self.invoice_id.name}"

    @api.constrains("customer_id", "invoice_id")
    def _check_customer_invoice_match(self):
        for record in self:
            if record.invoice_id and record.invoice_id.customer_id != record.customer_id:
                raise ValidationError(
                    "The selected invoice does not belong to the selected customer."
                )

    @api.constrains("recipient")
    def _check_recipient_email(self):
        for record in self:
            if record.recipient and "@" not in record.recipient:
                raise ValidationError("Please enter a valid recipient email address.")
