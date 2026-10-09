class RequestValidationError(ValueError):
    """Invalid client input: its message is returned to the caller."""


class NoApprovedModelError(RuntimeError):
    """The SSM deployment contract has no approved model package yet."""


class MissingBaselineError(ValueError):
    """An approved model package lacks its data quality drift baselines."""


class AthenaQueryError(RuntimeError):
    pass
