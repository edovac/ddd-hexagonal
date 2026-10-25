LATE_FEE_PER_DAY = 0.25
LATE_FEE_CAP = 10.0


def late_fee(days_late):
    if days_late <= 0:
        return 0.0
    return min(days_late * LATE_FEE_PER_DAY, LATE_FEE_CAP)
