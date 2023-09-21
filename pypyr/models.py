from typing import List, Optional

from attrs import define
from cattrs import Converter
from cattrs.gen import make_dict_structure_fn, override

converter = Converter()


@define
class Step:
    name: str
    comment: Optional[str] = None
    description: Optional[str] = None
    foreach: Optional[list] = None
    in_: Optional[dict] = None
    onError: Optional[str] = None  # TODO
    retry: Optional[dict] = None  # TODO
    run: bool = True
    skip: bool = False
    swallow: bool = False
    while_: Optional[dict] = None  # TODO

    def __hash__(self):
        # TODO: workaround to hash a pipeline
        return id(self)


@define
class Pipeline:
    context_parser: Optional[str] = None
    steps: Optional[List[Step]] = None  # TODO
    on_success: Optional[List[Step]] = None  # TODO
    on_failure: Optional[List[Step]] = None  # TODO

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


converter.register_structure_hook(
    Step, make_dict_structure_fn(Step, converter, in_=override(rename="in"))
)
