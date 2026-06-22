"""Apify facebook posts job_run_resource_estimate calculation."""

import datetime
import typing

from dateutil import parser


class DateParseError(Exception):
    """Custom exception for date parsing errors."""

    pass


def parse_date(
    date_str: typing.Union[str, datetime.datetime, datetime.date],
) -> datetime.date:
    """Parse a date string into a datetime.date object.

    Args:
        date_str: Date string in various formats, or datetime/date object

    Returns:
        datetime.date object

    Raises:
        DateParseError: If the date string cannot be parsed
    """
    if isinstance(date_str, datetime.datetime):
        return date_str.date()
    if isinstance(date_str, datetime.date):
        return date_str

    try:
        return parser.parse(date_str).date()
    except (ValueError, TypeError) as e:
        raise DateParseError(f"Failed to parse date '{date_str}': {str(e)}")


def get_today_date() -> datetime.date:
    """Get today's date as a datetime.date object."""
    return datetime.datetime.now().date()


def get_days_between_dates(
    start_date: typing.Union[str, datetime.datetime, datetime.date],
    end_date: typing.Union[str, datetime.datetime, datetime.date],
) -> int:
    """Calculate the number of days between two dates.

    It will calculate the number of days as if the start date is at 00:00:00 and the end date is at
    00:00:00. This means that the start date is inclusive.

    Args:
        start_date: Start date string or datetime object
        end_date: End date string or datetime object

    Returns:
        Number of days between the dates including the start date.

    Raises:
        DateParseError: If either date string cannot be parsed
    """
    start = parse_date(start_date)
    end = parse_date(end_date)

    if start > end:
        raise ValueError("Start date must be before or equal to end date")

    return (end - start).days


def compute_max_gather_result_count(
    account_url_list: typing.List[str],
    limit_posts_per_account: int,
    posts_created_after: typing.Optional[
        typing.Union[str, datetime.datetime, datetime.date]
    ] = None,
    posts_created_before: typing.Optional[
        typing.Union[str, datetime.datetime, datetime.date]
    ] = None,
) -> int:
    """Compute the maximum number of results that can be gathered based on account list date range.

    This function estimates the maximum possible posts by considering both:
        1. The absolute maximum (number of accounts × posts per account limit)
        2. A time-based maximum using an assumed average of x posts per day per account

    The lower of these two values is returned to provide a more realistic estimate for
    Apify Facebook post gathering. This helps control costs while allowing for larger data
    gathering operations when appropriate.

    Args:
        account_url_list: List of account URLs to gather from
        limit_posts_per_account: Maximum posts to gather per account
        posts_created_after: Optional start date for post creation
        posts_created_before: Optional end date for post creation

    Returns:
        Maximum number of results that can be gathered

    Raises:
        DateParseError: If date strings cannot be parsed
        ValueError: If start date is after end date
    """
    if not account_url_list:
        return 0

    # Calculate absolute maximum based on account list
    max_gather_result_count = len(account_url_list) * limit_posts_per_account

    # If no date range specified, return based on account list only
    if not posts_created_after:
        return max_gather_result_count

    # Parse dates and get date range
    start_date = parse_date(posts_created_after)
    end_date = parse_date(posts_created_before) if posts_created_before else get_today_date()

    days_between = get_days_between_dates(start_date, end_date)

    # Estimate possible posts per day across all accounts
    # Factor of 3 accounts for typical daily post frequency
    estimated_gather_result_count = (
        len(account_url_list) * min(limit_posts_per_account, 3) * days_between
    )

    return min(max_gather_result_count, estimated_gather_result_count)
