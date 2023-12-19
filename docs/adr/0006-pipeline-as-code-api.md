# Pipeline as Code API
## Why do this?
### Wishlist
1. Validate pipeline structure without having to run pipeline
2. Define pipelines as code

### Validation
pypyr currently reads pipelines from yaml files. pypyr is very forgiving when
interpreting pipeline yaml - it parses step-by-step as it goes (or just-in-time,
if you will) and does NOT validate the entire yaml file's structure in advance.

This does make pypyr very flexible, in that it's not restrictive about the
over-all file's structure and is relatively fault-tolerant - even if one section
of a pipeline is not valid, other valid sections will still work.

However, this also means that pipeline authors only discover at runtime whether
there are structural errors in their pipeline yaml. pypyr currently has no way
of validating that a pipeline's structure is correct and runnable without
actually running the pipeline. This is annoying in long running pipelines
because it could burn a lot of time before pypyr reaches a later malformed step
in the pipeline and raises a formatting error. 

### Pipelines as Code
Additionally, API consumers want to construct pipelines in code, rather than
have to author in yaml. The original design objective with pypyr is that the
pipeline yaml is intuitive and meant for humans to author and read. This remains
the case and pypyr is in NO WAY getting rid of yaml pipelines - the design
principle of simple, intuitively human-readable yaml pipelines still obtains.

However, pypyr can provide an alternative for API coders to construct pipelines
in code. Currently API consumers construct pipelines in YAML, rather than have
typed pipeline definitions that will make it possible to create pipelines right
there in the code without having to switch context to a YAML file.

The plan is to augment the intuitive yaml pipeline authoring experience with a
similarly intuitive authoring experience in code.

## Proposal: Model Pipelines in Code
We can achieve both Wishlist items with least effort if we modeled the entirety
of a pipeline in classes in code.

### Model pipeline body
Expand the current DSL classes to encompass over-all pipeline structure.
Practically speaking, this means to create a `PipelineBody` class to compose
the already existing `pypyr.dsl.Step` classes.

- `PipelineDefinition` <-- exists already
   - `PipelineBody` <-- NEW
      - Sequence of `Step` <-- exists already

The `PipelineBody` initialization _is_ effectively the validation. If a
`mapping` can parse into a `PipelineBody`, it means it's a valid pipeline. This
will happen on loading the pipeline, so pipeline authors will know immediately
if there are problems with the pipeline, rather than have to wait until pypyr
reaches a step at runtime to know that it passes validation.

### in parameter validation
The does NOT validate the step `in` input, this remains just-in-time. This
does seem like an oversight, but here are the reasons:
1. Step `in` is dynamic. This is one of the strengths of pypyr. The step's `in`
args could be derived dynamically from other preceding steps in the pipeline -
we cannot know at design time what those values are or if they resolve as
expected. The values could only retrieve at run-time.
2. The Step signature is simple - it's just `def run_step(context)`. The idea is
to allow pipeline authors to create steps with a single function without having
to inherit from classes or do more intricate interface driven development. The
key objective is to be as low-code as possible. Whatever validation happens in a
Step happens in that same function, so we don't have an easy way to separate a
Step's validation from a Step running without breaking existing steps. A
proposal here _could_ be to introduce an optional `def validate(context)`
function that could introduce validation for a step as a separate step, BUT this
would be of limited use since it couldn't possibly validate dynamic inputs,
which is key to pypyr's power.

### Cache and Runtime consume modeled pipeline
Given that the new `PipelineBody` will contain a parsed, known-correct pipeline,
modify the pipeline cache and the run logic to consume the `PipelineBody`,
rather than consuming the unstructured `dict` representing the raw pipeline as
it was parsed.

Add API entrypoints for coders to run the `PipelineDefinition`, or even the
contained `PipelineBody` directly:

```python
def run_pipeline_body(
    pipeline_name: str,
    pipeline_body: PipelineBody,
    args_in: list[str] | None = None,
    parse_args: bool | None = None,
    dict_in: dict | None = None,
    groups: list[str] | None = None,
    success_group: str | None = None,
    failure_group: str | None = None,
    loader: str | None = None,
    py_dir: str | bytes | PathLike | None = None
) -> Context

def run_pipeline_definition(
    pipeline_name: str,
    pipeline_definition: PipelineDefinition,
    args_in: list[str] | None = None,
    parse_args: bool | None = None,
    dict_in: dict | None = None,
    groups: list[str] | None = None,
    success_group: str | None = None,
    failure_group: str | None = None,
    loader: str | None = None,
    py_dir: str | bytes | PathLike | None = None
) -> Context
```

### Validate from the CLI
Introduce a validate switch from the cli:

```
$ pypyr validate my-dir/my-pipeline

# or maybe
$ pypyr my-dir/my-pipeline --validate
```

### A new _meta section
Introduce a new reserved key-word `_meta`. Ad hoc yaml that is NOT structural
pipeline step-groups/steps will go under this new `_meta` key. The ultimate plan
is to use `_meta` for future plans to provide self-documenting pipelines with
`author` and `help` or `description` sections for usage instructions and the
like.

This is necessary because in the new dispensation pypyr will attempt to parse
the entire yaml and all of the yaml must conform to some sort of schema, because
if we're back to allowing arbitrary yaml in a pipeline it would defeat the
wish-list purpose of validation.

## Breaking Changes
1. No more ad hoc yaml in a pipeline - all yaml in pipeline must conform to 
   schema.
2. Custom loaders returning a `PipelineDefinition` will have to wrap a mapping
   (aka dict) into a `PipelineBody`. Note that loaders returning a `Mapping`
   (e.g a `dict`) will keep on working as before, no changes necessary.
3. Broken pipelines that used to run until they got to a structurally malformed
   step will now not run at all, rather than run until it hits the breaking
   point.
4. Existing pipelines with a `_meta` step-group will not work anymore.

### Limiting impact
pypyr does not lightly introduce breaking changes. They are annoying for anyone
downstream. We have to measure carefully whether the benefits are worth the
breakages. The goal is to minimize the scope and impact of breakages.

The breaking changes are the minimal necessary and inevitable to provide this
long-asked-for feature to pypyr. Most users will not even notice a difference
other than a more efficient development cycle with quicker validation feedback.

1. No more ad hoc yaml in pipelines - there might well be pipelines out in the
wild that use custom yaml sections for documentation, meta-data and yaml
anchors. Remedying these to work in the new dispensation will just be copy/paste
of the non-pipeline yaml to go under the new `_meta` reserved key.
2. Custom pipeline loaders are relatively rare out in the wild - most pypyr
users stick to the built-in `file` loader. And loaders returning dicts/maps
aren't affected at all, only ones using the relatively more recently introduced
`PipelineDefinition`. The code upgrade required here is minor - it's a one
liner, which will be marked clearly in the release notes.
3. Pipelines with broken steps are definitionally broken. Although we are
breaking backwards compatibility here in the strict sense, in that it could well
result in failures of pipelines that at least partly worked before upgrading,
this will be a major version upgrade and the change in behavior will be explicit
in the release notes. And even so, these pipelines would have failed reporting
the error, it's just that there might have been side-effects from preceding
steps before the failure condition: the operator will be aware that the pipeline
is quitting reporting failure and that it's not "working" well before this
"breaking change" arrives. The exception is if a pipeline contained steps (e.g
in a failure handler) that never ran before, in which case the operator might be
unaware that the pipeline contains broken steps. Even in this case, the
breaking change would highlight this problem and provide opportunity to remedy
in advance rather than have it become a problem only on the first iteration of
such broken steps.
4. Hopefully `_meta` is an unusual enough term for a custom group that it won't
clash with existing group-names. If it does, the fix is easy enough - just
rename to anything other than `_meta` - even a one character change to `meta`
will do. To minimize impact, will introduce an explicit error message to
make it clear to the operator why it's not working if there is an attempt to run
a `_meta` group.

## Alternative Options:
### Separate validator
Keep pypyr as it is, but create an entirely separate validator.

Pros:
- no breaking changes to the pypyr core

Cons:
- maintain pipeline structural logic in two different places
- can't create pipelines as code

### Separate model classes
Introduce an entirely new layer of model classes to model pipeline structure.

Map these models to existing dsl classes.

Pros:
- no breaking changes

Cons:
- have to maintain pipeline structure in separate places, and _also_ maintain
the mapping/translation between these.

### YAML schema
Create a YAML schema that code editors can use for syntax highlighting.

This does not actually build validation into the pypyr core, nor allows for
pipelines as code.

This is more of an optional extra we can do at a later date, regardless of the
current architectural decision.

## Decision
Implement proposal. The breaking changes are limited enough in scope compared
to the tangible benefits for the pypyr-verse.

## Related discussions
- [#139](https://github.com/pypyr/pypyr/pull/139) - PR to output more useful error info, discussing plans for validator
- [#116](https://github.com/pypyr/pypyr/issues/116) - Enhancement request to add a pipeline validator
- [#229](https://github.com/pypyr/pypyr/issues/229) - Enhancement request to add a schema file for pipeline yaml
- [#332](https://github.com/pypyr/pypyr/pull/332) - draft PR implementing a pipeline model that models pipelines as code