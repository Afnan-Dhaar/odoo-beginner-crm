from odoo import fields, models


class CustomerActivity(models.Model):
    _name = "my.first.customer.activity"
    _description = "Customer Activity"
    _order = "due_date, id"

    customer_id = fields.Many2one(
        "my.first.customer",
        string="Customer",
        required=True,
        ondelete="cascade",
    )

    activity_type = fields.Selection(
        [
            ("call", "Call"),
            ("email", "Email"),
            ("meeting", "Meeting"),
            ("task", "Task"),
            ("follow_up", "Follow-up"),
        ],
        string="Type",
        required=True,
        default="task",
    )

    title = fields.Char(string="Title", required=True)
    description = fields.Text(string="Description")

    assigned_to = fields.Many2one(
        "res.users",
        string="Assigned To",
        required=True,
        default=lambda self: self.env.user,
    )

    due_date = fields.Date(
        string="Due Date",
        required=True,
        default=fields.Date.today,
    )

    priority = fields.Selection(
        [
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Priority",
        required=True,
        default="normal",
    )

    status = fields.Selection(
        [
            ("planned", "Planned"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        required=True,
        default="planned",
    )

    completed_at = fields.Datetime(string="Completed At", readonly=True)
    created_at = fields.Datetime(
        string="Created At",
        readonly=True,
        default=fields.Datetime.now,
    )
    created_by = fields.Many2one(
        "res.users",
        string="Created By",
        readonly=True,
        default=lambda self: self.env.user,
    )

    def action_mark_done(self):
        self.write(
            {
                "status": "done",
                "completed_at": fields.Datetime.now(),
            }
        )

    def action_cancel(self):
        self.write({"status": "cancelled", "completed_at": False})

    def action_set_planned(self):
        self.write({"status": "planned", "completed_at": False})