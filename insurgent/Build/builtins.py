async def build(*args):
    """
    Build a project asynchronously.

    This async version of build allows for awaiting the build process.

    Args:
        *args: Arguments to pass to the build function

    Returns:
        True if build succeeded, False otherwise
    """
    from .build import _build_async, build as run_build
    from insurgent.Logging.logger import error

    # Ensure coroutine is properly handled
    try:
        return await run_build(*args)
    except Exception as e:
        error(f"[BUILD] Async build error: {str(e)}")
        return False
