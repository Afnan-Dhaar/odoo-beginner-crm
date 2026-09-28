import base64

# pyrefly: ignore [missing-import]
from odoo.exceptions import ValidationError

from odoo import api, fields, models


class CustomerDocument(models.Model):
    _name = "my.first.customer.document"
    _description = "Customer Document"
    _order = "created_at desc, id desc"

    name = fields.Char(string="Document Name", required=True)
    document_type = fields.Selection(
        [
            ("proposal", "Proposal"),
            ("contract", "Contract"),
            ("receipt", "Receipt"),
            ("document", "Document"),
            ("other", "Other"),
        ],
        string="Document Type",
        default="document",
        required=True,
    )
    file = fields.Binary(string="File", required=True, attachment=True)
    file_name = fields.Char(string="File Name")
    file_size = fields.Integer(
        string="File Size (bytes)",
        compute="_compute_file_size",
        store=True,
    )
    customer_id = fields.Many2one(
        "my.first.customer",
        string="Customer",
        required=True,
        ondelete="cascade",
    )
    invoice_id = fields.Many2one(
        "my.first.customer.invoice",
        string="Invoice",
        ondelete="set null",
        domain="[('customer_id', '=', customer_id)]",
    )
    description = fields.Text(string="Description")
    created_at = fields.Datetime(
        string="Uploaded On",
        default=fields.Datetime.now,
        readonly=True,
    )
    created_by = fields.Many2one(
        "res.users",
        string="Uploaded By",
        default=lambda self: self.env.user,
        readonly=True,
    )

    @api.depends("file")
    def _compute_file_size(self):
        for doc in self:
            if doc.file:
                try:
                    doc.file_size = len(base64.b64decode(doc.file))
                except Exception:
                    doc.file_size = len(doc.file)
            else:
                doc.file_size = 0

    @api.onchange("file_name")
    def _onchange_file_name(self):
        if self.file_name and not self.name:
            self.name = self.file_name

    @api.onchange("invoice_id")
    def _onchange_invoice_id(self):
        if self.invoice_id and not self.customer_id:
            self.customer_id = self.invoice_id.customer_id

    @api.constrains("customer_id", "invoice_id")
    def _check_customer_invoice_match(self):
        for doc in self:
            if doc.invoice_id and doc.invoice_id.customer_id != doc.customer_id:
                raise ValidationError(
                    "The selected invoice does not belong to the selected customer."
                )
