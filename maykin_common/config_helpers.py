from dataclasses import dataclass
from typing import Any

from decouple import Csv, Undefined, config as _config, undefined


@dataclass
class EnvironmentVariable:
    name: str
    default: Any
    help_text: str
    group: str | None = None
    auto_display_default: bool = True

    def __post_init__(self):
        if not self.group:
            self.group = (
                "Required" if isinstance(self.default, Undefined) else "Optional"
            )

    def __eq__(self, other):
        return isinstance(other, EnvironmentVariable) and self.name == other.name


ENVVAR_REGISTRY: list[EnvironmentVariable] = []


def config(
    option: str,
    default: Any = undefined,
    help_text="",
    group=None,
    add_to_docs=True,
    auto_display_default=True,
    *args,
    **kwargs,
):
    """
    An override of ``decouple.config``, with custom options to construct documentation
    for environment variables.

    Pull a config parameter from the environment.

    Read the config variable ``option``. If it's optional, use the ``default`` value.
    Input is automatically cast to the correct type, where the type is derived from the
    default value if possible.

    Pass ``split=True`` to split the comma-separated input into a list.

    Additionally, the variable is added to a registry that is used to construct
    documentation using Sphinx directives. The following arguments are added for this:

    :param help_text: The help text to be displayed for this variable in the
        documentation. Default `""`
    :param group: The name of the section under which this variable will be grouped.
        Default ``None``
    :param add_to_docs: Whether or not this variable will be displayed in the
        documentation. Default ``True``
    :param auto_display_default: Whether or not the passed ``default`` value is
        displayed in the docs, this can be set to ``False`` in case a default needs
        more explanation that can be added to the ``help_text`` (e.g. if it is computed
        or based on another variable). Default ``True``
    """
    if add_to_docs:
        variable = EnvironmentVariable(
            name=option,
            default=default,
            help_text=help_text,
            group=group,
            auto_display_default=auto_display_default,
        )
        if variable not in ENVVAR_REGISTRY:
            ENVVAR_REGISTRY.append(variable)
        else:
            # If the same variable is defined again (i.e. because a project defines a
            # custom default), override it
            ENVVAR_REGISTRY[ENVVAR_REGISTRY.index(variable)] = variable

    if "split" in kwargs:
        kwargs.pop("split")
        kwargs["cast"] = Csv()
        if isinstance(default, list):
            default = ",".join(default)

    if default is not undefined and default is not None:
        kwargs.setdefault("cast", type(default))
    return _config(option, *args, default=default, **kwargs)
