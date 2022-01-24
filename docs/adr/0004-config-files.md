# Config file locations
## Why do this?
For pypyr to be more configurable it has to be able to read settings from a
configuration file. This is not only for run-time configuration values like
default settings, but also to allow an operator to add extra functionality like
create shortcuts to pipeline calls with complex input arguments or to add extra
pipeline location look-up locations.

Where exactly to save a CLI tool's config file is a potentially controversial
decision. There are a lot of opinions & arguments about different users'
preferences vs standards for the various operating systems.

This ADR discusses the options and outlines the decision making process.

## Requirements Wish-list
In a perfect world, pypyr should:
1. Look for config in the current directory first
2. Look for config in `pyproject.toml`, if it exists
3. Then fall-back on per-user configuration
4. Then fall-back to system-wide configuration
5. Merge the combined effective config of all the above in order of precedence
   1-4.
6. All config is optional. pypyr must run out-of-box with no further
   intervention required.

Per-user means specific to a user on the system - i.e the current authenticated
user.

In a truly perfect world, per-user and system-wide config file locations would
be standard across the different O/S platforms. . .but it isn't, and thus this
document.

## Platform specific config file locations
## POSIX
On POSIX systems this is easy enough - the
[XDG Base Directory specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
is for exactly this.

This covers all the Linuxes.

## MacOS
Apple's
[Library directory specification](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileSystemOverview/FileSystemOverview.html#//apple_ref/doc/uid/TP40010672-CH2-SW1)
defines where MacOS expects application config and data files.

A superficial reading of the spec might suggest that app config files belong in
a `Preferences` directory, where shared config files is `/Library/Preferences`,
and user specific config go to `~/Library/Preferences/`. This is a pretty common
interpretation online on Stackoverflow, blogs & it is even pretty common in
helper libraries specializing in returning user directories.

BUT, the `Preferences` directory actually takes `plist` files, not any old
application config file, and in fact, the official guidance _explicitly_ states
"You should not create files in this directory yourself" - the idea is to use
the dedicated MacOS/iOS API to get/set preferences here, not to use it as a
store for arbitrary configuration files.

Per the spec, then, the `Library/Application Support` directories is the
official place for arbitrary user-generated configuration files - "you might use
this directory to store app-created data files, configuration files, templates,
or other fixed or modifiable resources that are managed by the app".

Now, all of that said, it is very common for CLI apps on MacOS to follow more
POSIX-y ways of doing this - typically in dotfiles directly in the home
directory such as `~/.gitconfig` and `~/.zshrc`, or in the XDG config dir like
`~/.config/iterm2`, `~/.config/fish` and `~/.config/oh-my-zsh`.

Note that while the XDG_CONFIG_HOME location (`~/config/appname`) _is_ very
common for CLI apps, the XDG_CONFIG_DIRS default `/etc/xdg` for system-wide
config is not at all. Apple's guidance recommends `/Library/Application
Support/appname` for system-wide "all users" config. Additionally, a quick look
at the directory listing in `/etc` on MacOs shows only system provisioned
utilities and gives a (admittedly unquantifiable) don't-mess-with-me vibe.

So as a CLI app, leaning on the XDG_HOME_DIR spec, defaulting to
`~/.config/pypyr/` for per user config, puts pypyr in good company, and then the
system wide fallback should probably be the Mac-recommended `Library/Application
Support/pypyr/`. In some ways this is the worst of all options in that we're
ignoring the official MacOs guidance in some places, and also ignoring the XDG
Base Dir spec in other places; instead using some feel-good amalgamation of
both. In other ways, it feels sensible and un-annoying for a CLI tool. This is
clearly not a very empirical argument, but hey, I can't be the only dev using
Mac because you get that Linux-y goodness with the bonus of a slick desktop
experience, without having to worry about a Wayland compositor for your window
manager and recompiling misbehaving wifi drivers.

## Windows
On Windows user-specific config goes to `AppData` (`%LocalAppData%`) or
`AppData/Roaming` (`%AppData%`), and `ProgramData` (`%PROGRAMDATA%`, aka
`%ALLUSERSPROFILE%`) is for system-wide configuration.

Here is Microsoft's official word on
[Windows default known folders](https://docs.microsoft.com/en-us/windows/win32/shell/knownfolderid).

Whether or not to use roaming does not have an easy answer - roaming profiles
can take a long time to sync on user sign-in/off, there are size limits & you
might hamper other (more essential?) applications the operator's network
administrator associated with the login.

So I'm not convinced that a pypyr config file _should_ roam by default - for
one, it's making a potentially annoying assumption on behalf of the user and
their network admins, for another, the file might well contain machine-specific
configuration that should NOT roam.

Looking into how notable CLI tools manage this, here is a github issue
discussion on [Windows application data folders for
npm](https://github.com/npm/npm/issues/4564#issuecomment-258986520) by an
experienced Microsoft consultant, who writes:

> it's a fairly accepted thing that in Windows, 'nix like commands having user 
> specific config put that under the user's home folder in . prefixed files, so
> if it ain't broke, don't fix it.

Two of the most obvious CLI apps on Windows are:
- AWS CLI - uses `%USERPROFILE%\.aws\config`
- Azure CLI - uses `%USERPROFILE%\.azure\config`

(`%USERPROFILE%` is the home directory. e.g `C:\Users\myusername\`)

Excerpt from the
[Azure CLI configuration](https://docs.microsoft.com/en-us/cli/azure/azure-cli-configuration)
guidance:

> The CLI configuration file contains other settings that are used for managing
> CLI behavior. The configuration file itself is located at
> $AZURE_CONFIG_DIR/config. The default value of AZURE_CONFIG_DIR is
> $HOME/.azure on Linux and macOS, and %USERPROFILE%\.azure on Windows.


Given that the Azure CLI is from Microsoft itself, I think we can sensibly make
the case that Microsoft also views the home directory as a good place for config
files for CLI applications, regardless of the general guidance pointing to
`AppData`/`LocalAppData`.

If this is the case, there could be a degree of consistency to how pypyr works
if it uses, similarly to the discussion above re MacOS,
`%USERPROFILE%\.config\pypyr\` as the default location for per-user config, and
then falls-back to the O/S specified default for system-wide config in
`%ALLUSERSPROFILE%\pypyr`.

ALLUSERSAPPDATA	is the same as CSIDL_COMMON_APPDATA.

> CSIDL_COMMON_APPDATA
> FOLDERID_ProgramData
> Version 5.0.
> The file system directory that contains application data for all users. A
> typical path is C:\Documents and Settings\All Users\Application Data. This
> folder is used for application data that is not user specific. For example, an
> application can store a spell-check dictionary, a database of clip art, or a
> log file in the CSIDL_COMMON_APPDATA folder. This information will not roam
> and is available to anyone using the computer.

By default `%ALLUSERSPROFILE%` is `C:\ProgramData` for Vista and later, XP was
`C:\Documents and Settings\All Users`.

## Environment variable
pypyr should allow the operator explicitly to over-ride these defaults by
specifying an explicit location for a config file in an environment variable
named something like `$PYPYR_CONFIG_FILE`.

The idea is that setting this environment variable to a path will replace the
per-user and system-wide config look-ups, but pypyr will still do the current
directory check first.

## Configuration file names
The obvious candidate is `pypyr-config.yaml`. This means that the file can live
inside a project in the root of the repo and not just in a pypyr specific
directory. Examples in the field include `swagger-config.yaml`,
`docker-compose.yaml`.

Alternatively, you could do `.pypyr/config.yaml` - in other words, the config
file goes into a `.pypyr` directory. In general, dotted directories are hidden
by default, and don't go into source control (e.g `.vscode/`, `.tox/`,
`.pytest_cache/`) but this is by no means a hard rule - e.g `.github/` for
GitHub Actions absolutely does go into source control. (Note in the case of tox
`tox.ini` is in the root of the repo and `.tox/` is effectively a temp dir.)

Another very common naming convention is a dotfile - something like `.pypyr` or
`.pypyr-config`. In the negative here is that some IDEs don't have a
straightforward way of associating a file format to files without extensions
like dotfiles, so you lose the auto-formatting, pretty colors and structural
error checking a full-powered IDE gives. But nothing stops you from adding an
extension, so `.pypyr.yaml` etc. Example in the field is `.travis.yml`.

## Configuration file format
Given how much pypyr uses YAML, it makes sense to have the default configuration
option use YAML files.

However, in the Python ecosystem a `pyproject.toml` file to consolidate project
related config is becoming more common. To prevent operators from needing a
special individual config file just for pypyr, and given that pypyr has TOML
parsing the core as of ADR-0003, pypyr should also check for a `pyproject.toml`
in the current directory.

Per [PEP518]( https://www.python.org/dev/peps/pep-0518/) custom tools should
store their config in `pyproject.toml` in the `tool` table, giving `tool.pypyr`
in this case.

As a general task-runner, pypyr is not as a matter of course wedded into Python
projects that necessarily have a `pyproject.toml` file - operators using pypyr
as a general automation tool very likely will not have one. Thus, having a pypyr
specific YAML config option provides more user flexibility without making YAML
pipeline authors have to learn TOML too.

As long as the toml and yaml config parses to the same `dict` structures, which
it should, it isn't a significant technical burden supporting both.

## Order of precedence
Having general system-wide configuration that a user or a project can over-ride
is useful. To this end, the config source order of precedence should be:

1. ./pypyr-config.yaml
2. ./pyproject.toml
3. {user config dir}/pypyr/config.yaml
4. {shared config dirs}/pypyr/config.yaml

The idea is that the specific pypyr config file will over-ride `pyproject.toml`.
This will allow operators to check shared config into a source control repo
while still over-riding settings for their individual/specific local machines by
adding their own `pypyr-config.yaml` next to the `pyproject.toml` file.

Similarly, a project-specific config in the current working directory overrides
user-wide config, which over-rides system-wide config.

## Dynamic Properties
The config parser could allow dynamic properties - i.e it'll pick up any given
property the operator decides to add, rather than only allow known properties.

On the plus side, this would allow maximum flexibility, which is very much in
keeping with the general pypyr philosophy.

However, the negative is that typos will be harder to spot and could lead to
surprising behavior that is difficult to troubleshoot - because a mistyped
property or misconfigured input file would just result in pypyr blindly
creating the wrong inputs as given.

It might therefore be a better idea to fail immediately with a clear error
message if a config property is unexpected. Still to allow operators the
flexibility of creating their own properties, add a `vars` dict to the
expected/known properties, which the operator can use for _ad hoc_ custom
config properties.

## Decision
1. Check current directory 1st, in order, for
    - `./pypyr-config.yaml`
    - `./pyproject.toml` under table `tool.pypyr`
2. Thereafter, follow the XDG Base dir spec for and *nix, as much as possible
   for other platforms.
    - Per-user config reads from `~/.config/` on all platforms
    - Shared config
        - POSIX: XDG Base Dir spec
        - MacOs: `/Library/Application Support/`
        - Windows: `%ALLUSERSPROFILE%` (usually `C:\ProgramData``)
3. In the user/shared config dirs, look for `pypyr/config.yaml`
4. To mitigate upset where users have strong opinions about where config should
   live, environment variable `PYPYR_CONFIG_FILE` over-rides opinionated
   implementation of per user/shared config locations, while still doing the
   current directory look-up a usual.
5. All config is optional. pypyr work with sensible defaults without any special
   config intervention necessary.
6. Only allow known properties in config file with a clear explicit error on
   unexpected keys.