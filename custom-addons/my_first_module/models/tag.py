from odoo import fields, models


class CustomerTag(models.Model):
    _name = "my.first.customer.tag"
    _description = "Customer Tag"

    name = fields.Char(
        string="Tag Name",
        required=True,
    )

    customer_ids = fields.Many2many(
        "my.first.customer",
        "customer_tag_rel",
        "tag_id",
        "customer_id",
        string="Customers",
    )
