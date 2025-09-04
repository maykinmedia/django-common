import warnings
from collections import defaultdict

from decouple import Undefined, undefined
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.states import RSTState
from docutils.statemachine import ViewList

from maykin_common.config_helpers import (
    ENVVAR_OPTIONAL_GROUP,
    ENVVAR_REGISTRY,
    ENVVAR_REQUIRED_GROUP,
    EnvironmentVariable,
)


def get_envvar(param_name: str) -> EnvironmentVariable:
    """
    Get an environment variable and its metadata from the registry by name

    :arg param_name: name of the environment variable
    :returns: the environment variable with metadata for documentation
    """
    var = next((v for v in ENVVAR_REGISTRY if v.name == param_name), None)
    if not var:
        raise ValueError(f"Envvar with name {param_name} not found in registry")
    return var


def get_envvar_group(
    group_name: str, members: list[str] | None = None, exclude: list[str] | None = None
) -> list[EnvironmentVariable]:
    """
    Get a list of environment variables and their metadata from
    the registry by group name

    :arg group_name: name of the environment variable group
    :arg members: name(s) of the environment variable to include from the group
    :arg exclude: name(s) of the environment variable to exclude from the group
    :returns: the list of environment variables with metadata for documentation
    """
    variables = [v for v in ENVVAR_REGISTRY if v.group == group_name]
    if members:
        return [v for v in variables if v.name in members]
    if exclude:
        return [v for v in variables if v.name not in exclude]
    return variables


def document_param(
    var: EnvironmentVariable,
    state: RSTState,
    default: str | None | Undefined = undefined,
) -> nodes.Node:
    """
    Create an rST node to document an environment variable

    :arg var: the environment variable metadata
    :arg state: the reStructuredText state machine state
    :arg default: an optional override for the default of the environment variable
    :returns: the node with a list item to document the environment variable
    """
    para = nodes.inline()

    result = f"* ``{var.name}``: "

    if var.help_text:
        result += var.help_text
        if not var.help_text.endswith("."):
            result += "."

    if var.auto_display_default:
        # Use explicitly provided default to override the default defined in code
        default_value = default if default is not undefined else var.default
        if default_value is not undefined:
            text = "(empty string)" if default_value == "" else str(default_value)
            result += f" Defaults to: ``{text}``."

    # Make sure the line is rendered as rST
    vl = ViewList()
    vl.append(var.help_text, "<param_help>")
    text, _ = state.inline_text(result, 0)
    para += text

    # TODO cleaner way to do this?
    para += nodes.raw("", "<br>", format="html")

    return para


def document_group(group: list[EnvironmentVariable], state: RSTState) -> nodes.Node:
    """
    Create an rST node to document a group of environment variables

    :arg group: the list of environment variables with metadata
    :arg state: the reStructuredText state machine state
    :returns: the node with list items to document the environment variables
    """
    para = nodes.paragraph()
    for var in group:
        if not var.add_to_docs:
            continue
        para += document_param(var, state)
    return para


class ConfigParamDirective(Directive):
    """
    Directive to generate documentation for a specific parameter (environment variable)
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        "default": directives.unchanged,
    }

    def run(self):
        param_name = self.arguments[0]
        default = self.options.get("default", undefined)

        var = get_envvar(param_name)
        para = document_param(var, self.state, default=default)

        return [para]


class ConfigGroupDirective(Directive):
    """
    Directive to generate documentation for a specific parameter group
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        "members": directives.unchanged,
        "exclude": directives.unchanged,
    }

    def run(self):
        group_name = self.arguments[0]
        members = self.options.get("members", "")
        exclude = self.options.get("exclude", "")

        if members and exclude:
            raise ValueError("cannot use both `members` and `exclude` options")

        group = get_envvar_group(group_name, members=members, exclude=exclude)

        return [document_group(group, self.state)]


class ConfigAllParamsDirective(Directive):
    """
    Directive to generate documentation for all parameter groups
    """

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        "members-groups": directives.unchanged,
        "exclude-groups": directives.unchanged,
        "exclude-params": directives.unchanged,
    }

    def run(self):
        members_groups = self.options.get("members-groups", "")
        exclude_groups = self.options.get("exclude-groups", "")
        exclude_params = self.options.get("exclude-params", "")

        if members_groups and exclude_groups:
            raise ValueError(
                "cannot use both `members-groups` and `exclude-groups` options"
            )

        grouped_vars = defaultdict(list)
        for var in ENVVAR_REGISTRY:
            # Check if the group should be included
            if members_groups and var.group not in members_groups:
                continue
            elif exclude_groups and var.group in exclude_groups:
                continue

            # Check if the param should be included
            if var.name in exclude_params or not var.add_to_docs:
                continue

            if not var.help_text:
                warnings.warn(
                    f"missing help_text for environment variable {var}", stacklevel=2
                )
            grouped_vars[var.group].append(var)

        root = nodes.container()

        def handle_group(group_name, variables, root):
            group = nodes.section()
            group["ids"].append(group_name)

            group += nodes.title(text=group_name)
            group += document_group(variables, self.state)
            root += group

        # Make sure the required vars are listed first
        if required_vars := grouped_vars.pop(ENVVAR_REQUIRED_GROUP, None):
            handle_group(ENVVAR_REQUIRED_GROUP, required_vars, root)

        optional_vars = grouped_vars.pop(ENVVAR_OPTIONAL_GROUP, None)
        for group_name, variables in grouped_vars.items():
            handle_group(group_name, variables, root)

        # Make sure the optional vars are listed first
        if optional_vars:
            handle_group(ENVVAR_OPTIONAL_GROUP, optional_vars, root)

        return [root]


def setup(app):
    app.add_directive("config-param", ConfigParamDirective)
    app.add_directive("config-group", ConfigGroupDirective)
    app.add_directive("config-all-params", ConfigAllParamsDirective)
