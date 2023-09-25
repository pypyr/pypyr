from pypyr.dsl import Jsonify, PyString, SicString
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


def test_converter_cast_fields():
    data = {
        "stop": "stop",
        "max": '1',
        "sleep": '0.1',
        "errorOnMax": True,
    }

    while_ = converter.structure(data, While)

    assert while_ == While(
        stop="stop",
        max=1,
        sleep=0.1,
        error_on_max=True,
    )


def test_expression_fields():
    """
    Expresion is a type that can be formatted as the real value.
    """
    data = {
        'errorOnMax': '{errorOnMax}',
        'max': '{max}',
        'sleep': '{sleep}',
        'stop': '{stop}',
    }

    retry = converter.structure(data, While)

    assert retry == While(
        error_on_max='{errorOnMax}',
        max='{max}',
        sleep='{sleep}',
        stop='{stop}',
    )


def test_special_tag_directive_fields():
    data = {
        'errorOnMax': PyString('f()'),
        'max': Jsonify("{'test': True}"),
        'sleep': SicString('{sleep}'),
        'stop': SicString('{stop}'),
    }

    while_ = converter.structure(data, While)

    assert while_ == While(
        error_on_max=PyString('f()'),
        max=Jsonify("{'test': True}"),
        sleep=SicString('{sleep}'),
        stop=SicString('{stop}'),
    )
