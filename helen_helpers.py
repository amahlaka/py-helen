import datetime


def get_date_formatted(input, roundTo=None):
    targetdate = get_date(input)
    if roundTo == "end":
        targetdate.replace(hour=23, minute=59, second=59, microsecond=0)
    elif roundTo == "start":
        targetdate.replace(hour=0, minute=0, second=0, microsecond=0)
    return targetdate.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def current_time(round=False):
    now = datetime.datetime.utcnow()
    # Round to end of the day
    if round:
        now = now.replace(hour=23, minute=59, second=59, microsecond=0)
    return now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
# Convert input, such as "4 Days ago" to a datetime object in UTC
# TODO: Fix the parsing of the strings
def get_date(input):
    now = datetime.datetime.utcnow()
    if input.endswith("Days ago") or input.endswith("day ago"):
        return now - datetime.timedelta(days=int(input[:-8]))
    elif input.endswith("Hours ago"):
        return now - datetime.timedelta(hours=int(input[:-9]))
    elif input.endswith("Weeks ago") or input.endswith("week ago"):
        return now - datetime.timedelta(weeks=int(input[:-8]))
    elif input.endswith("Months ago") or input.endswith("month ago"):
        return now - datetime.timedelta(months=int(input[:-9]))
    elif input.endswith("Years ago") or input.endswith("year ago"):
        return now - datetime.timedelta(years=int(input[:-8]))
    else:
        raise Exception("Unknown time format")
