from pypyr.models import While, converter


def test_init():
    while_ = While(
        stop="stop",
        max=1,
        sleep=0.1,
        error_on_max=True,
    )

    assert while_.stop == "stop"
    assert while_.max == 1
    assert while_.sleep == 0.1
    assert while_.error_on_max is True


def test_convert():
    data = {
        "stop": "stop",
        "max": 1,
        "sleep": 0.1,
        "errorOnMax": True,
    }

    while_ = converter.structure(data, While)

    assert while_ == While(
        stop="stop",
        max=1,
        sleep=0.1,
        error_on_max=True,
    )
