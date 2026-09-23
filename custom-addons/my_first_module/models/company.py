from odoo import api, fields, models


class Company(models.Model):
    _name = "my.first.company"
    _description = "Company"

    name = fields.Char(
        string="Company Name",
        required=True,
    )
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    website = fields.Char(string="Website")
    industry = fields.Char(string="Industry")
    street = fields.Char(string="Street")
    city = fields.Char(string="City")
    state = fields.Char(string="State")
    zip = fields.Char(string="ZIP Code")
    country = fields.Char(string="Country")
    notes = fields.Text(string="Notes")
    customer_ids = fields.One2many(
        "my.first.customer",
        "company_id",
        string="Customers",
    )
    customer_count = fields.Integer(compute="_compute_customer_counts")
    active_customer_count = fields.Integer(compute="_compute_customer_counts")

    @api.depends("customer_ids", "customer_ids.status")
    def _compute_customer_counts(self):
        for company in self:
            company.customer_count = len(company.customer_ids)
            company.active_customer_count = len(
                company.customer_ids.filtered(
                    lambda customer: customer.status == "active"
                )
            )
