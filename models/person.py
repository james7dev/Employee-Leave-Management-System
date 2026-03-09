class Person:
    def __init__(self, id: int, name: str, email: str, department: str, role: str):
        self.id         = id
        self.name       = name
        self.email      = email
        self.department = department
        self.role       = role

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} name='{self.name}' role='{self.role}'>"

    @classmethod
    def from_row(cls, row: dict):
        return cls(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            department=row["department"],
            role=row["role"],
        )
