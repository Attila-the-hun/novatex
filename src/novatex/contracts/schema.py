"""Schema version validation for contract templates."""

SUPPORTED_VERSIONS = {"1.0"}


def validate_version(version: str) -> None:
    """Raise ValueError if schema version is not supported."""
    if version not in SUPPORTED_VERSIONS:
        raise ValueError(
            f"Unsupported schema version '{version}'. "
            f"Supported: {sorted(SUPPORTED_VERSIONS)}"
        )
