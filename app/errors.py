"""Domain exception hierarchy.

Repositories and routers raise these exceptions; ``app.main`` registers a single
handler that turns any of them into the documented error envelope
``{"detail": ..., "code": ...}`` (GUIDE FR-33, §10.4). No layer builds an error
response by hand, so the error format cannot drift between endpoints.
"""

from http import HTTPStatus


class FairShareError(Exception):
    """Base class for every domain error raised by the application."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(FairShareError):
    """A referenced resource does not exist."""

    status_code = HTTPStatus.NOT_FOUND


class ConflictError(FairShareError):
    """The request conflicts with the current state of the resource."""

    status_code = HTTPStatus.CONFLICT


class UnprocessableError(FairShareError):
    """The request is well-formed but violates a domain rule."""

    status_code = HTTPStatus.UNPROCESSABLE_ENTITY


class GroupNotFoundError(NotFoundError):
    code = "GROUP_NOT_FOUND"


class MemberNotFoundError(NotFoundError):
    code = "MEMBER_NOT_FOUND"


class ExpenseNotFoundError(NotFoundError):
    code = "EXPENSE_NOT_FOUND"


class DuplicateMemberNameError(ConflictError):
    code = "DUPLICATE_MEMBER_NAME"


class MemberHasActivityError(ConflictError):
    code = "MEMBER_HAS_ACTIVITY"


class PayerNotInGroupError(UnprocessableError):
    code = "PAYER_NOT_IN_GROUP"


class ParticipantNotInGroupError(UnprocessableError):
    code = "PARTICIPANT_NOT_IN_GROUP"


class DuplicateParticipantError(UnprocessableError):
    code = "DUPLICATE_PARTICIPANT"


class NoParticipantsError(UnprocessableError):
    code = "NO_PARTICIPANTS"


class SharesDoNotSumError(UnprocessableError):
    code = "SHARES_DO_NOT_SUM"


class SameMemberSettlementError(UnprocessableError):
    code = "SAME_MEMBER_SETTLEMENT"


class MemberNotInGroupError(UnprocessableError):
    code = "MEMBER_NOT_IN_GROUP"
