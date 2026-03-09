class LeaveType:
    def __init__(self, id: int, name: str, annual_quota: int,
                 requires_hr: bool, requires_document: bool, 
                 max_consecutive_days: int, notice_period_days: int,
                 carry_forward_allowed: bool):
        self.id                     = id
        self.name                   = name
        self.annual_quota           = annual_quota
        self.requires_hr            = requires_hr
        self.requires_document      = requires_document
        self.max_consecutive_days   = max_consecutive_days
        self.notice_period_days     = notice_period_days
        self.carry_forward_allowed  = carry_forward_allowed

    def __repr__(self):
        return f"<LeaveType id={self.id} name='{self.name}' quota={self.annual_quota}>"

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            name=row["name"],
            annual_quota=row["annual_quota"],
            requires_hr=bool(row["requires_hr"]),
            requires_document=bool(row["requires_document"]),
            max_consecutive_days=row["max_consecutive_days"],
            notice_period_days=row["notice_period_days"],
            carry_forward_allowed=bool(row["carry_forward_allowed"])
        )
