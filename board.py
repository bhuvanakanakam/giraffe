"""
board.py -Board state and rules for Giraffee.

Author:  Ayush Jain (ayushjain_01)
Team:    404NotFound (Ayush Jain, Bhuvana Kanakam, Prithvi Sunilkumar)
Course:  95-895 Python Systems Fundamentals, Fall 2026, Mini 2
Part of: M1 Domain Model

What lives here:
  - All custom errors needed for this project

AI Use: None for this file.
"""

from items import BoardItem, User, WorkflowStage
from errors import InvalidBoardError, InvalidStageError, NotFoundError, DuplicateIDError, StageFullError, InvalidUserError, AlreadyClaimedError

class Board:
    """
    Owns a board's members, stages and items.
    """

    def __init__(self, name: str):
        if not isinstance(name, str) or not name.strip():
            raise InvalidBoardError("Board name must be a non-empty string.")
        self._name = name.strip()
        self._users: dict[str, User] = {}
        self._stages: dict[str, WorkflowStage] = {}
        self._items: dict[str, BoardItem] = {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def users(self) -> tuple[User, ...]:
        return tuple(self._users.values())

    @property
    def stages(self) -> tuple[WorkflowStage, ...]:
        return tuple(self._stages.values())

    def add_user(self, user: User)-> None:
        if not isinstance(user, User):
            raise InvalidUserError("Expected a User object")

        if not isinstance(user.user_id, str) or not user.user_id.strip():
            raise InvalidUserError("User ID must be a non-empty string")
        
        if not isinstance(user.name, str) or not user.name.strip():
            raise InvalidUserError("User name cannot be empty")
        if user.user_id in self._users:
            raise DuplicateIDError(
                f"User {user.user_id!r} already exists"
            )

        self._users[user.user_id] = user

    def add_stage(self, stage: WorkflowStage) -> None:
        if not isinstance(stage.name, str) or not stage.name.strip():
            raise InvalidStageError("Stage name cannot be empty")

        if stage.limit is not None:
            if type(stage.limit) is not int or stage.limit < 0:
                raise InvalidStageError(
                    "Stage limit must be a non-negative integer or None"
                )

        if stage.name in self._stages:
            raise DuplicateIDError(
                f"Stage {stage.name!r} already exists"
            )

        self._stages[stage.name] = stage

    def add_item(self, item: BoardItem) -> None:
        """Add a valid item without violating board rules."""
        item.validate()

        if item.item_id in self._items:
            raise DuplicateIDError(
                f"Item {item.item_id!r} already exists"
            )

        if item.stage not in self._stages:
            raise NotFoundError(
                f"Stage {item.stage!r} does not exist"
            )

        if item.owner is not None and item.owner not in self._users:
            raise NotFoundError(
                f"User {item.owner!r} is not a board member"
            )

        stage = self._stages[item.stage]
        count = sum(
            existing.stage == stage.name
            for existing in self._items.values()
        )

        if stage.limit is not None and count >= stage.limit:
            raise StageFullError(
                f"Stage {stage.name!r} has reached its limit"
            )

        self._items[item.item_id] = item

    def claim(self, item_id: str, user_id: str) -> None:
        """Assign an unclaimed item to a board member."""
        if item_id not in self._items:
            raise NotFoundError(
                f"Item {item_id!r} does not exist"
            )

        if user_id not in self._users:
            raise NotFoundError(
                f"User {user_id!r} is not a board member"
            )

        item = self._items[item_id]

        if item.is_claimed:
            raise AlreadyClaimedError(
                f"Item {item_id!r} already belongs to {item.owner!r}"
            )

        item.set_owner(user_id)

    def move(self, item_id: str, stage_name: str) -> None:
        """Move an item without exceeding the destination's limit."""
        if item_id not in self._items:
            raise NotFoundError(
                f"Item {item_id!r} does not exist"
            )

        if stage_name not in self._stages:
            raise NotFoundError(
                f"Stage {stage_name!r} does not exist"
            )

        item = self._items[item_id]

        # Already there: no state or history change is needed.
        if item.stage == stage_name:
            return

        stage = self._stages[stage_name]
        count = sum(
            existing.stage == stage_name
            for existing in self._items.values()
        )

        if stage.limit is not None and count >= stage.limit:
            raise StageFullError(
                f"Stage {stage_name!r} has reached its limit"
            )

        item.set_stage(stage_name)

    def add_comment(self, item_id: str, text: str) -> None:
        """Add a non-empty comment to an item's history."""
        if item_id not in self._items:
            raise NotFoundError(
                f"Item {item_id!r} does not exist"
            )

        if not isinstance(text, str) or not text.strip():
            raise InvalidBoardError("Comment cannot be empty")

        self._items[item_id].add_note(f"Comment: {text.strip()}")

    def describe(self) -> str:
        """Return a readable summary without changing board state."""
        lines = [f"Board: {self.name}"]

        for stage in self._stages.values():
            stage_items = [
                item
                for item in self._items.values()
                if item.stage == stage.name
            ]

            limit = "unlimited" if stage.limit is None else stage.limit
            lines.append(
                f"\n{stage.name} ({len(stage_items)}/{limit})"
            )

            if not stage_items:
                lines.append("  (empty)")

            for item in stage_items:
                lines.append(f"  {item.describe()}")

        return "\n".join(lines)

    def delete_item(self, item_id: str) -> None:
        """Remove an existing item from the board."""
        if item_id not in self._items:
            raise NotFoundError(
                f"Item {item_id!r} does not exist"
            )

        del self._items[item_id]

    def edit_item(
        self,
        item_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
    ) -> None:
        """Update an item's text after validating every supplied field."""
        if item_id not in self._items:
            raise NotFoundError(
                f"Item {item_id!r} does not exist"
            )

        if title is not None:
            if not isinstance(title, str) or not title.strip():
                raise InvalidBoardError(
                    "Title must be a non-empty string"
                )

        if description is not None:
            if not isinstance(description, str):
                raise InvalidBoardError(
                    "Description must be a string"
                )

        item = self._items[item_id]

        # Commit only after all supplied fields have passed validation.
        if title is not None:
            item.title = title.strip()

        if description is not None:
            item.description = description

        if title is not None or description is not None:
            item.add_note("Item text updated")