class LeaveType:
    def __init__(self, id: int, name: str, max_days_per_year: int,
                 requires_approval: bool, requires_docs: bool, is_paid: bool):
        self.id                 = id
        self.name               = name
        self.max_days_per_year  = max_days_per_year
        self.requires_approval  = requires_approval
        self.requires_docs      = requires_docs
        self.is_paid            = is_paid

    def __repr__(self):
        return f"<LeaveType id={self.id} name='{self.name}' max={self.max_days_per_year}>"

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            name=row["name"],
            max_days_per_year=row["max_days_per_year"],
            requires_approval=bool(row["requires_approval"]),
            requires_docs=bool(row["requires_docs"]),
            is_paid=bool(row["is_paid"]),
        )
