"""
items.py - board items and small data records for Giraffe

Author:  Bhuvana Kanakam (bkanakam)
Team:    404NotFound (Ayush Jain, Bhuvana Kanakam, Prithvi Sunilkumar)
Course:  95-895 Python Systems Fundamentals, Fall 2026, Mini 2
Part of: M1 Domain Model

What lives here:
  - WorkflowStage and User: plain data, written as dataclasses
  - BoardItem: the abstract base class every item on a board comes from
  - Task, Chore, ReferralRequest: the three kinds of items we support
  - item_from_dict(): turns saved JSON back into the right kind of item

AI use: I used Claude to help structure this file. I reviewed and
tested every part, and can explain all of it. Cited in the README.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import date

from errors import InvalidItemError


# ---------------------------------------------------------------------------
# Dataclasses
# These only hold facts. They have no rules of their own, so a dataclass
# is enough (it writes __init__, __repr__ and __eq__ for us).
# frozen=True means they can't be changed after they're created.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorkflowStage:
    """One column on a board, like "To Do" or "Accepted".

    limit is the max number of items allowed in this stage.
    None means there's no limit.
    """
    name: str
    limit: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> WorkflowStage:
        return cls(**data)


@dataclass(frozen=True)
class User:
    """Someone who can be added to a board and own items."""
    user_id: str
    name: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> User:
        return cls(**data)


# ---------------------------------------------------------------------------
# BoardItem: the abstract base class
# You can't create a plain BoardItem. Every real item has to be a Task,
# Chore or ReferralRequest, and each of those must write validate(),
# describe() and details() itself.
# ---------------------------------------------------------------------------

class BoardItem(ABC):
    """Anything that can sit on a board and move through its stages.

    owner, stage and history start with an underscore because only Board
    should change them. Board checks its rules first (one owner, stage
    limits) and then calls set_owner() / set_stage().
    """

    KIND = "item"  # each subclass overrides this; it gets saved in the JSON

    def __init__(self, item_id: str, title: str, description: str = "",
                 stage: str | None = None, owner: str | None = None,
                 history: list[str] | None = None):
        self.item_id = item_id
        self.title = title
        self.description = description
        self._stage = stage
        self._owner = owner
        # make our own copy so a list passed in from outside can't change ours
        self._history = list(history) if history else []

    # Read-only properties. Other code can look at these but not assign to
    # them, so nobody can skip Board's checks by writing item.owner = "x".

    @property
    def owner(self) -> str | None:
        return self._owner

    @property
    def stage(self) -> str | None:
        return self._stage

    @property
    def history(self) -> list[str]:
        # hand back a copy, so appending to it doesn't touch the real history
        return list(self._history)

    @property
    def is_claimed(self) -> bool:
        return self._owner is not None

    # Setters. Board calls these only after its own checks pass.
    # Each change is also written to the item's history.

    def set_owner(self, user_id: str | None) -> None:
        self._owner = user_id
        self._history.append(f"owner set to {user_id}")

    def set_stage(self, stage_name: str) -> None:
        self._stage = stage_name
        self._history.append(f"moved to {stage_name}")

    def add_note(self, text: str) -> None:
        self._history.append(text)

    # Every subclass has to write these three. If one is missing, Python
    # refuses to create that object at all, so we can't forget one.

    @abstractmethod
    def validate(self) -> None:
        """Raise InvalidItemError if this item's data doesn't make sense."""

    @abstractmethod
    def describe(self) -> str:
        """Return a one-line summary to show on the board."""

    @abstractmethod
    def details(self) -> dict:
        """Return the fields only this kind of item has, for saving."""

    # Helpers shared by all subclasses

    def _check_common(self) -> None:
        # every kind of item needs an id and a title, so check those once here
        if not isinstance(self.item_id, str) or not self.item_id.strip():
            raise InvalidItemError("item_id cannot be empty")
        if not isinstance(self.title, str) or not self.title.strip():
            raise InvalidItemError(f"item {self.item_id} needs a title")

    def _owner_text(self) -> str:
        return self._owner or "unassigned"

    def to_dict(self) -> dict:
        # shared fields first, then whatever is special to this kind.
        # "kind" is what lets us rebuild the right class when loading.
        return {
            "kind": self.KIND,
            "item_id": self.item_id,
            "title": self.title,
            "description": self.description,
            "stage": self._stage,
            "owner": self._owner,
            "history": list(self._history),
            **self.details(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> BoardItem:
        # drop "kind" since the constructor doesn't take it; cls is already
        # the right subclass because item_from_dict picked it
        fields = {k: v for k, v in data.items() if k != "kind"}
        return cls(**fields)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.item_id!r}, {self.title!r})"

    def __eq__(self, other: object) -> bool:
        # two items are equal if everything we'd save about them matches
        if not isinstance(other, BoardItem):
            return NotImplemented
        return self.to_dict() == other.to_dict()


# ---------------------------------------------------------------------------
# The three kinds of items
# Same method names, different rules. Board just calls item.validate()
# and item.describe() and doesn't need to know which kind it has.
# ---------------------------------------------------------------------------

class Task(BoardItem):
    """A piece of work with a point estimate (sprint boards)."""

    KIND = "task"

    def __init__(self, item_id: str, title: str, points: int, **kwargs):
        super().__init__(item_id, title, **kwargs)
        self.points = points

    def validate(self) -> None:
        self._check_common()
        # points have to be a positive whole number, so 0, -2 or 1.5 fail
        if type(self.points) is not int or self.points <= 0:
            raise InvalidItemError(
                f"task {self.item_id} needs a positive whole number of points")

    def describe(self) -> str:
        return (f"[Task] {self.title} ({self.points} pts) | "
                f"{self.stage} | {self._owner_text()}")

    def details(self) -> dict:
        return {"points": self.points}


class Chore(BoardItem):
    """A household job with a due date (roommate boards)."""

    KIND = "chore"

    def __init__(self, item_id: str, title: str, due_date: str, **kwargs):
        super().__init__(item_id, title, **kwargs)
        # kept as a "YYYY-MM-DD" string so it saves to JSON as is
        self.due_date = due_date

    def validate(self) -> None:
        self._check_common()
        # fromisoformat fails on anything that isn't a real date,
        # like "next friday" or "2026-13-40"
        try:
            date.fromisoformat(self.due_date)
        except (TypeError, ValueError):
            raise InvalidItemError(
                f"chore {self.item_id} needs a due date like 2026-11-08")

    def describe(self) -> str:
        return (f"[Chore] {self.title} (due {self.due_date}) | "
                f"{self.stage} | {self._owner_text()}")

    def details(self) -> dict:
        return {"due_date": self.due_date}


class ReferralRequest(BoardItem):
    """An applicant asking for a referral at a company (referral boards).

    The owner here is the referrer who picks up the request.
    """

    KIND = "referral"

    def __init__(self, item_id: str, title: str, company: str,
                 applicant: str, **kwargs):
        super().__init__(item_id, title, **kwargs)
        self.company = company
        self.applicant = applicant

    def validate(self) -> None:
        self._check_common()
        if not isinstance(self.company, str) or not self.company.strip():
            raise InvalidItemError(
                f"referral {self.item_id} needs a company")
        if not isinstance(self.applicant, str) or not self.applicant.strip():
            raise InvalidItemError(
                f"referral {self.item_id} needs an applicant")

    def describe(self) -> str:
        return (f"[Referral] {self.applicant} -> {self.company} | "
                f"{self.stage} | referrer: {self._owner_text()}")

    def details(self) -> dict:
        return {"company": self.company, "applicant": self.applicant}


# ---------------------------------------------------------------------------
# Loading items back from JSON
# A dict maps each saved "kind" to its class, so there's no if/elif on
# the type. Adding a new kind later is one new line in this dict.
# ---------------------------------------------------------------------------

ITEM_KINDS: dict[str, type[BoardItem]] = {
    Task.KIND: Task,
    Chore.KIND: Chore,
    ReferralRequest.KIND: ReferralRequest,
}


def item_from_dict(data: dict) -> BoardItem:
    """Rebuild a saved item as the right subclass."""
    kind = data.get("kind")
    item_class = ITEM_KINDS.get(kind)
    if item_class is None:
        raise InvalidItemError(f"unknown item kind: {kind!r}")
    return item_class.from_dict(data)


# ---------------------------------------------------------------------------
# Quick check: run "python items.py" to try this file on its own
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    items = [
        Task("t1", "Build login page", points=3, stage="To Do"),
        Chore("c1", "Take out trash", due_date="2026-11-08", stage="Unclaimed"),
        ReferralRequest("r1", "Amazon SDE intern", company="Amazon",
                        applicant="Ana", stage="Requested"),
    ]

    # same two calls on every item; each kind answers in its own way
    for item in items:
        item.validate()
        print(item.describe())

    # save one item to a dict and load it back, it should come back the same
    items[1].set_owner("bhuvana")
    copy = item_from_dict(items[1].to_dict())
    print("round trip ok:", copy == items[1], "|", copy.describe())

    # a bad item should be rejected with our own exception
    try:
        Task("t2", "Broken task", points=0).validate()
    except InvalidItemError as e:
        print("Rejected:", e)
