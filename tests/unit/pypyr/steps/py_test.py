"""py.py unit tests."""
import pytest
from pypyr.context import Context
from pypyr.dsl import PyString
from pypyr.errors import KeyInContextHasNoValueError, KeyNotInContextError
from pypyr.moduleloader import _ChainMapPretendDict
import pypyr.steps.py

# region py


def test_py_existing_key():
    """Py expression can update existing key."""
    context = Context({'x': 123, 'py': "x = abs(-42); save('x')"})
    assert context['x'] == 123
    pypyr.steps.py.run_step(context)
    # nothing added to context, but x is updated.
    assert context == {'x': 42, 'py': "x = abs(-42); save('x')"}


def test_py_with_import():
    """Py expression can use imports."""
    context = Context(
        {'y': 4, 'py': 'import math\nx = math.sqrt(y)\nsave("x")'})
    assert context['y'] == 4
    assert 'x' not in context
    pypyr.steps.py.run_step(context)
    assert context['x'] == 2
    assert context['y'] == 4


def test_py_single_code():
    """One word python function works."""
    context = Context({'py': 'abs(-1-2)'})
    pypyr.steps.py.run_step(context)


def test_py_sequence():
    """Sequence of py code works and touches context."""
    context = Context({'py': "test = 1; save('test')"})
    pypyr.steps.py.run_step(context)

    context.update({'py': "test += 2; save('test')"})
    pypyr.steps.py.run_step(context)

    context.update({'py': "test += 3; save('test')"})
    pypyr.steps.py.run_step(context)

    assert context['test'] == 6, "context should be 6 at this point"

    assert context == {'py': "test += 3; save('test')", 'test': 6}


def test_py_replace_objects():
    """Rebind mutable and immutable objects in exec scope."""
    pycode = """\
alist = [0, 1, 2]
adict = {'a': 'b', 'c': 'd'}
anint = 456
mutate_me.append(12)
astring = 'updated'
"""
    context = Context({'alist': [0, 1],
                       'adict': {'a': 'b'},
                       'anint': 123,
                       'mutate_me': [10, 11],
                       'astring': 'a string',
                       'py': pycode})

    pypyr.steps.py.run_step(context)

    # rebound vars not changed because no `save()`
    assert context == {'alist': [0, 1],
                       'adict': {'a': 'b'},
                       'anint': 123,
                       'mutate_me': [10, 11, 12],
                       'astring': 'a string',
                       'py': pycode}


def test_py_with_closure_scope():
    """Free variables scopes resolve to global."""
    pycode = """\
list1.append(1)
list2 = ['a', 'b', 'c']
out = [(x, y) for x in list1 for y in list2]
save('out')
"""
    context = Context({'list1': [0],
                       'list2': ['a', 'b'],
                       'py': pycode})

    pypyr.steps.py.run_step(context)

    assert context == {'list1': [0, 1],
                       'list2': ['a', 'b'],
                       'py': pycode,
                       'out': [(0, 'a'), (0, 'b'), (0, 'c'),
                               (1, 'a'), (1, 'b'), (1, 'c')]}


def test_py_save_inputs():
    """Special save takes args and kwargs."""
    pycode = """\
a = 1
b = 2
c = 3
d = 4
e = 5
f = 6
g = 7
h = 8
i = 9
j = 10
save('a')
save('b', 'c')
save(dd=d)
save(ee=e, ff=f+1)
save('g', 'h', ii=i, jj=j, k=5)
"""
    context = Context({'py': pycode})
    pypyr.steps.py.run_step(context)

    assert context == {'a': 1,
                       'b': 2,
                       'c': 3,
                       'dd': 4,
                       'ee': 5,
                       'ff': 7,
                       'g': 7,
                       'h': 8,
                       'ii': 9,
                       'jj': 10,
                       'k': 5,
                       'py': pycode}


def test_py_save_existing():
    """Save overwrites existing keys."""
    pycode = """\
alist = [0, 1, 2]
adict = {'a': 'b', 'c': 'd'}
anint = 456
mutate_me.append(12)
astring = 'updated'

save('alist', 'adict', 'anint', 'mutate_me', 'astring')
"""
    context = Context({'alist': [0, 1],
                       'adict': {'a': 'b'},
                       'anint': 123,
                       # strictly speaking not necessary to save mutate_me
                       # explicitly, coz it's mutated not rebound, but test
                       # that it works coz end-users mightn't see the
                       # distinction
                       'mutate_me': [10, 11],
                       'astring': 'a string',
                       'py': pycode})

    pypyr.steps.py.run_step(context)

    assert context == {'alist': [0, 1, 2],
                       'adict': {'a': 'b', 'c': 'd'},
                       'anint': 456,
                       'mutate_me': [10, 11, 12],
                       'astring': 'updated',
                       'py': pycode}


def test_py_save_key_error():
    """Save raises special message on KeyError."""
    pycode = "notfound='arb'; save(notfound)"
    context = Context({'py': pycode})

    with pytest.raises(KeyError) as err:
        pypyr.steps.py.run_step(context)

    # KeyError looks like it reprs on the __str__?
    expected = repr(
        "Trying to save 'arb', but can't find it in the py step scope. "
        "Remember it should be save('key'), not save(key) - mind the quotes.")

    assert str(err.value) == expected


def test_py_save_keyword_exists():
    """Save does not overwrite existing user 'save' key."""
    pycode = "k2='v2'; save('k2')"
    context = Context({'save': 123, 'py': pycode})

    pypyr.steps.py.run_step(context)

    assert context == {'save': 123, 'py': pycode, 'k2': 'v2'}


def test_py_imports_not_in_context():
    """Imported modules + non saves don't end up in context."""
    pycode = """\
from math import sqrt
b = sqrt(a)
"""
    context = Context({'a': 4,
                       'py': pycode})

    pypyr.steps.py.run_step(context)

    assert context == {'a': 4,
                       'py': pycode}


def test_py_sequence_with_semicolons():
    """Single py code string with semi - colons works."""
    context = Context({'py':
                       'x = abs(-1); x+= abs(-2); x += abs(-3); save("x")'})
    pypyr.steps.py.run_step(context)

    assert context == Context({
        'py': 'x = abs(-1); x+= abs(-2); x += abs(-3); save("x")',
        'x': 6})


def test_py_sequence_with_linefeeds():
    """Single py code string with linefeeds works."""
    context = Context({'py':
                       'abs(-1)\nabs(-2)\nabs(-3)'})
    pypyr.steps.py.run_step(context)


def test_py_error_throws():
    """Input pycode error should raise up to caller."""
    with pytest.raises(AssertionError):
        context = Context({'py': 'assert False'})
        pypyr.steps.py.run_step(context)


def test_py_no_context_throw():
    """No pycode in context should throw assert error."""
    with pytest.raises(KeyNotInContextError) as err_info:
        context = Context({'blah': 'blah blah'})
        pypyr.steps.py.run_step(context)

    assert str(err_info.value) == ("context['py'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.py.")


def test_py_none_context_throw():
    """None pycode in context should throw assert error."""
    with pytest.raises(KeyInContextHasNoValueError):
        context = Context({'py': None})
        pypyr.steps.py.run_step(context)
# endregion py

# region pycode


def test_pycode_single_code():
    """One word python function works."""
    context = Context({'pycode': 'abs(-1-2)'})
    pypyr.steps.py.run_step(context)


def test_pycode_sequence():
    """Sequence of py code works and touches context."""
    context = Context({'pycode': "context['test'] = 1;"})
    pypyr.steps.py.run_step(context)

    context.update({'pycode': "context['test'] += 2"})
    pypyr.steps.py.run_step(context)

    context.update({'pycode': "context['test'] += 3"})
    pypyr.steps.py.run_step(context)

    assert context['test'] == 6, "context should be 6 at this point"

    assert context == {'pycode': "context['test'] += 3", 'test': 6}


def test_pycode_replace_objects():
    """Rebind mutable and immutable objects in eval scope."""
    pycode = """\
context['alist'] = [0, 1, 2]
context['adict'] = {'a': 'b', 'c': 'd'}
context['anint'] = 456
context['mutate_me'].append(12)
context['astring'] = 'updated'
"""
    context = Context({'alist': [0, 1],
                       'adict': {'a': 'b'},
                       'anint': 123,
                       'mutate_me': [10, 11],
                       'astring': 'a string',
                       'pycode': pycode})

    pypyr.steps.py.run_step(context)

    assert context == {'alist': [0, 1, 2],
                       'adict': {'a': 'b', 'c': 'd'},
                       'anint': 456,
                       'mutate_me': [10, 11, 12],
                       'astring': 'updated',
                       'pycode': pycode}


def test_pycode_with_closure_scope():
    """Free variables in closure scopes resolve to global."""
    pycode = """\
context['list1'].append(1)
context['list2'] = ['a', 'b', 'c']
context['out'] = [(x, y) for x in context['list1'] for y in context['list2']]
"""
    context = Context({'list1': [0],
                       'list2': ['a', 'b'],
                       'pycode': pycode})

    pypyr.steps.py.run_step(context)

    assert context == {'list1': [0, 1],
                       'list2': ['a', 'b', 'c'],
                       'pycode': pycode,
                       'out': [(0, 'a'), (0, 'b'), (0, 'c'),
                               (1, 'a'), (1, 'b'), (1, 'c')]}


def test_pycode_imports_not_in_context():
    """Imported modules don't end up in context."""
    pycode = """\
from math import sqrt
context['b'] = sqrt(context['a'])
"""
    context = Context({'a': 4,
                       'pycode': pycode})

    pypyr.steps.py.run_step(context)

    assert context == {'a': 4,
                       'b': 2,
                       'pycode': pycode}


def test_pycode_sequence_with_semicolons():
    """Single py code string with semi - colons works."""
    context = Context({'pycode':
                       'abs(-1); abs(-2); abs(-3);'})
    pypyr.steps.py.run_step(context)

    assert context == {'pycode':
                       'abs(-1); abs(-2); abs(-3);'}, ("context in and out "
                                                       "the same")


def test_pycode_sequence_with_linefeeds():
    """Single py code string with linefeeds works."""
    context = Context({'pycode':
                       'abs(-1)\nabs(-2)\nabs(-3)'})
    pypyr.steps.py.run_step(context)


def test_pycode_error_throws():
    """Input pycode error should raise up to caller."""
    with pytest.raises(AssertionError):
        context = Context({'pycode': 'assert False'})
        pypyr.steps.py.run_step(context)


def test_pycode_no__context_throw():
    """No pycode in context should throw assert error."""
    with pytest.raises(KeyNotInContextError) as err_info:
        context = Context({'blah': 'blah blah'})
        pypyr.steps.py.run_step(context)

    assert str(err_info.value) == ("context['py'] "
                                   "doesn't exist. It must exist for "
                                   "pypyr.steps.py.")


def test_pycode_none_context_throw():
    """None pycode in context should throw assert error."""
    with pytest.raises(KeyInContextHasNoValueError):
        context = Context({'pycode': None})
        pypyr.steps.py.run_step(context)

# endregion pycode

# region nested scope for both py and pycode


def test_py_scope_class_accessors():
    """Class with instance, static & class attributes for py and pycode."""
    # region py
    pycode = """\
class ArbClassForEvalTest():
    a = 123

    def __init__(self):
        self.b = 456

    def dothing(self, val):
        return ArbClassForEvalTest.a + val

    @classmethod
    def dothing_class_method(cls, val):
        return cls.a - val

    @staticmethod
    def dothing_static_method(val):
        return val + 2

out_class = ArbClassForEvalTest
a = ArbClassForEvalTest.a
b = ArbClassForEvalTest().b
c = ArbClassForEvalTest().dothing(2)
d = ArbClassForEvalTest.dothing_class_method(3)
e = ArbClassForEvalTest.dothing_static_method(4)
f = ArbClassForEvalTest

save('a', 'b', 'c', 'd', 'e', 'f')
"""
    context = Context({'a': 999,
                       'py': pycode})
    pypyr.steps.py.run_step(context)

    def verify_context(context):
        assert context['a'] == 123
        assert context['b'] == 456
        assert context['c'] == 125
        assert context['d'] == 120
        assert context['e'] == 6

        instance = context['f']()
        assert instance.b == 456
        assert instance.dothing(5) == 128

        assert len(context) == 7

    verify_context(context)
    assert PyString('f().dothing(6)').get_value(context) == 129

    # endregion py
    # region pycode
    pycode = """\
class ArbClassForEvalTest():
    a = 123

    def __init__(self):
        self.b = 456

    def dothing(self, val):
        return ArbClassForEvalTest.a + val

    @classmethod
    def dothing_class_method(cls, val):
        return cls.a - val

    @staticmethod
    def dothing_static_method(val):
        return val + 2

out_class = ArbClassForEvalTest
context['a'] = ArbClassForEvalTest.a
context['b'] = ArbClassForEvalTest().b
context['c'] = ArbClassForEvalTest().dothing(2)
context['d'] = ArbClassForEvalTest.dothing_class_method(3)
context['e'] = ArbClassForEvalTest.dothing_static_method(4)
context['f'] = ArbClassForEvalTest
"""
    context = Context({'a': 999,
                       'pycode': pycode})
    pypyr.steps.py.run_step(context)

    verify_context(context)
    assert PyString('f.dothing_class_method(6)').get_value(context) == 117
    # endregion pycode


def test_py_scope_function():
    """Nested functions resolve globals."""
    # region py
    pycode = """\
a = context_in_a + 2

def my_function(arg1):
    return arg1 + context_in_b

def my_closure(arg1):
    closure_scoped = a + arg1 + context_in_c

    def enclosed(arg2):
        return arg1 + arg2 + closure_scoped + context_in_d

    return enclosed

save('a', 'my_function', closure=my_closure(3))
"""
    context = Context({'context_in_a': 10,
                       'context_in_b': 20,
                       'context_in_c': 30,
                       'context_in_d': 40,
                       'py': pycode})
    pypyr.steps.py.run_step(context)

    def verify_context(context):
        assert context['a'] == 12
        assert context['my_function'](3) == 23
        # closure_scoped == 45
        assert context['closure'](4) == 92

        assert len(context) == 8

    verify_context(context)
    assert PyString('closure(5) - abs(-3)').get_value(context) == 90

    # endregion py

    # region pycode
    pycode = """\
a = context['context_in_a'] + 2

def my_function(arg1):
    return arg1 + context['context_in_b']

def my_closure(arg1):
    closure_scoped = a + arg1 + context['context_in_c']

    def enclosed(arg2):
        return arg1 + arg2 + closure_scoped + context['context_in_d']

    return enclosed

context['a'] = a
context['my_function'] = my_function
context['closure'] = my_closure(3)
"""
    context = Context({'context_in_a': 10,
                       'context_in_b': 20,
                       'context_in_c': 30,
                       'context_in_d': 40,
                       'pycode': pycode})
    pypyr.steps.py.run_step(context)

    verify_context(context)
    assert PyString('closure(5) - abs(-3)').get_value(context) == 90
    # endregion pycode


def test_py_scope_class_implicit_global():
    """Class-level global reference resolves."""
    # region py
    # will resolve because globals is a dict
    pycode = """\
class MyClass():
    b = context_in_a + 1

    def dothing(self, val):
        return val + context_in_a

    @classmethod
    def dothing_class_method(cls, val):
        return val + context_in_a

    @staticmethod
    def dothing_static_method(val):
        return val + context_in_a

assert MyClass.b == 11
assert MyClass().dothing(10) == 20
assert MyClass.dothing_class_method(20) == 30
assert MyClass.dothing_static_method(30) == 40
save('MyClass')
"""
    context = Context({'context_in_a': 10,
                       'py': pycode})

    pypyr.steps.py.run_step(context)

    assert len(context) == 3
    assert context['context_in_a'] == 10
    assert context['py'] == pycode
    assert 'MyClass' in context

    context['context_in_a'] = 100
    assert context['MyClass']().dothing(40) == 50
    assert context['MyClass'].dothing_class_method(50) == 60
    assert context['MyClass'].dothing_static_method(60) == 70
    assert context['context_in_a'] == 100
    # endregion py

    # region pycode
    # Does resolve for pycode form, because it uses a standard dict as globals
    pycode = """\
context['bare'] = 111
class MyClass():
    b = context['context_in_a'] + 1
    context['context_in_b'] = abs(-22)

    def dothing(self, val):
        context['dothing_instance'] = val + 2

    @classmethod
    def dothing_class_method(cls, val):
        context['dothing_class'] = val + 3

    @staticmethod
    def dothing_static_method(val):
        context['dothing_static'] = val + 4

assert MyClass.b == 11
MyClass().dothing(10)
MyClass.dothing_class_method(11)
MyClass.dothing_static_method(12)
"""
    context = Context({'context_in_a': 10,
                       'context_in_b': 20,
                       'pycode': pycode})
    pypyr.steps.py.run_step(context)

    assert context == {'bare': 111,
                       'context_in_a': 10,
                       'context_in_b': 22,
                       'dothing_instance': 12,
                       'dothing_class': 14,
                       'dothing_static': 16,
                       'pycode': pycode}
    # endregion pycode


def test_py_scope_class_globals():
    """Global lookup inside class."""
    # region py
    pycode = """\
a = context_in_a + 2
context_in_b = 22

class MyClass():
    b = 3
    global context_in_c
    c = context_in_c + abs(-3)
    context_in_c = 333

    def my_function(self, arg1):
        return arg1 + context_in_c + context_in_d

    class MyNested():
        global context_in_e
        d = context_in_e + 5
        context_in_e = 555

        def dothing(self):
            return context_in_a + 6

assert a == 12
# notice context_in_c is updated at class level
assert MyClass().my_function(1) == 333 + context_in_d + 1
assert MyClass.b == 3
assert MyClass.c == 33
assert MyClass.MyNested.d == 55
assert MyClass.MyNested().dothing() == 16
assert context_in_c == 333
assert context_in_e == 555
context_in_e = 5555
save('context_in_e')
"""
    context = Context({'context_in_a': 10,
                       'context_in_b': 20,
                       'context_in_c': 30,
                       'context_in_d': 40,
                       'context_in_e': 50,
                       'py': pycode})
    pypyr.steps.py.run_step(context)

    assert context == {'context_in_a': 10,
                       'context_in_b': 20,  # no save, no update
                       'context_in_c': 30,  # in class scope
                       'context_in_d': 40,
                       'context_in_e': 5555,
                       'py': pycode}
    # endregion py

    # region py style with _ChainMapPretendDict to illustrate difference
    pycode = """\
a = context_in_a + 2
context_in_b = 22

class MyClass():
    b = 3
    global context_in_c
    c = context_in_c + abs(-3)
    context_in_c = 333

    def my_function(self, arg1):
        return arg1 + context_in_c + context_in_d

    class MyNested():
        global context_in_e
        d = context_in_e + 5
        context_in_e = 555

        def dothing(self):
            return context_in_a + 6

assert a == 12
# notice context_in_c still thinks it's 30 - global doesn't update
assert MyClass().my_function(1) == 30 + context_in_d + 1
assert MyClass.b == 3
assert MyClass.c == 33
assert MyClass.MyNested.d == 55
assert MyClass.MyNested().dothing() == 16
assert context_in_c == 30
assert context_in_e == 50 # even with global, no update coz ChainMap
context_in_e = 5555
# save('context_in_e')
"""
    context = Context({'context_in_a': 10,
                       'context_in_b': 20,
                       'context_in_c': 30,
                       'context_in_d': 40,
                       'context_in_e': 50,
                       'py': pycode})
    first_dict = {}
    # first_dict gets any adds/imports, not the 2nd dict which is context.
    # other than this, first_dict behaves like locals, basically.
    globals = _ChainMapPretendDict(first_dict,
                                   context)
    # the save function ref allows pipeline to use save to persist vars
    # back to context,
    # first_dict['save'] = get_save(context, globals)
    exec(context['py'], globals)

    assert context == {'context_in_a': 10,
                       'context_in_b': 20,  # no save, no update
                       'context_in_c': 30,  # in class scope
                       'context_in_d': 40,
                       'context_in_e': 50,  # even with global, no update
                       'py': pycode}
    # endregion  py style with _ChainMapPretendDict to illustrate difference

    # region pycode
    pycode = """\
a = context['context_in_a'] + 2
context['context_in_b'] = 22

class MyClass():
    b = 3
    # no global necessary for pycode form
    c = context['context_in_c'] + abs(-3)
    context['context_in_c'] = 333

    def my_function(self, arg1):
        return arg1 + context['context_in_c'] + context['context_in_d']

    class MyNested():
        d = context['context_in_e'] + 5
        context['context_in_e'] = 555

        def dothing(self):
            return context['context_in_a'] + 6

assert a == 12
assert MyClass().my_function(1) == 333 + 40 + 1
assert MyClass.b == 3
assert MyClass.c == 33
assert MyClass.MyNested.d == 55
assert MyClass.MyNested().dothing() == 16
assert context['context_in_c'] == 333
context['context_in_e'] = 5555
"""
    context = Context({'context_in_a': 10,
                       'context_in_b': 20,
                       'context_in_c': 30,
                       'context_in_d': 40,
                       'context_in_e': 50,
                       'pycode': pycode})
    pypyr.steps.py.run_step(context)

    assert context == {'context_in_a': 10,
                       'context_in_b': 22,
                       'context_in_c': 333,  # in class scope
                       'context_in_d': 40,
                       'context_in_e': 5555,
                       'pycode': pycode}
    # endregion pycode

# endregion nested scope for both py and pycode
