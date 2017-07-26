#!/usr/bin/env python3

import unittest
from datetime import datetime, timedelta

from utils import calculate_available_time

AVAILABLE = 'AVAILABLE'
NOT_AVAILABLE = 'NOT AVAILABLE'


class BaseTest(unittest.TestCase):
    def test_get_total_time(self):
        # generate test data:
        times = [
            ("2017-07-26 14:00:00", NOT_AVAILABLE),
            ("2017-07-26 13:00:00", AVAILABLE),
            ("2017-07-26 12:00:00", NOT_AVAILABLE),
            ("2017-07-26 11:00:00", AVAILABLE),
            ("2017-07-26 10:00:00", NOT_AVAILABLE),
            ("2017-07-26 09:00:00", AVAILABLE),
            ("2017-07-25 12:00:00", NOT_AVAILABLE),
            ("2017-07-25 11:00:00", AVAILABLE),
            ("2017-07-25 10:00:00", NOT_AVAILABLE),
            ("2017-07-25 09:00:00", AVAILABLE),
            ("2017-07-24 16:00:00", NOT_AVAILABLE),
        ]
        f = "%Y-%m-%d %H:%M:%S"
        data = [{'dt': datetime.strptime(t, f), 'status': s} for t, s in times[::-1]]
        assert len(data) == len(times)
        total = calculate_available_time(data=data, avail_status=AVAILABLE, not_avail_status=NOT_AVAILABLE)
        print(total)
        assert total == timedelta(hours=5)


if __name__ == '__main__':
    unittest.main()
