from pypyr.models import Pipeline, Step, converter


def test_init():
    pipeline = Pipeline(
        context_parser="context_parser",
        steps=[Step(name='step')],
        on_success=[Step(name='success')],
        on_failure=[Step(name='failure')],
    )

    assert pipeline.context_parser == "context_parser"
    assert pipeline.steps == [Step(name='step')]
    assert pipeline.on_success == [Step(name='success')]
    assert pipeline.on_failure == [Step(name='failure')]


def test_init_with_steps_names():
    pipeline = Pipeline(
        context_parser="context_parser",
        steps=['step'],
        on_success=['success'],
        on_failure=['failure'],
    )

    assert pipeline.context_parser == "context_parser"
    assert pipeline.steps == ['step']
    assert pipeline.on_success == ['success']
    assert pipeline.on_failure == ['failure']


def test_convert_steps_as_strings():
    data = {
        "context_parser": "context_parser",
        "on_success": ["success_step"],
        "on_failure": ["failure_step"],
        "steps": ["step_one"],
    }

    pipeline = converter.structure(data, Pipeline)

    assert pipeline == Pipeline(
        context_parser="context_parser",
        on_success=["success_step"],
        on_failure=["failure_step"],
        steps=["step_one"],
    )


def test_convert_with_steps():
    data = {
        "context_parser": "context_parser",
        "on_success": [{"name": "success_step"}],
        "on_failure": [{"name": "failure_step"}],
        "steps": [{"name": "step_one"}],
    }

    pipeline = converter.structure(data, Pipeline)

    assert pipeline == Pipeline(
        context_parser="context_parser",
        on_success=[Step(name="success_step")],
        on_failure=[Step(name="failure_step")],
        steps=[Step(name="step_one")],
    )
