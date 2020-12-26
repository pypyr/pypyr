"""Loops integration tests."""
from pathlib import Path
from pypyr import pipelinerunner

working_dir_tests = Path(Path.cwd(), 'tests')


def test_foreach_enumerables():
    """Builtin generators, on the fly generators, lists & dicts in foreach."""
    context = pipelinerunner.main_with_context(
        pipeline_name='pipelines/loops/foreach',
        working_dir=working_dir_tests)

    assert context['just_list'] == [0, 1, 2]
    assert context['just_dict'] == ['a', 'c']
    assert context['just_dict_items'] == [('a', 'b'), ('c', 'd')]
    assert context['generator_out'] == [4, 5, 6]
    assert context['product_out'] == [('A', 0), ('A', 1),
                                      ('B', 0), ('B', 1)]
