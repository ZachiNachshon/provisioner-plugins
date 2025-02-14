#!/usr/bin/env python3

from loguru import logger
from provisioner_installers_plugin.src.utilities.utilities_cli import SupportedToolingsCli

from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators


class UtilityListCmd:
    def run(self, ctx: Context) -> None:
        logger.debug("Inside UtilityListCmd run()")
        collaborators = CoreCollaborators(ctx)

        # Convert to list and sort by display_name
        sorted_utilities = sorted(
            SupportedToolingsCli.values(), key=lambda x: x.display_name.lower()  # Case-insensitive sorting
        )

        # Find the maximum length of utility names for proper padding
        max_name_length = max(len(utility.display_name) for utility in sorted_utilities)

        # Build the utilities string with consistent padding
        utilities = ""
        new_line = ""
        for utility in sorted_utilities:
            # Pad the display name to align all descriptions
            padded_name = utility.display_name.ljust(max_name_length)
            utilities += f"{new_line}{padded_name}    {utility.description}"
            new_line = "\n"

        help_info = ""
        help_info += 'Use "provisioner install cli <name>" to install any utility'
        help_info += '\nUse "provisioner install cli <name>@<ver>" to install specific version'
        help_info += "\n\nExamples:\n"
        help_info += "  provisioner install cli helm\n"
        help_info += "  provisioner install cli helm@3.7.0"
        collaborators.printer().print_with_rich_table_fn(utilities)
        collaborators.printer().print_fn(help_info)
