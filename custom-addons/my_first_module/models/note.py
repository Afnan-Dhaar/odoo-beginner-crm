from odoo import api, fields, models


class CustomerNote(models.Model):
    _name = "my.first.customer.note"
    _description = "Customer Note"

    customer_id = fields.Many2one(
        "my.first.customer",
        string="Customer",
        required=True,
        ondelete="cascade",
    )

    title = fields.Char(
        string="Title",
        required=True,
    )

    note = fields.Text(
        string="Note",
        required=True,
    )

    note_type = fields.Selection(
        [
            ("general", "General"),
            ("call", "Call"),
            ("email", "Email"),
            ("meeting", "Meeting"),
            ("follow_up", "Follow-up"),
        ],
        string="Note Type",
        default="general",
        required=True,
    )

    status = fields.Selection(
        [
            ("open", "Open"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="open",
        required=True,
    )

    priority = fields.Selection(
        [
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Priority",
        default="normal",
        required=True,
    )

    follow_up_date = fields.Date(
        string="Follow-up Date",
    )

    contacted = fields.Boolean(
        string="Contacted",
        default=False,
    )

    created_at = fields.Datetime(
        string="Created At",
        readonly=True,
        default=fields.Datetime.now,
    )

    updated_at = fields.Datetime(
        string="Updated At",
        readonly=True,
    )

    is_overdue = fields.Boolean(
        string="Overdue",
        compute="_compute_is_overdue",
        search="_search_is_overdue",
    )

    created_by = fields.Many2one(
        "res.users",
        string="Created By",
        readonly=True,
        default=lambda self: self.env.user,
    )

    @api.depends("status", "follow_up_date")
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for note in self:
            note.is_overdue = bool(
                note.status == "open"
                and note.follow_up_date
                and note.follow_up_date < today
            )

    def _search_is_overdue(self, operator, value):
        if operator not in ("=", "!="):
            return []
        is_overdue = value if operator == "=" else not value
        if is_overdue:
            return [
                ("status", "=", "open"),
                ("follow_up_date", "<", fields.Date.today()),
            ]
        return [
            "|",
            ("status", "!=", "open"),
            ("follow_up_date", ">=", fields.Date.today()),
        ]

    def write(self, vals):
        vals["updated_at"] = fields.Datetime.now()
        return super().write(vals)

    def action_mark_done(self):
        for note in self:
            note.status = "done"

    def action_mark_contacted(self):
        for note in self:
            note.contacted = True
