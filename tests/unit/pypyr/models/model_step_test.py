from pypyr.models import Retry, Step, While, converter


def test_init():
    """Step.__init__ happy path."""
    step = Step(
        name="blah",
        comment="comment",
        description="description",
        foreach=["foreach"],
        in_={"in": "in"},
        on_error="onError",
        retry=Retry(),
        run=True,
        skip=False,
        swallow=False,
        while_=While(),
    )

    assert step.name == "blah"
    assert step.comment == "comment"
    assert step.description == "description"
    assert step.foreach == ["foreach"]
    assert step.in_ == {"in": "in"}
    assert step.on_error == "onError"
    assert step.retry == Retry()
    assert step.run is True
    assert step.skip is False
    assert step.swallow is False
    assert step.while_ == While()


def test_convert():
    data = {
        "name": "blah",
        "comment": "comment",
        "description": "description",
        "foreach": ["foreach"],
        "in": {"in": "in"},
        "onError": "onError",
        "retry": {
            'max': 1,
            'sleep': 0,
            'stopOn': ['ValueError', 'MyModule.SevereError'],
            'retryOn': ['TimeoutError'],
            'backoff': 'backoff',
            'backoffArgs': {'arg1': 'value 1'},
            'sleepMax': 123,
            'jrc': 123.45,
        },
        "run": True,
        "skip": False,
        "swallow": False,
        "while": {"stop": "stop", "max": 1, "sleep": 0.1, "errorOnMax": True},
    }

    step = converter.structure(data, Step)

    assert step == Step(
        name="blah",
        comment="comment",
        description="description",
        foreach=["foreach"],
        in_={"in": "in"},
        on_error="onError",
        retry=Retry(
            backoff="backoff",
            backoff_args={'arg1': 'value 1'},
            jrc=123.45,
            max=1,
            retry_on=['TimeoutError'],
            sleep=0,
            sleep_max=123,
            stop_on=['ValueError', 'MyModule.SevereError'],
        ),
        run=True,
        skip=False,
        swallow=False,
        while_=While(stop="stop", max=1, sleep=0.1, error_on_max=True),
    )
