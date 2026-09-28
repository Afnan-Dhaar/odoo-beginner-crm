from odoo import fields, models


class CustomerTimeline(models.Model):
    _name = "my.first.customer.timeline"
    _description = "Customer Timeline"
    _order = "event_date desc, id desc"

    customer_id = fields.Many2one(
        "my.first.customer",
        string="Customer",
        required=True,
        ondelete="cascade",
    )
    event_type = fields.Selection(
        [
            ("note", "Note"),
            ("activity", "Activity"),
            ("invoice", "Invoice"),
            ("payment", "Payment"),
            ("document", "Document"),
            ("email", "Email"),
        ],
        string="Event Type",
        required=True,
    )
    title = fields.Char(string="Title", required=True)
    description = fields.Text(string="Description")
    event_date = fields.Datetime(string="Date", required=True)
    source_ref = fields.Char(string="Source", readonly=True)
