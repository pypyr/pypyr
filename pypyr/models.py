import logging
from collections import defaultdict
from typing import Annotated, Dict, List, NewType, Optional, get_args

from attrs import define, fields
from cattrs import Converter
from cattrs.gen import make_dict_structure_fn, override

from pypyr.dsl import SpecialTagDirective

converter = Converter()
logger = logging.getLogger(__name__)


class Annotable(NewType):
    @property
    def supertype(self):
        return self.__supertype__

    def __getitem__(self, item):
        return Annotated[self, item]


Expression = NewType('Expression', str)
SpecialTag = NewType('SpecialTag', SpecialTagDirective)
Tag = Annotable('Tag', SpecialTag | Expression)


@define
class Retry:
    backoff: Tag[str] = 'fixed'
    backoff_args: Optional[dict] = None
    jrc: Tag[float] = 0
    max: Optional[Tag[int]] = None
    retry_on: Optional[List[str]] = None
    sleep: Tag[float | List[float]] = 0
    sleep_max: Optional[Tag[float]] = None
    stop_on: Optional[List[str]] = None


@define
class While:
    error_on_max: Tag[bool] = False
    max: Optional[Tag[int]] = None
    sleep: Tag[float] = 0
    stop: Optional[Tag[str]] = None


@define
class Step:
    name: str
    comment: Optional[str] = None
    description: Optional[str] = None
    foreach: Optional[Tag[list]] = None
    in_: Optional[dict] = None
    on_error: Optional[str] = None
    retry: Optional[Retry] = None
    run: Tag[bool] = True
    skip: Tag[bool] = False
    swallow: Tag[bool] = False
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


def structure_tag(data, cls):
    if isinstance(data, SpecialTagDirective):
        return data

    tag_type, field_type = get_args(cls)
    logger.debug("structuring '%s' data '%s' ", cls, data)

    try:
        return converter.structure(data, field_type)
    except (ValueError, TypeError) as e:
        if not isinstance(data, str):
            raise e
        return data


def structure_bool(data, cls):
    if not isinstance(data, bool):
        raise ValueError(f'Expected a boolean value, got {data}')

    return data


def structure_list(data, cls):
    if not isinstance(data, list):
        raise ValueError(f'Expected a list value, got {data}')

    return data


converter.register_structure_hook(Pipeline, structure_pipeline)

converter.register_structure_hook(bool, structure_bool)

converter.register_structure_hook(list, structure_list)

converter.register_structure_hook(
    float | List[float],
    lambda data, _: data if isinstance(data, list) else float(data),
)

converter.register_structure_hook(Tag, structure_tag)

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
