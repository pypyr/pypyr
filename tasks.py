"""Project CI/CD tools."""
from invoke import Collection

from ops import (
    bump,
    config,
    lint,
    package,
    pipeline_buildout,
    pipeline_bump,
    publish,
    tag,
    test,
)

ns = Collection()
ns.add_task(tag.tag, "pipeline_tag")
ns.add_task(pipeline_buildout.buildout, "pipeline_buildout")
ns.add_task(pipeline_bump.pipeline_bump, "pipeline_bumpversion")
ns.add_task(config.all, "config")
ns.add_task(config.show_version, "show_version")
ns.add_collection(lint)
ns.add_collection(test)
ns.add_collection(bump)
ns.add_task(package.all, "package")
ns.add_collection(publish)
