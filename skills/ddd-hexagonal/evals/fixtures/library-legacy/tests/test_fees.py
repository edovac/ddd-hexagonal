from library.fees import late_fee


def test_no_fee_when_on_time():
    assert late_fee(0) == 0.0


def test_fee_per_day():
    assert late_fee(4) == 1.0


def test_fee_is_capped():
    assert late_fee(100) == 15.0
