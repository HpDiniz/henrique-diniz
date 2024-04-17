import re

from datetime import datetime, timedelta
from typing import Any


class Utils():

    def get_inferior_date_interval_from_months(number_of_months: int) -> datetime:

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
        return datetime.fromtimestamp(int(timestamp) / 1000)

    def count_pattern_matches_in_text(pattern: Any, text: str, flags=0):
        return len(re.findall(pattern, text, flags=flags))
