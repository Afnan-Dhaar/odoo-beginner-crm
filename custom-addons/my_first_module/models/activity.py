from odoo import api, fields, models


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
    completed_by = fields.Many2one(
        "res.users",
        string="Completed By",
        readonly=True,
    )
    is_overdue = fields.Boolean(
        string="Overdue",
        compute="_compute_is_overdue",
        search="_search_is_overdue",
    )
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

    @api.depends("status", "due_date")
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for activity in self:
            activity.is_overdue = bool(
                activity.status == "planned"
                and activity.due_date
                and activity.due_date < today
            )

    def _search_is_overdue(self, operator, value):
        if operator not in ("=", "!="):
            return []
        is_overdue = value if operator == "=" else not value
        if is_overdue:
            return [
                ("status", "=", "planned"),
                ("due_date", "<", fields.Date.today()),
            ]
        return [
            "|",
            ("status", "!=", "planned"),
            ("due_date", ">=", fields.Date.today()),
        ]

    def action_mark_done(self):
        self.write(
            {
                "status": "done",
                "completed_at": fields.Datetime.now(),
                "completed_by": self.env.user.id,
            }
        )

    def action_cancel(self):
        self.write(
            {
                "status": "cancelled",
                "completed_at": False,
                "completed_by": False,
            }
        )

    def action_set_planned(self):
        self.write(
            {
                "status": "planned",
                "completed_at": False,
                "completed_by": False,
            }
        )
