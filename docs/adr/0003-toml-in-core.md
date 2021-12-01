# Add TOML parsing to the core
## Why do this?
[TOML](https://toml.io/en/) is becoming a popular configuration format, and
unavoidably so in Python in the shape of `pyproject.toml` as accepted by
[PEP518](https://www.python.org/dev/peps/pep-0518/).

One of pypyr's better features is wrangling configuration files between text,
JSON and YAML for automation activities. Given TOML's recent rise in prominence,
it makes sense to add functionality to pypyr for the usual read, write and
formatting built-in steps.

Under consideration is 
1. Which TOML library to use
2. Whether to add the TOML dependency to the pypyr core or as a separate plugin?

## Which Python TOML Library is best?
Since "best" is a variable term best left to click-bait internet articles,
instead let's ask which TOML library more suits the current requirements of the
project with the least negatives.

### Selection criteria
1. [TOML 1.0](https://github.com/toml-lang/toml/releases/tag/1.0.0) was released
   on 2021/01/12. Most obvious criterion then is v1.0 compliance.
2. Works with standard pypyr Context formatting operations. This means that
   parsing output should use basic Python types, or is at least covariant with
   the basic types - especially `Mapping` & `Sequence`. This is to make sure
   that toml structures imports into Context and pipeline authors can use `set`
   and formatting expressions like they would for any other Context item.
3. Style (comments, whitespace) preserving round-trip parsing. This is nice to
   have to allow pypyr to work with replacing values in a user's TOML file
   without destroying the user's comments/whitespace.

### Python TOML libraries at a glance
- [tomli](https://github.com/hukkin/tomli)
  - Relatively fast read-only parsing.
- [tomlkit](https://github.com/sdispater/tomlkit) 
  - Round-trip white-space/style preserving.
- [toml](https://github.com/uiri/toml)
  - This was initially vendored in pip itself to deal with `pyproject.toml`.
  - Even so `pip` has since moved to `tomli`.
- [pytoml](https://github.com/avakar/pytoml)
  - Abandoned by the creator for eminently sensible reasons (interesting read
    too... https://github.com/avakar/pytoml/issues/15) But let's not get into an
    argument over whether a shiny new fashion in config formats is in fact doing
    anything better than the previous fashions in config management.
- [qtoml](https://github.com/alethiophile/qtoml)
  - Still on TOML v0.5.0.

Note these are the pure Python parsers - there are also a others using wrappers
for different underlying tech:

- [pytomlpp](https://github.com/bobfang1992/pytomlpp)
  - Python wrapper for the [toml++](https://marzer.github.io/tomlplusplus/) C++
    library.
- [rtoml](https://github.com/samuelcolvin/rtoml)
  - Python wrapper for fast parsing written in Rust.

#### TOMLKit
Of the available options, _only_ `tomlkit` supports style-preserving roundtrip
parsing. Furthermore, `tomlkit` was created for the express purpose of handling
TOML parsing for the [poetry](https://python-poetry.org) tool - as this is one
of the 2 most popular new PEP517 & PEP518 Python build systems there is some
comfort in the wide adoption of a very actively used tool that means a greater
likelihood of maintenance & support, and specifically that `pyproject.toml`
files _should_ parse without surprises.

TOMLKit only lists itself as `1.0.0rc1` compliant. Looking at the [TOML spec
release history](https://github.com/toml-lang/toml/releases/) delta of `rc1` vs
`v1`, it only looks like clarifications & administrative/documentation updates -
there doesn't _seem_ to be anything notable missing or functionally different in
`rc1` as opposed to `v1`. It's not impossible that I missed something, though -
but given `TOMLKit`'s wide usage via `poetry`, I would expect obvious
out-of-date spec handling to have been noticed by someone somewhere, and I see
none such in the [issues list](https://github.com/sdispater/tomlkit/issues).

There is a but... `TOMLKit` fails the third requirement - it is not
interoperable with the pypyr Context because it outputs custom types rather than
Python built-ins. Specifically it represents tables with classes like
`class Table(Item,MutableMapping, dict)` or
`class InlineTable(Item, MutableMapping, dict)`. 

(See here for [TOMLkit API types](https://github.com/sdispater/tomlkit/blob/master/tomlkit/items.py).)

The constructors for these do NOT allow any of these to instantiate like a
standard `Mapping` type does - which means that the pypyr Context formatting &
merge methods cannot work with structures loaded from TOML _unless_ we add
specific type handling for these. As a matter of principle, I am not cheerful
about having Context be more type aware than the basic type system and
`collections.abc` - `pypyr.context.Context` is a dependency for a lot of other
pypyr modules, but also, where does it end? Instead, if anything, Context would
need re-coding to create shallow copies + in-place update of the copy instead of
using the ctor to instantiate a new container for formatting output. This is not
a trivial change and has the potential to break fundamental functionality for
pretty much everyone.

That the TOML parser output interoperates with the pypyr Context is a more
important requirement than that it is style-preserving. Pipeline authors can of
course maintain style/whitespace while formatting TOML files by using either
`pypyr.steps.filereplace` and `pypyr.steps.fileformat` (the former in all cases,
the latter if the TOML contains no {} structural braces for inline tables).
Therefore, having a style preserving TOML parser is not essential in that pypyr
can already serve the functionality elsewhere.

#### toml
The `toml` library is a largely historical artifact at this point. Not only is
it well behind on implementing TOML v1, but also because of lack of maintenance
on functionality as is - even `pip` itself [has moved from vendoring `toml` to
`tomli`](https://github.com/pypa/pip/pull/10035). This exodus from `toml` to
`tomli` includes the very prominent:
- [pip](https://github.com/pypa/pip/issues/10034)
- [typeshed](https://github.com/python/typeshed/issues/6022)
- [black](https://github.com/psf/black/issues/2280)
- [mypy](https://github.com/python/mypy/pull/10824)
- [coverage](https://github.com/nedbat/coveragepy/issues/1180)
- [flit](https://github.com/pypa/flit/pull/438)

#### tomli
`tomli` then seems to be where the Python community in general is coalescing for
a standard TOML parser. `tomli` is read-only, for write functionality there is
the companion library [tomli-w](https://github.com/hukkin/tomli-w).

`tomli` is explicitly TOML v1.0 compliant.

`tomli` is _significantly_ faster than TOMLKit. It does not, however, preserve
style/whitespace like `tomlkit` does. For most use-cases, arguably TOML reading
is the important part...

## Plug-in or Core?
As for adding the dependency, there are two options:
- Add separate `pypyr.toml` plugin in its own repo.
- Add TOML parsing to the pypyr core itself.

pypyr has a [third party
library](https://pypyr.io/docs/contributing/contribute-to-pypyr/#roll-your-own-plug-in)
principle that _generally_ external dependencies should get their own repo, to
keep the pypyr core as light as possible.

However, on pypyr's roadmap is adding a configuration file for setting pypyr
run-time properties. Much as .yaml would be the more sensible format, given
pypyr already natively _lives_ in yaml, the increased adoption of
`pyproject.toml` in the Python eco-system not only by `setuptools` but also
widely used popular Python tools & libraries does mean that pypyr probably
shouldn't be the sole tool to demand users keep a separate .config file just for
it. A feature request for `pyproject.toml` has already come in.

So, were it the case that TOML parsing would only involve a context parser and
read/write/format steps, it definitely should isolate itself in its on repo. But
given the need to parse `pyproject.toml` as a core config store, it makes sense
to add it to the core.

The only remaining point to consider is whether to add the core dependency for
all pypyr installs, or to make the user specifically have to request the
functionality via `extras_require` - i.e `$ pip install pypyr[toml]`.

If pypyr is to pull core config information out of `pyproject.toml` as a default
start-up option, this is fundamental enough that I'm hesitant to introduce extra
installation friction to get this working without surprises. Given that at worst
the downside is having an unused TOML library in site-packages for what is
likely to be a dev virtual environment anyway & a slightly longer install time
(this in itself cached & fast because it is just a pure Python package), given
the amount of dependencies in a modern Python dev environment this is arguably a
drop in the ocean. Given how many `pyproject.toml` compliant tools use `tomli`
already, there is a pretty good chance the library will exist in a dev vevn
already anyway.

(Also, I get the sense I'm maybe one of the three last
people in this solar system who still even cares about whether a given library
is pulling in too many dependencies.)

## Decision
Add `tomli` + `tomli-w` to the pypyr core as part of the default install.
