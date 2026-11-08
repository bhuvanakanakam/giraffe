"""
errors.py - Custom exceptions for the Giraffe's domain rules.

Author:  Ayush Jain (ayushjain_01)
Team:    404NotFound (Ayush Jain, Bhuvana Kanakam, Prithvi Sunilkumar)
Course:  95-895 Python Systems Fundamentals, Fall 2026, Mini 2
Part of: M1 Domain Model

What lives here:
  - All custom errors needed for this project

AI Use: None for this file.
"""

class GiraffeError(Exception):
    """Base class for all Giraffe exceptions."""

class InvalidItemError(GiraffeError):
    """Raised when an item's data is invalid."""

class InvalidBoardError(GiraffeError):
    """Raised when a board's configuration or operation data is invalid."""

class InvalidUserError(InvalidBoardError):
    """Raised when a user is invalid."""

class InvalidStageError(InvalidBoardError):
    """Raised when a stage is invalid."""

class DuplicateIDError(GiraffeError):
    """Raised when an item with a duplicate ID is encountered."""

class NotFoundError(GiraffeError):
    """Raised when an item, stage, or user is not found."""

class AlreadyClaimedError(GiraffeError):
    """Raised when an item has already been claimed by a user."""

class StageFullError(GiraffeError):
    """Raised when an operation would exceed a workflow's stage limit."""
