import re

from datetime import datetime, timedelta
from typing import Any


class Utils():
    """
    Collection of utility functions for common tasks.
    """

    def get_inferior_date_interval_from_months(number_of_months: int) -> datetime:
        """
        Calculate the start date of an interval by subtracting a number of months from the current date.

        Args:
            number_of_months (int): Number of months to subtract.

        Returns:
            datetime: Start date of the interval.
        """
        current_date = datetime.today().replace(day=1, hour=0, minute=0, second=0)
        target_date = current_date.replace(day=1)

        if number_of_months > 0:
            number_of_months = number_of_months - 1

        for _ in range(number_of_months):
            target_date -= timedelta(days=target_date.day)
            target_date -= timedelta(days=1)
            target_date -= timedelta(days=target_date.day - 1)

        return target_date

    def get_date_from_timestamp(timestamp: str | int):
        """
        Convert a timestamp to a datetime object.

        Args:
            timestamp (str | int): Timestamp to convert.

        Returns:
            datetime: Datetime object representing the timestamp.
        """
        return datetime.fromtimestamp(int(timestamp) / 1000)

    def count_pattern_matches_in_text(pattern: Any, text: str, flags=0):
        """
        Count the occurrences of a pattern in a text using regular expressions.

        Args:
            pattern (Any): Regular expression pattern to search for.
            text (str): Text to search within.
            flags (int): Optional flags to modify regex behavior (default is 0).

        Returns:
            int: Number of matches found.
        """
        return len(re.findall(pattern, text, flags=flags))
