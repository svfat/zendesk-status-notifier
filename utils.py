from datetime import timedelta


def calculate_available_time(data, avail_status, not_avail_status):
    last_status = not_avail_status
    start = None
    total = timedelta()
    for item in data:
        if item['status'] == avail_status and last_status != avail_status:
            # start timedelta
            start = item['dt']
        elif item['status'] == not_avail_status and last_status == avail_status:
            # end timedelta
            total += item['dt'] - start
            start = None
        last_status = item['status']
    return total
