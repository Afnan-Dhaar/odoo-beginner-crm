from odoo.exceptions import ValidationError

from odoo import api, fields, models


class Customer(models.Model):
    _name = "my.first.customer"
    _description = "Customer"

    reference = fields.Char(
        string="Reference", required=True, copy=False, readonly=True, default="New"
    )

    name = fields.Char(string="Customer Name", required=True)
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")

    company_id = fields.Many2one(
        "my.first.company",
        string="Company",
    )

    company_name = fields.Char(
        string="Company Name",
        related="company_id.name",
        store=True,
    )

    note_ids = fields.One2many(
        "my.first.customer.note",
        "customer_id",
        string="Notes",
    )

    activity_ids = fields.One2many(
        "my.first.customer.activity",
        "customer_id",
        string="Activities",
    )

    invoice_ids = fields.One2many(
        "my.first.customer.invoice",
        "customer_id",
        string="Invoices",
    )

    tag_ids = fields.Many2many(
        "my.first.customer.tag",
        "customer_tag_rel",
        "customer_id",
        "tag_id",
        string="Tags",
    )

    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
    )

    status = fields.Selection(
        [
            ("new", "New"),
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
        string="Status",
        default="new",
        required=True,
    )

    last_updated = fields.Datetime(
        string="Last Updated",
        readonly=True,
    )

    created_at = fields.Datetime(
        string="Created At",
        readonly=True,
    )

    @api.depends("reference", "name")
    def _compute_display_name(self):
        for customer in self:
            customer.display_name = f"{customer.reference} - {customer.name}"

    @api.constrains("email")
    def _check_email(self):
        for customer in self:
            if customer.email and "@" not in customer.email:
                raise ValidationError("Please enter a valid email address.")

    @api.onchange("email")
    def _onchange_email(self):
        if self.email and "@" in self.email:
            self.status = "active"

    def action_activate(self):
        for customer in self:
            customer.status = "active"

    def action_deactivate(self):
        for customer in self:
            customer.status = "inactive"

    def action_test_recordset(self):
        print("Number of records:", len(self))

        for customer in self:
            print("Customer:", customer.name)
            print("Record ID:", customer.id)

    def action_search_active_customers(self):
        active_customers = self.env["my.first.customer"].search(
            [("status", "=", "active")]
        )

        print("Active customers:", len(active_customers))

        for customer in active_customers:
            print("Active Customer:", customer.name)

    def action_search_active_company_customers(self):
        customers = self.env["my.first.customer"].search(
            [
                ("status", "=", "active"),
                ("company_id.name", "=", "Aseef Technologies"),
            ]
        )

        print("Matching customers:", len(customers))

        for customer in customers:
            print("Customer:", customer.name)

    def action_search_new_or_inactive_customers(self):
        customers = self.env["my.first.customer"].search(
            [
                "|",
                ("status", "=", "new"),
                ("status", "=", "inactive"),
            ]
        )

        print("New OR Inactive customers:", len(customers))

        for customer in customers:
            print("Customer:", customer.name, "| Status:", customer.status)

    def action_search_active_company_or_new(self):
        customers = self.env["my.first.customer"].search(
            [
                "|",
                "&",
                ("status", "=", "active"),
                ("company_id.name", "=", "Aseef Technologies"),
                ("status", "=", "new"),
            ]
        )

        print("Active + Aseef OR New customers:", len(customers))

        for customer in customers:
            print(
                "Customer:",
                customer.name,
                "| Status:",
                customer.status,
                "| Company:",
                customer.company_name,
            )

    # def action_test_multiple_create(self):
    #     customers = self.create(
    #         [
    #             {
    #                 "name": "Multi Create A",
    #                 "email": "multi.a@test.com",
    #                 "phone": "3333333333",
    #             },
    #             {
    #                 "name": "Multi Create B",
    #                 "email": "multi.b@test.com",
    #                 "phone": "4444444444",
    #             },
    #         ]
    #     )

    #     print("Created records:", len(customers))

    #     for customer in customers:
    #         print(
    #             "Customer:",
    #             customer.name,
    #             "| Reference:",
    #             customer.reference,
    #             "| Created At:",
    #             customer.created_at,
    #         )

    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("reference", "New") == "New":
                vals["reference"] = self.env["ir.sequence"].next_by_code(
                    "my.first.customer"
                )

            vals["created_at"] = fields.Datetime.now()

        return super().create(vals_list)

    def write(self, vals):
        vals["last_updated"] = fields.Datetime.now()
        return super().write(vals)

    def unlink(self):
        for customer in self:
            if customer.status == "active":
                raise ValidationError("Active customers cannot be deleted.")

        return super().unlink()
