from decimal import Decimal

from pypyr.models import Retry, converter


def test_init_defaults():
    retry = Retry()

    assert retry.backoff == 'fixed'
    assert retry.backoff_args is None
    assert retry.jrc == 0
    assert retry.max is None
    assert retry.retry_on is None
    assert retry.sleep == Decimal('0')
    assert retry.sleep_max is None


def test_init():
    retry = Retry(
        backoff="backoff",
        backoff_args={"backoff": "args"},
        jrc=1,
        max=2,
        retry_on=["retry", "on"],
        sleep=3,
        sleep_max=4,
        stop_on=["stop", "on"],
    )

    assert retry.backoff == "backoff"
    assert retry.backoff_args == {"backoff": "args"}
    assert retry.jrc == 1
    assert retry.max == 2
    assert retry.retry_on == ["retry", "on"]
    assert retry.sleep == Decimal('3')
    assert retry.sleep_max == 4
    assert retry.stop_on == ["stop", "on"]


def test_convert():
    data = {
        'max': 1,
        'sleep': 0,
        'stopOn': ['ValueError', 'MyModule.SevereError'],
        'retryOn': ['TimeoutError'],
        'backoff': 'backoff',
        'backoffArgs': {'arg1': 'value 1'},
        'sleepMax': 123,
        'jrc': 123.45,
    }

    retry = converter.structure(data, Retry)

    assert retry == Retry(
        backoff="backoff",
        backoff_args={'arg1': 'value 1'},
        jrc=123.45,
        max=1,
        retry_on=['TimeoutError'],
        sleep=0,
        sleep_max=123,
        stop_on=['ValueError', 'MyModule.SevereError'],
    )


def test_evaluable_fields():
    """
    Evaluable are types containing an expression
    that can be formatted as the real value.
    """
    data = {
        'backoff': '{backoff}',
        'jrc': '{jrc}',
        'max': '{max}',
        'sleep': '{sleep}',
        'sleepMax': '{sleepMax}',
    }

    retry = converter.structure(data, Retry)

    assert retry == Retry(
        backoff="{backoff}",
        jrc='{jrc}',
        max='{max}',
        sleep='{sleep}',
        sleep_max='{sleepMax}',
    )
