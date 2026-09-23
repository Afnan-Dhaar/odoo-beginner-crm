from odoo import api, fields, models


class CustomerTag(models.Model):
    _name = "my.first.customer.tag"
    _description = "Customer Tag"

    name = fields.Char(
        string="Tag Name",
        required=True,
    )
    color = fields.Integer(string="Color", default=0)
    active = fields.Boolean(string="Active", default=True)

    customer_ids = fields.Many2many(
        "my.first.customer",
        "customer_tag_rel",
        "tag_id",
        "customer_id",
        string="Customers",
    )
    customer_count = fields.Integer(compute="_compute_customer_count")

    @api.depends("customer_ids")
    def _compute_customer_count(self):
        for tag in self:
            tag.customer_count = len(tag.customer_ids)
