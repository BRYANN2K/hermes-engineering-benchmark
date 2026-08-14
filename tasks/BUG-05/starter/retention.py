from datetime import datetime, timedelta, timezone

def select_deletions(names, keep, now, max_age_days):
    parsed=[]
    for name in names:
        try:
            stamp=name.split('-')[1]
            parsed.append((datetime.strptime(stamp,'%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc),name))
        except Exception: pass
    parsed.sort(reverse=True)
    cutoff=now-timedelta(days=max_age_days)
    return sorted(name for stamp,name in parsed[keep:] if stamp<=cutoff)
