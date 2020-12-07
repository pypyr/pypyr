# Namespace dictionaries for dynamic Python code in eval & exec
## What we're trying to do here
pypyr provides two ways of letting a pipeline run inline dynamic python code:

- Expressions via a `!py` string.
```yaml
- name: arbitrary-step
  comment: arbitrary python expression to evaluate to a bool.
  run: !py len(arbkey) > 1
```

- Dynamic code block via the `pypyr.steps.py` built-in step.
```yaml
- name: pypyr.steps.py
  comment: just some arbitrary python code.
  in:
    py: |
      from math import sqrt

      print(f"py step: {1+1}")

      # use imported code like sqrt from math
      arbvalue = sqrt(1764)
      print(int(arbvalue))
```

The underlying mechanism for these is Python's 
[eval](https://docs.python.org/3/library/functions.html#eval) and 
[exec](https://docs.python.org/3/library/functions.html#exec).

To make pipeline authors' lives easier, pypyr should allow you to use context
dictionary keys as if they are plain old variables in the dynamic code. Since
context is pretty much a dict anyway, the pypyr runtime can inject the context
dict into the dynamic code's namespace:

```python
context = {'a': 'b'}
exec('assert a == "b"', context)
```

## The problem
### eval & exec free variables only resolve against globals
Function signatures for eval and exec:
- `eval(expression[, globals[, locals]])`
    - From Python documentation:
    > Note, eval() does not have access to the nested scopes (non-locals) in the enclosing environment.
- `exec(object[, globals[, locals]])`
    - From Python documentation:
    > If exec gets two separate objects as globals and locals, the code will be executed as if it were embedded in a class definition.

For both, [free variables resolve _only_ against
globals](https://docs.python.org/3/reference/executionmodel.html#resolution-of-names).


> Class definition blocks and arguments to exec() and eval() are special in the
> context of name resolution. A class definition is an executable statement that
> may use and define names. These references follow the normal rules for name
> resolution with an exception that unbound local variables are looked up in the
> global namespace. The namespace of the class definition becomes the attribute
> dictionary of the class. The scope of names defined in a class block is
> limited to the class block; it does not extend to the code blocks of methods –
> this includes comprehensions and generator expressions since they are
> implemented using a function scope. 

Simply put, that means this will not work because the nested scope in the 
comprehension will resolve in `globals`, not `locals`:
```python
source = '[(x, y) for x in list1 for y in list2]'

globals = {}
locals = {
    'list1': [0, 1, 2],
    'list2': ['a', 'b', 'c']
}

# both eval & exec will fail with:
# NameError: name 'list2' is not defined
eval(source, globals, locals)
exec(source, globals, locals)
```

Whereas this will work:
```python
source = '[(x, y) for x in list1 for y in list2]'

globals = {'list1': [0, 1, 2],
           'list2': ['a', 'b', 'c']}
locals = {}

# works. because list1 + list2 are in globals.
eval(source, globals, locals)
exec(source, globals, locals)
```

This is really not a great error: other than an operator being steeped in the
edge case mysteries of Python namespacing it's not at all an obvious failure.
For a pipeline author the dynamic python code looks like it should work, and
indeed if you ran it as normal Python it also will work:
```python
list1 = [0, 1, 2]
list2 = ['a', 'b', 'c']
out = [(x, y) for x in list1 for y in list2]
```

So, to make this work the contents of context _has_ to be in `globals`. The
following possible solutions discuss the options for doing so.

## Possible solutions
### Using context as globals
A naive implementation is simply to use the pypyr context as globals, since
context is in itself a dict:
```python
eval(source, context)
exec(source, context)
```

This has implications for the context dictionary, however.

For both eval & exec (from official documentation):
> If the globals dictionary does not contain a value for the key __builtins__, a
> reference to the dictionary of the built-in module builtins is inserted under
> that key.

And in the case of `exec`, any additional variables declared and also any
imports in the dynamic code will also end up in `globals`:
```python
source = """\
from math import sqrt
x = 123
"""

# globals and locals
globals = {}
locals = {}
# x and sqrt in locals,
# __builtins__ in globals
exec(source, globals, locals)

# only using globals
globals = {}
locals = {}
# x, sqrt, __builtins__ in globals
exec(source, globals)
```

This is a problem because:
- Which variables should persist into context after the step completes? There
  might well be intermediate variables that the operator does _not_ want to
  pollute context. The `pypyr.steps.py` step should behave like a function, it
  is counter-intuitive & surprising that any arbitrary variable in the enclosed
  scope ends up persisted or rebinding existing variables in context.
- The pipeline author will especially not expect imports to end up in context.
- You can't go back to using context as `locals` because
  - free variables won't resolve anymore, as described above. So nested list
    comprehensions will stop working.
  - you still end up with `imports` in locals 
- Context will get an extra pipeline accessible `__builtins__` key. Although
  this arguably not a big deal and even more arguably a very edge case, it could
  theoretically clash with a user provided key of the same name.

### Creating a new dict
You can unpack context into a new dict, so any additions do not pollute the 
original context:

```python
source = """\
from math import sqrt
a = 'UPDATED'
c['c2'] = 'NEW'
x = 123
"""
globals = {'__builtins__': __builtins__}
context = {'a': 'b', 'c': {'c1': '123'}}
globals.update(context)

# could instead create a third dict like this. . . but why?
# namespace = {**globals, **context}

# everything in globals
exec(source, globals)

# context not polluted with any dynamic additions
# immutable objects will not update
# but any mutable updates will persist.
# {'a': 'b', 'c': {'c1': '123', 'c2': 'NEW'}}
```

This approach more or less works the way a Python enclosed scope works, e.g in 
a function. I.e mutables rebind and therefore do not persist outside of the
enclosed scope, and immutables update unless you re-assign them.

This approach has its own problems:
- Context is potentially big. Effectively making a copy of it is not great for
  cpu & memory.
  - This probably doesn't matter too much for `exec` in `pypyr.steps.py` since
    this is a discrete step.
  - But, for `!py` strings this can massively increase overhead due to their
    potential ubiquity all over the pipeline. Specifically for a `!py` string
    you would have to copy context as it is at that point into namespace for
    each and every py-string for the simple reason that context mutates, so no
    simple caching.
- You will have to add a way for the pipeline author to specify which variables
  from the dynamic code to persist back into context.
- If pypyr is going to inject a `save` function, or indeed any other key, into
  the scope, it will hide any existing user keys of the same name. This won't
  touch the originals in context itself, so that these are hidden for the
  duration of the step scope is not necessarily a big problem.

### context as globals with in-place delete
You could use context as the `globals` input, and then selectively purge
unwanted keys from it each time the eval/exec completes.

This gets hairy. You'd have to snapshot context before `eval`/`exec`, and then 
remove the delta after the dynamic code completes. You could add some cuteness 
like a `save_me` to allow the dynamic code to specify new vars that should 
persist.

```python
source = """\
from math import sqrt
x = 123
y = 456
z = 789

save_me = {'x', 'y'}
"""

context = {'a': 'b', 'c': 'd'}
# .keys not helpful, because it mutates. Thus unpack into new set.
keys_snapshot = set(context)
# x, y, z, sqrt, save_me, __builtins__ added to context
exec(source, context)

# don't del while iterating
to_save = context.get('save_me', None)
if to_save:
    save_me = keys_snapshot | to_save
else:
    save_me = keys_snapshot

for var in (set(context) - save_me):
    del context[var]

# now context is:
# {'a': 'b', 'c': 'd', 'x': 123, 'y': 456}
```

`save_me` here is just for demo purposes, it'd be better to use a lambda to
avoid adding `save_me` as a magic reserved context key that pipeline authors
can't use.

For `eval` you'd follow much the same approach, with the additional complication
that there is a pre-existing globals dict with namespace imports to subtract
from context after it completes, and `save_me` is irrelevant.

Quite other than that this is subjectively an annoying amount of footwork (very
big brain technical term there):
  - You're adding multiple dict iterations for set conversion and set operations
    to union and diff. Although for perf + memory it probably doesn't matter too
    much for `pypyr.steps.py`, for `!py` strings this has the potential to have
    a bigger impact.
  - Although specified new variables will get added to context with something
    akin to `save_me`, it's not obvious to the pipeline author that using a
    local inside the dynamic expression will overwrite an existing key in
    context.
  - A seemingly unrelated statement like `import math` will overwrite an
    existing key `math` in context.

### Use a custom object as globals namespace
How about creating a custom dict-like object that will allow pypyr to re-use 
Context without copying it, while still keeping locals & imports from the
dynamic code separate so that it doesn't pollute context?

A
[ChainMap](https://docs.python.org/3/library/collections.html#collections.ChainMap)
looks ideal for this situation. You can combine multiple dicts without the
performance overhead of making a full copy of context first.

Except, from Python documentation on both `eval` & `exec`. . .
> If only globals is provided, it must be a dictionary (and not a subclass of
> dictionary), which will be used for both the global and the local variables.
> If globals and locals are given, they are used for the global and local
> variables, respectively. If provided, locals can be any mapping object.

Succinctly put, although `locals` can be any mapping object, `globals` _must_ be
a dict.

This is not quite true. The Python core was patched in 2012 quietly to support
dict subclasses (basically, will respect overridden `__getitem__`, which means
`MutableMapping` instances like `ChainMap` will work.) This was not the direct
intent of the patch, but it was a side-effect of it.

https://bugs.python.org/issue14385

> use PyObject_GetItem when globals() is a dict subclass, but LOAD_NAME,
> STORE_GLOBAL, and DELETE_GLOBAL weren't changed. (LOAD_NAME uses
> PyObject_GetItem for builtins now, but not for globals.)

This comes with the caveat that:

> This means that global lookup doesn't respect overridden __getitem__ inside a
> class statement (unless you explicitly declare the name global with a global
> statement, in which case LOAD_GLOBAL gets used instead of LOAD_NAME).

This is notwithstanding a 
previously rejected enhancement patch from 2006
https://bugs.python.org/issue1402289 to provide full `Mapping` compatibility. 
Also, this: https://bugs.python.org/issue32615 - dict subclasses will work in 
some places, but not everywhere and whether they do or not is an implementation 
detail of the particular Python compiler. 

### class-level access to global variables
Using a derived dict means that accessing a global variable in the class scope 
itself will fail.

```python
# ---------------------------------------------------
# this works
source = """\
class MyClass():
    b = a + 1
    a = 456

print(MyClass.a) # == 456
print(MyClass.b) # == 124
"""

actual_dict = {'a': 123}

exec(source, actual_dict)
assert actual_dict['a'] == 123
assert actual_dict['MyClass'].b == 124

# ---------------------------------------------------
# this doesn't work
# in a derived dict with overridden getitem will fail
# if not explicit global with:
# NameError: name 'a' is not defined


class MyDict(dict):
    def __getitem__(self, key):
        return 123 if key == 'a' else dict.__getitem__(self, key)


source = """\
class MyClass():
    global a # will fail with NameError 'a' if this not here
    b = a + 1
    a = 456

print(a) # == 123, thanks to custom __getitem__
print(MyClass.b) # == 124
"""

derived_dict = MyDict(x=123)
exec(source, derived_dict)
assert derived_dict.get('a') == 456  # .get bypasses __getitem__
assert derived_dict['MyClass'].b == 124
```

Do note that this limitation is only the case for class-level attributes.
Top level scope, enclosed scopes in functions or even inside class methods will 
work with the overridden global lookup:

```python
# these all work
print(a)

class MyClass():
    def mymethod(self):
        self.b = a + 1

def myfunction(x):
    return a + x
```

While this is not great, arguably this is not the end of the world. The
workaround is not only easy enough (i.e put it inside a method), but arguably
the more common way of coding: especially within the context of what dynamic
code does in pypyr - this is for pipelines to execute bits of helper code and
will pretty much follow a functional programming style idiom.

This limitation only applies to `exec`, not `eval` - simply because you can't 
define classes in `eval`.

But still, it is an annoying and, to the uninformed end-user, surprising
limitation.

### adding __builtins__ to global scope
Other than using globals in class scope, the other bit that requires an actual 
dict rather than a dict sub-class is adding built-ins to the global namespace.

The actual exec/eval source (eval 927-934, exec ln 1004 - 1013):
https://github.com/python/cpython/blob/master/Python/bltinmodule.c

```c
int r = _PyDict_ContainsId(globals, &PyId___builtins__);
if (r == 0) {
    r = _PyDict_SetItemId(globals, &PyId___builtins__,
                          PyEval_GetBuiltins());
```

So since this isn't using `PyObject_GetItem` & `PyObject_SetItem` etc., this 
will _not_ honor overridden `__getitem__` in dict subclasses.

Now, this is not necessarily a problem. Because as long as the `__builtins__`
key can get/set on the object via the PyDict accessors it's fine, regardless of
what the overridden `__getitem__` does.

### Using a chainmap as globals namespace
Armed with the above, we can use composition to make dict that will work as a 
dict for `__builtins__` but still provide custom getitem/setitem accessors for 
other namespace calls.

```python
import builtins
from collections import ChainMap


class ChainMapDict(dict):
    """Dict that uses both the underlying dict and a ChainMap for storage."""

    def __init__(self, *maps):
        dict.__setitem__(self, '__builtins__', builtins.__dict__)
        self.chainmap = ChainMap(*maps)

    def __setitem__(self, key, item):
        print(f'__setitem__ {key=} {item=}')
        self.chainmap[key] = item

    def __getitem__(self, key):
        print(f'__getitem__ {key=}')
        return self.chainmap[key]

source = "x = abs(a)"

d1 = {'a': -123}
d2 = {'c': 'd'}

dict_with_chainmap = ChainMapDict(d1, d2)

exec(source, dict_with_chainmap)

# the dict itself only contains __builtins__
print(dict_with_chainmap.keys())
# dict_keys(['__builtins__'])

# the actual namespace add/edits are in the chainmap's underlying dicts
print(dict_with_chainmap.chainmap)
# ChainMap({'a': -123, 'x': 123}, {'c': 'd'})
```

Do note to use `builtins.__dict__` rather than `__builtins__` to get a handle on
the builtins dict - `__builtins__` is an [implementation
detail](https://docs.python.org/3/library/builtins.html) and varies between
python running as a script, interactively or in a package.

This approach will still have the issue that class-level global reads won't
work, unless the global is in the `dict` itself, not in the `ChainMap`. For what
we're trying to achieve here, using `Context` as the underlying dict would mean
adding the `__builtins__` key to context, which is another thing we're trying to
avoid.

A side-effect of this is that `__builtins__` won't be available to the dynamic
code. Executing built-in functions work, but if the code for some reason wants
to do `__builtins__.abs(-1)` rather than `abs(-1)`. This is probably unusual
enough not to worry about - I can't quickly think of too many compelling reasons
why anyone would _want_ to use `__builtins__` as an accessor in their code other
than if they want to bypass an identical name in local scope.

Also, above excerpt is a bit naive - you're going to have to over-ride dict 
much more to get some consistency & avoid surprises for things like contains
and equality checks:

```python
import builtins
from collections import ChainMap


class _DictWithChainMap(dict):
    """Dict that uses both the underlying dict and a ChainMap for storage.

    Don't Use Me. Seriously.

    The only reason for this is to use as globals with eval/exec. Because
    eval/exec only accepts dict type as globals argument.

    However, for the purposes of pypyr, rather than make a whole copy of the
    context dict each and every time a py expression evaluations, it's much
    more performance efficient to use a chainmap to chain together the dynamic
    code's global namespace and context.

    That does not mean what you see here is a good idea. It's not. It's the
    least bad of other bad options.

    Don't pickle me. Re-instantiate instead.

    There are 2 storage mechanisms here:
    - the dict instance itself
    - the _chainmap property (a list of dicts, basically.)

    __getitem__ and __setitem__ uses the _chainmap. all other accessors (e.g
    .get(), .items()) uses the dict instance itself.

    See docs/adr/0001-namespace-on-eval-and-exec.md
    """

    def __init__(self, *maps):
        """Initialize the dict to builtins, and the chainmap to *maps."""
        # preloading __builtins__ means doesn't have to be added on each
        # eval/exec invocation.
        dict.__setitem__(self, '__builtins__', builtins.__dict__)
        self._chainmap = ChainMap(*maps)

    def __contains__(self, key):
        """Key exists in the chainmap or in the instance."""
        return key in self._chainmap or key in self.keys()

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.items() == other.items() and
            self._chainmap == other._chainmap
        )

    def __getitem__(self, key):
        """Get from the chainmap rather than the underlying dict."""
        return self._chainmap[key]

    def __len__(self):
        """Combine the len of all dicts in chainmap, but not the instance."""
        return len(self._chainmap)

    def __setitem__(self, key, item):
        """Set in the chainmap rather than the underlying dict."""
        self._chainmap[key] = item

    def __repr__(self):
        """Chainmap is the important part for repr & to reinitialize."""
        return (f'{self.__class__.__name__}('
                f'{", ".join(map(repr, self._chainmap.maps))})')
```

### using multiple inheritance
Instead of composition, you could also be super lazy and just do this with
multiple inheritance:

```python
class _ChainMapPretendDict(ChainMap, dict):
    """It's a ChainMap. But it will pass an isinstance check for dict."""

    def __init__(self, *maps):
        """Initialize the dict to builtins, and the chainmap to *maps."""
        dict.__setitem__(self, '__builtins__', builtins.__dict__)
        super().__init__(*maps)
```

Because the `ChainMap` is first in the MRO, it will override most (but not all)
of the dict's methods without pypyr having to implement a lot of boilerplate to
reroute the `MutableMapping` members to the `ChainMap` instead like it has to
with the composition example given previously.

It's maybe not particularly clear to a casual observer that the `ChainMap`
somehow _also_ has a dict hash-table storage associated with it where cpython
`PyDict` get/set methods will end up persisting.

In a perfect world it would be nice to add the dict instance itself as one of
the maps to the `ChainMap`, but passing in a reference of self to the ChainMap 
leads to recursion trouble: `self.maps.append(self)`. And I don't see any way 
of getting a reference to the underlying dict itself.

It might be an idea to put context itself into the underlying dict so that
class-level global references will work. But, if you're going to unpack context
into the underlying dict here, you might as well stick to the more recommend
route of creating a new, normal dictionary because you're incurring the
iteration+copy overhead anyway:

```python
globals = {'__builtins__': builtins.__dict__}
context = {'a': 'b', 'c': {'c1': '123'}}
globals.update(context)
```

## Decision
Because comprehensions is one of Python's most powerful features, and losing
with a mysterious error a chunk of this functionality when these nest is
needlessly hampering pypyr providing useful & compact expression of logic to
pipeline authors:

- pypyr should inject context into `globals` for both `eval` & `exec`. This is
  to ensure nested scopes resolve as expected.
- `globals` should contain `__builtins__`, referring to the builtins dict.
- `eval` & `exec` shouldn't add anything to context that the pipeline didn't
  explicitly ask for.

Therefore, 
- `eval` will use a `ChainMap` that can pass as a `dict` via multiple
  inheritance.
  - Because `eval` is only for expressions, the limitation of this approach
    regarding class level globals is not relevant - you can't declare a class in
    an expression.
  - Since `!py` strings, which use `eval`, are potentially all over the
    pipeline, including in tight loops, it's more sensible for performance to
    use a `ChainMap` to avoid the overhead of unpacking/copying the full context
    on each evaluation.
  - Given how long the undocumented ability to use derived dicts as a namespace
    for evals has been around, it's _probably_ safe to assume it's not going to
    taken away anytime soon. If it does, the remedy is simple enough - revert to
    the (more inefficient) `dict` + shallow copy, which comes down to 2-4 lines
    of code.
- `exec` will use a standard `dict`, with the contents of context shallow copied
   in.
  - Although this will have a performance impact for CPU (iterating context to
    make the copy) and memory (the copy itself) compared to using a `ChainMap`,
    this is the lesser evil since it avoids the surprising behavior on class
    level globals when using the `ChainMap` approach.
  - The performance impact is not as important as for `eval`, since a py step
    does not have as much ubiquitous use as a py-string.
  - Additionally, although in the case of `eval` the benefits of `ChainMap`
    outweigh the negatives, Python official documentation explicitly does not
    allow for `dict` or `Mapping` sub-classes. So it is strictly speaking the
    more proper supported option anyway.