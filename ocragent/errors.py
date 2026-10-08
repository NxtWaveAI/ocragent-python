class OcrAgentError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message

    def __repr__(self):
        return f"{self.__class__.__name__}(status={self.status}, code={self.code!r}, message={self.message!r})"


class AuthError(OcrAgentError):
    def __init__(self, message: str = "Invalid or expired API key."):
        super().__init__(401, "UNAUTHORIZED", message)


class ForbiddenError(OcrAgentError):
    def __init__(self, message: str):
        super().__init__(403, "FORBIDDEN", message)


class NotFoundError(OcrAgentError):
    def __init__(self, message: str = "Resource not found."):
        super().__init__(404, "NOT_FOUND", message)


class RateLimitError(OcrAgentError):
    def __init__(self, retry_after: int = 60):
        super().__init__(429, "RATE_LIMITED", f"Rate limit exceeded. Retry after {retry_after}s.")
        self.retry_after = retry_after


class ValidationError(OcrAgentError):
    def __init__(self, message: str):
        super().__init__(422, "VALIDATION_ERROR", message)


class PlanLimitError(OcrAgentError):
    """Raised when the account's plan limit is hit: monthly doc cap, agent slot cap, or API key credit cap."""
    def __init__(self, message: str = "You have reached your plan limit. Please upgrade to continue."):
        super().__init__(402, "plan_limit_exceeded", message)


class AgentPausedError(OcrAgentError):
    """Raised when the target agent is paused and cannot accept new extraction jobs."""
    def __init__(self, message: str = "This agent is paused. Resume it before submitting jobs."):
        super().__init__(422, "agent_paused", message)
