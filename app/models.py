from dataclasses import dataclass, asdict, fields


@dataclass
class Record:
    id: int
    category: str
    rule_topic: str
    ticket_status: str
    time_window: str
    charge_or_refund: str
    rule_ref: str
    source_url: str
    verified: bool = True

    @classmethod
    def from_dict(cls, d: dict) -> "Record":
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in names})

    def to_dict(self) -> dict:
        return asdict(self)

    def text(self) -> str:
        return " ".join([self.rule_topic, self.ticket_status, self.time_window,
                         self.charge_or_refund, self.category])
