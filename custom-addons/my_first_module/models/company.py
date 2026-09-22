from odoo import fields, models


class Company(models.Model):
    _name = "my.first.company"
    _description = "Company"

    name = fields.Char(
        string="Company Name",
        required=True,
    )
    customer_ids = fields.One2many(
        "my.first.customer",
        "company_id",
        string="Customers",
    )
