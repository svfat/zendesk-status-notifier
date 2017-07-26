from datetime import datetime, timedelta


def calculate_available_time(data, avail_status, not_avail_status, f):
    last_status = not_avail_status
    start = None
    total = timedelta()
    for item in data:
        if item['status'] == avail_status and last_status != avail_status:
            # start timedelta
            start = datetime.strptime(item['dt'], f)
        elif item['status'] == not_avail_status and last_status == avail_status:
            # end timedelta
            total += item['dt'] - start
            start = None
        last_status = item['status']
    return total
