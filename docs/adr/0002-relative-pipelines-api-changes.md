# Relative pipelines & API changes
## Why do this?
The idea is to use paths relative to the parent pipeline instead of resolving
everything from $PWD when parent pipelines use `pype` to call child pipelines.

This allows portable pipeline directories - so you can more easily create
shared/common pipeline libraries _without_ requiring `pip install` of custom
code 1st.

You'd be able to have a directory `/common`, and `pype` those pipelines from
elsewhere. Any custom collateral that the pipelines need, such as custom steps,
can exist in the shared pipeline directory _without_ the references depending
on where pypyr was called from originally.

```text
- root/
    - subdir/
        - pipeB.yaml
        - pipeC.yaml
        - customstep.py
    - pipeA.yaml
```

- `pipeA` calls `pipeB` like this: `subdir/pipeB`.
- `pipeB` can just reference its own dependencies relative to itself:
    - `pipeC` rather than `subdir/pipeB`
    - `customstep` rather than `subdir.customstep`

When everything sits under the same root directory, this doesn't seem like such
a big deal. But this will allow the invoked child pipeline + collateral to be
used anywhere else, meaning you open the door to have:

```
- /shared-pipelines/
    - mydir/
        - pipeB.yaml
        - pipeC.yaml
        - customstep.py
- /git
    - myproject/
        - pipelines/
            - pipeA.yaml
    - anotherproject/
        - pipeA.yaml
```

- You can now call your shared pipelines from anywhere:
    - Both of the `pipeA` pipelines live in their own respective projects.
    - Both of the `pipeA` pipelines can invoke `/shared-pipelines/mydir/pipeB`
    - `pipeB` can just reference its own dependencies relative to itself:
        - `pipeC` 
        - `customstep`
    - If you did NOT have this change, you couldn't run `pipeA` which uses
      `pype` to call `pipeB` from either of the project directories. So this
      won't work:
        - `/git/myproject/pipelines> $ pypyr pipeA`
        - `/git/anotherproject> $ pypyr pipeA`

Now your shared pipelines will work from wherever you call them. Much rejoicing!

## How it currently works
pypyr currently resolves all pipelines and custom modules like steps/context
parsers/loaders from a single path - the current working directory (which is to
say $PWD (aka wherever pypyr is invoked from).

This is a bit of a legacy feature, which has been overtaken by events.

This makes pipelines less portable than they should be. When you have parent
pipelines calling child pipelines via `pypyr.steps.pype`, it means the child
pipeline has to be coded with paths relative to the $CWD, effectively making
it the child's responsibility to understand from where it is called.

```text
- root/
    - subdir/
        - pipeB.yaml
        - pipeC.yaml
        - customstep.py
    - pipeA.yaml
```

So at present:
-  `pipeA` calls `subdir/pipeB`.
- `pipeB` has to reference its own dependencies relative to the root directory
    - `subdir/pipeC`
    - `subdir/customstep`

Therefore `pipeB` will only work when pypyr is calling from the `root`
directory, and from nowhere else.

As it stands, if you want this to work when you call `pipeB` directly, you have
to invoke pypyr like this:

```console
$ pypyr subdir/pipeB --dir path/to/root
```

or in the case of the api

```python
from pypyr import pipelinerunner
context = pipelinerunner.main_with_context(pipeline='subdir/pipeB ', working_dir='path/to/root')
```

But this doesn't help if you want to use `pipeB` as a component by calling it
with `pype` from a different parent pipeline located somewhere else, because the
child will still resolve everything relative to the original parent working
directory. You still sit with the problem that the child is not truly an
independent component, it relies on being called from the right place.

You could pass `--dir` to reference the invoked child pipeline's parent and
construct a relative path for the root pipeline-name from there, but this
is not intuitive at all.

## Proposed Changes
There are 3 main functional areas to change:
- Remove the `WorkingDir` global to make parent directory specific to a running
  instance of a pipeline.
- Resolve child pipelines relative to the parent on `pype`
- Load Python modules relative to the current pipeline's path.

This will be involve a breaking change and thus a major version number increase.

### Remove WorkingDir global
The `working_dir` cli/api input currently sets a global `WorkingDir` property.

This has the side-effect that a pypyr session can effectively only have one
`WorkingDir` at a time. It so happens this has not caused problems so far -
mostly because all API consumers I have seen so far have just had all their
pipelines + collateral in the same place, and maybe that the calling environment
is effectively single-threaded or not contentious enough that it's been a
noticeable issue even in cases where the dir does change between calls.

But it is misleading to allow:
```python
 pipelinerunner.main('mypipe', working_dir='mydir')
 pipelinerunner.main('mypipe2', working_dir='mydir2')
 ```

In a multi-threaded environment this can and will cause problems, because
`working_dir` is a shared global.

Change this to make the dir truly local & contained to the called function.

### Resolve child pipelines relative to parent
The `pype` step will need to be aware of the parent pipeline's location.

This means that the current pipeline (i.e the parent) has to be set on the
`Context` object.

A low-touch way of doing this is just to add a `.parent` property to the context
instance on `pype`:
```python
old_parent = context.parent
context.parent = 'newparenthere'
# run child pipeline here, and then. . .
context.parent = old_parent
```

But this is brittle:
- Assuming we're only interested in passing a single attribute around, maybe
  this is not so bad, but as more cascading attributes get added this gets
  silly. As it is, `parent` would be joining `pipeline_name` and `working_dir`,
  so there are already 3 separate properties of which to keep track.
- This is only relevant to the file-loader, so you'd need some extra checks for
  other/custom loaders.
- you'd have to code carefully with error handling to make sure the parent
  always resets even when the child pipeline doesn't complete as expected.
- There would have to be a separate initialization of all properties on the root
  pipeline's initialization, and then again on `pype`. And then again on error,
  in case of unexpected termination of the child pipeline.

This problem is better solved by introducing a call-stack for the pipeline
call-chain:
- Add a `Pipeline` class to model the run-time properties of a currently 
  running pipeline - such as its `name` and `path`.
    - The `Pipeline` instance references a shared `PipelineDefinition`, which
      contains the pipeline body.
    - The `PipelineDefinition` is a unique cached reference to the expensive
      results of the pipeline's yaml parsing & loading. It has to be unique to
      the loader - i.e `pipeA` loaded from the file-system refers to a different
      thing than `pipeA` loaded from `s3` or somewhere else. 
    - Make the loader responsible to set whether to cascade the `parent` down
      to the child pipeline by having a `LoaderInfo` class associated with the
      `PipelineDefinition`.
- Add a call-stack of running `Pipeline` instances in the pipeline call-chain.
- Use a context manager clearly to set the scope of a currently
  running Pipeline on the `Context` object, so that `context.current_pipeline`
  at all times contains the current pipeline's properties.

This grants the opportunity for a few more improvements:
- Currently `pypyr.pipelinerunner` is coded in a largely stateless FP 
  paradigm, where there is a chain of FIVE different functions slinging pretty
  much the same set of 7-8 arguments around between them.
    - Note that `working_dir` somewhat messily currently is global.
    - Since the new `Pipeline` class models all the run-time parameters for a
      pipeline, `pipelinerunner` can massively simplify its current convoluted
      logic by just using the single `Pipeline` instance rather than having to
      fling the same ~8 arguments separately across multiple functions.
    - A single `run()` function can replace the current `pipelinerunner` 4-5
      daisy-chained functions.
- Wrap loaders in a new `Loader` class, which contains its own pipeline cache.
    - Get rid of the general pipeline cache, because the pipeline cache(s) are
      now each scoped to a specific loader.
    - The loader decides whether a `parent` property is even relevant and
      whether to cascade it by setting a boolean `is_cascading`.
    - It does so be setting the `LoaderInfo` class on the `PipelineDefinition`
      it creates.
    - For backwards compatibility & ease of use, if a loader returns a bare
      pipeline yaml body instead of a `PipelineDefinition`, the pypyr core will
      wrap the pipeline yaml into a `PipelineDefinition` with a set of of
      default `LoaderInfo` properties.
  
For backwards compatibility, keep $PWD as a fallback look-up location for the
file loader, so the lookup order is:
1. Parent dir
2. CWD
3. CWD/pipelines
4. {Pypyr Install Dir}/pipelines

Steps 2-4 are the same as ever, so by and large existing pipelines should
just keep on working as before.

### Load Python modules relative to the current pipeline
The file loader will add the pipeline's parent directory to `sys.path`.

This allows users to load ad hoc custom modules _without_ having to
install these into the current environment first.

Additionally, the `dir` input now instead refers to `py_dir`. pypyr adds
`py_dir` to `sys.path`. 

Previously `dir` would ALSO mean pipeline yaml files resolve relative to it,
but the new `py_dir` only refers to Python modules.

Thus, previously these two cli calls would both load `./mydir/mypipe.yaml`:
```console
$ pypyr mypipe --dir mydir
$ pypyr mydir/mypipe
```

Whereas now
```console
$ pypyr mypipe --dir mydir
```

means:
- load `./mypipe.yaml`
- look in `./mydir` for custom modules

#### maybe not use sys.path
But why use `sys.path` at all? I investigated extensively using `importlib`
instead. It gets hairy.

In a perfect world, module references should be scoped relative to the pipeline
itself. Thus `dir1/pipeA` and `dir2/pipeB` can both reference an identically
named local `mystep` without clashing:

```text
- dir/
    - pipeA.yaml
    - mystep.py
    - sharedcode.py
- dir2/
    - pipeB.yaml
    - mystep.py
- pipeC.yaml
```

There are two important principles with which to contend:
- Python expects module + package initialization to happens once and once only.
- Python expects that module names are unique.

The Python core enforces these conditions by using the `sys.modules` dict.

But, per example above, `mystep` can only be unique in `sys.modules` if it's
qualified by a package reference, which is very thing we're trying to avoid.

So to keep imports X1, pypyr would effectively have to by-pass `sys.modules`
and maintain its own object cache reference PER PIPELINE.

To bypass `sys.modules`, pypyr has to bypass the usual recommended
`importlib.import_module` and/or `importlib.util.find_spec` in favor of
lower-level calls.

This would look something like this:

```python
parent_path, module_name = self.parse_name(full_name)
spec_paths = [str(parent_path), str(work_dir)]

for meta_importer in sys.meta_path:
# find spec stores paths it found in sys.path_importer_cache...
    spec = meta_importer.find_spec(name, spec_paths)

    if spec is not None:
        print(f"found spec with {meta_importer=}")
        break
else:
    print("not found in any meta_path find_spec")

if spec:
    # purposefully NOT inserting into sys.modules - to allow same bare name in different dirs
    # sys.modules[module_name] = mod
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
else:
    # import_module has its own cache already - aka sys.modules
    module = importlib.import_module(name)
```

This is the bare minimum just to show the broad strokes - but it still does not
recursively import a module's parents, as is normal for Python. I.e for
`mypackage.sub.mymodule` it won't initialize `mypackage` & `sub`.

This gets difficult. An API consumer might well have already imported a package
namespace the usual way and invoked pypyr later in that same session. If pypyr
uses modules in that package, it'd 1st have to check `sys.modules` for a
reference to avoid >1 `exec_module` on an already imported package, before
importing the module itself. pypyr would then have to maintain the imported
module in its own cache, uniquely identified by pipeline-name.

This gets even more difficult. Even though we now have a unique `pipeA+mystep`
module, and a separate `pipeB+mystep` module, `pipeC` might call `dir.pipeA`,
which already exists in `pipeA`'s module cache. So there'd also need to be some
sort of global pypyr module cache, _in addition to_ a per pipeline module
resolution mechanism. On top of checking `sys.modules`.

This gets even more difficult. If `mystep` uses the standard `import sharedcode`
directive to get to `dir/sharedcode.py`, this will NOT work unless pypyr also
intercepts the usual Python `__import__` (return top-level package) and
`import_module` (return module itself).

Of course, all of this would need to be thread-safe.

I can't shake the feeling that this is fighting against the very way in which
Python thinks about imports. The opportunities for subtle bugs are legion.

Quite other than performance implications for all these extra checks against a
fundamental mechanism like imports, the very sharp collective of Python
developers have carefully shaped & ironed out the core import utilities over 20+
years. For poor little pypyr to think it can do better all by its lonesome self
and just basically rewrite the entire import system in a few weeks is some
_wild_ hubris.

Appending to `sys.path`, even though clumsy in some respects, at the very least
does not incur this degree of risky open-heart surgery.

## Benefits
- pypyr's current API is the result of accretion over time. And with hindsight,
  in an effort to maintain backwards compatibility on each individual change,
  the cumulative effect of those changes over time has been needlessly to
  complicate things for consumers. It also needlessly complicates things for the
  pypyr core itself.
  - At present there are two different entry points (`main` and
    `main_with_context`), that work differently in subtle ways.
  - Future plans for pypyr include more functionality for loading pipelines
    from shared pipeline libraries or shortcuts specified in a `pyproject.toml`
    file, and this will be much easier to implement with a simpler call-chain
    for pipeline invocation.
- The current pipeline cache has a ~bug~ design limitation in that it assumes
  a unique pipeline name across all loaders. So if you called `pipeA` on the
  file-system, and later from a custom loader getting something called
  `pipeA` from somewhere else, it would over-write `pipeA` in the cache, and
  future callers might get the wrong pipeline when asking for `pipeA`.
- Simplify how `pype` works and get rid of the current clumsy code that does the
  side-shuffle with `pipeline_name` & `working_dir` on context.
- Allowing steps to access pipeline metadata, for example pipeline help text...
- `Step` wouldn't need a separate reference to `StepsRunner` anymore, it'd
  already be contained in `context.current_pipeline`.
- The future road-map for pypyr is looking to create shared pipeline libraries,
  allowing pipeline authors to use pipelines as components _without_ having to
  copy-and-paste. These changes are essential to make this work.
- API consumers can decide whether they want to make entries in `sys.path` or
  not just by passing `None` to `py_dir` and not using the default file loader.
    - This is relevant because especially those with custom loaders might well
      NOT want to effect changes to `sys.path` unnecessarily.

## Negatives
- This is a breaking change for API consumers.
    - Entry-point
        - `pipelinerunner.run()` replaces `pipelinerunner.main()` and
          `pipelinerunner.main_with_context()`.
        - A possible mitigation is to keep the current `main` and
          `main_with_context` entry-points and make some assumptions about what
          the caller means by `dir` and call into the new code with that under
          the hood.
        - BUT, given that the function signature for these is already changing
          in that `dir` now does NOT mean the same thing anymore, I believe it's
          the lesser evil explicitly to break the API with a major version no.
          increase, rather than implicitly "keep it working" where
          `main`/`main_with_context` is not quite doing what you think it's
          doing under the hood.
        - The client code change to make the new API work is relatively simple,
          so it's more the case that consumers check & verify that the new
          dispensation won't cause problems than causing hours of work in and of
          itself.
        - `pipelinerunner.main('pipe', working_dir='/dir')` becomes
            `pipelinerunner.run('pipe', py_dir='/dir')` 
    - Custom loader signature
        - The custom loader signature changes from
          `def get_pipeline_path(pipeline_name, working_directory)` to
          `def get_pipeline_path(pipeline_name, parent)`
        - We could keep backwards compatibility here by just keeping the
          "working_directory" name and use it as "parent". But this introduces
          confusion over what the badly-named argument actually means, and given
          that the major version increase is a rare opportunity to set right the
          accreted regrets of the past, lets not introduce another "legacy"
          weirdness in the code-base.
- This is a breaking change for cli consumers using the `--dir` flag.
    - This is unavoidable.
    - The only mitigation is that I have rarely seen anyone even be aware that
      this `--dir` switch exists. CLI clients generally go
      `$ pypyr mydir/mypipe` rather than `$ pypyr mypipe --dir mydir`.
    - For those that do, the change in practice to make it work is minor:
        - pipeline yaml references is amenable to update with find & replace.
        - cli invocation becomes `$ pypyr mydir/mypipe` rather than `$ pypyr
          mypipe --dir mydir`.
- This _could_ a breaking change for pipeline authors that use `pype`.
    - `pype` will only break in some cases when the containing pipeline was
      called with `working_dir`.
    - This aside, the mitigation is that the pipeline sequence and custom module
      look-up will still fallback to look in $CWD, which means that mostly
      currently working pipelines will keep working as before.


## Decision
Make it so.

Breaking changes are annoying and I try very hard to be sure that pypyr
maintains backwards compatibility. So this decision I did not take lightly.
Further mitigation, there was ~9 months for feedback on Discussion
post #221 on this topic.

In this case, I believe the positives outweigh the negatives. As is, new
functionality that will broaden pypyr's usability & power is being held back by
the cumulative effect of older code that has been overtaken by events.
