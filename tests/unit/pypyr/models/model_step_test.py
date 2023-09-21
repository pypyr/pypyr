from pypyr.models import Step, While, converter


def test_init():
    """Step.__init__ happy path."""
    step = Step(
        name="blah",
        comment="comment",
        description="description",
        foreach=["foreach"],
        in_={"in": "in"},
        on_error="onError",
        retry={"retry": "retry"},
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
    assert step.retry == {"retry": "retry"}
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
        "retry": {"retry": "retry"},
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
        retry={"retry": "retry"},
        run=True,
        skip=False,
        swallow=False,
        while_=While(stop="stop", max=1, sleep=0.1, error_on_max=True),
    )
