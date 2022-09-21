# Replace setup.py build front-end
## Why do this?
The legacy setup.py packaging build front-end is deprecated. pypyr has to move
to a supported and future-proof build & packaging mechanism.

The standard in scope is [PEP517](https://peps.python.org/pep-0517/).

> SetuptoolsDeprecationWarning: setup.py install is deprecated. Use build and pip and other standards-based tools

## Options
The obvious options are:
- [pypa build](https://pypa-build.readthedocs.io/en/latest/)
- [flit](https://flit.pypa.io/en/stable/)
- [poetry](https://python-poetry.org)
- [hatch](https://hatch.pypa.io/)

All of the above tools look great, have been around for years now and have
positive community feedback.

I'm not going to be delve too deeply into the options. The reason is that one of
the wonders of PEP517 is that theoretically you could replace the build
front-end with another PEP517 compliant framework down the line without too much
fuss. Therefore, it's probably not worth it to invest significant time in a
comparative analysis when the decision can be amended in the future without
disruption.

`poetry` and `hatch` are closer to project manager software and do a lot more
than just serve as a build front-end.

`build` and `flit` focuses just on simple build.

Rather than re-engineer how the entire pypyr build workflow works, I'm going to
stick to just replacing the build front-end. Therefore, `poetry` & `hatch`,
while great, are surplus to the immediate requirement. If pypyr later wants to
switch to these that would also be relatively smooth, since the real work here
is in provisioning the `pyproject.toml` file, which forms part of this current
change.

As of writing (21 Sept 2022) `build` still has several features in beta when it
comes to specifying build config in `pyproject.toml` - including specifying
`package_data`. This might necessitate keeping the old `setup.cfg` or `setup.py`
around to provide features that have not been officially released in `build`
yet, which somewhat defeats one of the benefits of moving to the new
`pyproject.toml` orientated streamlined format.

And that leaves `flit`. Some official Python tooling use `flit` to bootstrap
their own installs, so it's definitely a solid choice.

## twine
pypyr uses `twine` for package uploads to PyPI. `twine` also has a `check`
function that validates the project README.

All the discussed build tools provide a public or upload style function to push
the package to PyPi, negating the need for `twine`.

`twine` check only checks that `Description-Content-Type` is set, which `flit`
does do. `twine` check at present does not do any further validation on markdown
type README files, so there is no further functionality it provides that `flit`
is not doing itself.

## Decision
1. Replace deprecated `setup.py` build with `flit`.
2. Move as much config as possible to `pyproject.toml`.
3. Remove `twine` dependency.