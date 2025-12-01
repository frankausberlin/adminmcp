# server.py
from datetime import datetime
import json
import logging
import math
from urllib import error, parse, request

from mcp.server.fastmcp import FastMCP

try:
    from adminmcp.logging_config import setup_logging
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from adminmcp.logging_config import setup_logging

try:
    import pytz
except ImportError:
    pytz = None

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

"""AdminMCP Server implementation.

This module implements an MCP (Model Context Protocol) server using FastMCP,
providing various tools and resources for mathematical operations, datetime,
and Wikipedia article fetching.
"""

# Setup logging
# Setup logging
setup_logging()
logger = logging.getLogger(__name__)
logger.info("Starting AdminMCP Server")

# Create an MCP server
mcp = FastMCP("AdminMCP Server")


def _get_timezone_name(tzinfo):
    """Get the name of a timezone object.

    Args:
        tzinfo: A timezone info object or None.

    Returns:
        str: The timezone name, or 'UTC' if not available.
    """
    if tzinfo is None:
        return "UTC"
    return (
        getattr(tzinfo, "zone", None)
        or getattr(tzinfo, "key", None)
        or tzinfo.tzname(None)
        or "UTC"
    )


def _get_current_datetime():
    """Get the current datetime with proper timezone handling.

    This function attempts to use pytz or ZoneInfo for accurate timezone
    information, falling back to the system's default if unavailable.

    Returns:
        datetime: The current datetime object with timezone.
    """
    now = datetime.now().astimezone()
    if pytz:
        tz_name = _get_timezone_name(now.tzinfo)
        try:
            tz = pytz.timezone(tz_name)
        except Exception:
            tz = pytz.UTC
        return now.astimezone(tz)
    if ZoneInfo is not None:
        tz_name = _get_timezone_name(now.tzinfo)
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("UTC")
        return now.astimezone(tz)
    return now


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers together.

    Args:
        a: The first integer to add.
        b: The second integer to add.

    Returns:
        The sum of a and b.
    """
    return a + b

# Add a subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract one integer from another.

    Args:
        a: The integer to subtract from.
        b: The integer to subtract.

    Returns:
        The result of a minus b.
    """
    return a - b

# Add a multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two integers.

    Args:
        a: The first integer to multiply.
        b: The second integer to multiply.

    Returns:
        The product of a and b.
    """
    return a * b

# Add a division tool
@mcp.tool()
def divide(a: int, b: int) -> float | None:
    """Divide one integer by another.

    Args:
        a: The dividend.
        b: The divisor.

    Returns:
        The quotient as a float, or None if dividing by zero.
    """
    return a / b if b != 0 else None

# A resource for mathematical constants
@mcp.resource("resource://math/constant/{name}")
def get_constant(name: str) -> float | None:
    """Get the value of a mathematical constant.

    Args:
        name: The name of the constant (e.g., 'pi', 'e', 'tau').

    Returns:
        The value of the constant as a float, or None if not found.
    """
    constants = {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau
    }
    return constants.get(name.lower())

# A resource to check if a number is even
@mcp.resource("resource://number/{n}/is_even")
def is_even(n: int) -> bool:
    """Check if a given integer is even.

    Args:
        n: The integer to check.

    Returns:
        True if the number is even, False otherwise.
    """
    return n % 2 == 0


@mcp.resource("resource://datetime/current")
def current_datetime():
    """Get current datetime information.

    Returns:
        dict: A dictionary containing 'datetime' (ISO format),
              'timezone', and 'unix_timestamp'.
    """
    now = _get_current_datetime()
    return {
        "datetime": now.isoformat(),
        "timezone": _get_timezone_name(now.tzinfo),
        "unix_timestamp": now.timestamp()
    }


@mcp.resource("resource://wikipedia/article/{title}")
def wikipedia_article(title: str) -> dict:
    """Fetch Wikipedia article summary.

    Args:
        title: The title of the Wikipedia article.

    Returns:
        dict: The article summary data from Wikipedia API,
              or an error dict if not found.

    Raises:
        error.HTTPError: If there's an HTTP error other than 404.
    """
    encoded_title = parse.quote(title, safe="")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
    req = request.Request(url, headers={"User-Agent": "Python MCP server"})
    try:
        with request.urlopen(req) as resp:
            encoding = resp.headers.get_content_charset("utf-8")
            return json.loads(resp.read().decode(encoding))
    except error.HTTPError as exc:
        if exc.code == 404:
            return {"error": "Article not found", "title": title}
        raise


# run the MCP server
if __name__ == "__main__":
    try:
        logger.info("MCP server is starting up")
        mcp.run()
    except Exception as e:
        logger.error(f"MCP server failed: {e}")
        raise
