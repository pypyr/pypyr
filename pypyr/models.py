from collections import defaultdict
from typing import Annotated, Dict, List, NewType, Optional, get_args

from attrs import define, fields
from cattrs import Converter
from cattrs.gen import make_dict_structure_fn, override

converter = Converter()


class Annotable(NewType):
    @property
    def supertype(self):
        return self.__supertype__

    def __getitem__(self, item):
        return Annotated[self, item]


Evaluable = Annotable('Evaluable', str)


@define
class Retry:
    backoff: Evaluable[str] = 'fixed'
    backoff_args: Optional[dict] = None
    jrc: Evaluable[float] = 0
    max: Optional[Evaluable[int]] = None
    retry_on: Optional[List[str]] = None
    sleep: Evaluable[float] = 0
    sleep_max: Optional[Evaluable[float]] = None
    stop_on: Optional[List[str]] = None


@define
class While:
    error_on_max: bool = False
    max: Optional[int] = None
    sleep: float = 0
    stop: Optional[str] = None


@define
class Step:
    name: str
    comment: Optional[str] = None
    description: Optional[str] = None
    foreach: Optional[list] = None
    in_: Optional[dict] = None
    on_error: Optional[str] = None
    retry: Optional[Retry] = None
    run: bool = True
    skip: bool = False
    swallow: bool = False
    while_: Optional[While] = None

    def __hash__(self):
        # TODO: workaround to hash a pipeline
        return id(self)


Steps = List[Step | str]


@define
class Pipeline:
    context_parser: Optional[str] = None
    extra: Optional[Dict[str, Steps]] = None
    on_failure: Optional[Steps] = None
    on_success: Optional[Steps] = None
    steps: Optional[Steps] = None

    def __hash__(self):
        # TODO: workaround to hash a pipeline
        return id(self)

    def get(self, key, default=None):
        # TODO: workaround to make the pipeline behave like a dict
        return getattr(self, key, default)

    def __getitem__(self, key):
        # TODO: workaround to make the pipeline behave like a dict
        return getattr(self, key)

    def __contains__(self, item):
        # TODO: workaround to make the pipeline behave like a dict
        return hasattr(self, item)


def structure_pipeline(data, cls, extra_field_name='extra'):
    structured_data = defaultdict(dict)
    fields_by_name = {f.name: f for f in fields(cls)}

    for k, v in data.items():
        if k in fields_by_name and k != extra_field_name:
            structured_data[k] = converter.structure(v, fields_by_name[k].type)
        else:
            structured_data[extra_field_name][k] = converter.structure(
                v, Steps  # TODO: change hard-coded Steps to a dynamic type
            )

    return cls(**structured_data)


def structure_evaluable(data, cls):
    evaluable, type_ = get_args(cls)
    try:
        return converter.structure(data, type_)
    except ValueError:
        return converter.structure(data, evaluable.supertype)


converter.register_structure_hook(Pipeline, structure_pipeline)

converter.register_structure_hook(Evaluable, structure_evaluable)

converter.register_structure_hook(
    Step | str,
    lambda data, _: data
    if isinstance(data, str)
    else converter.structure(data, Step),
)

converter.register_structure_hook(
    Retry,
    make_dict_structure_fn(
        Retry,
        converter,
        backoff_args=override(rename="backoffArgs"),
        retry_on=override(rename="retryOn"),
        sleep_max=override(rename="sleepMax"),
        stop_on=override(rename="stopOn"),
    ),
)

converter.register_structure_hook(
    Step,
    make_dict_structure_fn(
        Step,
        converter,
        on_error=override(rename="onError"),
        in_=override(rename="in"),
        while_=override(rename="while"),
    ),
)

converter.register_structure_hook(
    While,
    make_dict_structure_fn(
        While,
        converter,
        error_on_max=override(rename="errorOnMax"),
    ),
)
