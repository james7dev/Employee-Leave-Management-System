from config import STATUS_PENDING


class LeaveRequest:
    def __init__(self, id, employee_id, leave_type_id, start_date, end_date,
                 working_days, is_half_day=False, status=STATUS_PENDING,
                 reason=None, manager_note=None, submitted_at=None, actioned_at=None):
        self.id             = id
        self.employee_id    = employee_id
        self.leave_type_id  = leave_type_id
        self.start_date     = start_date
        self.end_date       = end_date
        self.working_days   = working_days
        self.is_half_day    = is_half_day
        self.status         = status
        self.reason         = reason
        self.manager_note   = manager_note
        self.submitted_at   = submitted_at
        self.actioned_at    = actioned_at

    def __repr__(self):
        return (f"<LeaveRequest id={self.id} employee={self.employee_id} "
                f"status='{self.status}' days={self.working_days}>")

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            employee_id=row["employee_id"],
            leave_type_id=row["leave_type_id"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            working_days=row["working_days"],
            is_half_day=bool(row["is_half_day"]),
            status=row["status"],
            reason=row["reason"],
            manager_note=row["manager_note"],
            submitted_at=row["submitted_at"],
            actioned_at=row["actioned_at"],
        )
