#!/usr/bin/env python3


from functools import wraps
from typing import Callable, Optional

import typer

from provisioner_shared.components.remote.remote_opts import TyperRemoteOpts

typer_remote_opts: TyperRemoteOpts = None


class CommonState:
    zachi: bool = False
    test: bool = False


common_state = CommonState()


def common_options_decorator(f: Callable) -> Callable:
    @wraps(f)
    def wrapper(
        zachi: bool = typer.Option(False, "--zachi", "-z", help="Example flag"),
        test: bool = typer.Option(False, "--test", help="Test flag"),
        *args,
        **kwargs,
    ):
        common_state.zachi = zachi
        common_state.test = test
        return f(*args, **kwargs)

    return wrapper


# class GlobalOptions:
#     def __init__(self):
#         self.zachi = False
#         self.test = False

# global_options = GlobalOptions()

# def common_options_decorator(f: Callable) -> Callable:
#     """Decorator that adds common options to the command."""
#     # Define the options directly using Click's Option
#     options = [
#         typer.Option(False, "--zachi", "-z", help="Example flag"),
#         typer.Option(False, "--test", help="Test flag"),
#     ]

#     # Apply each option to the function
#     for option in options:
#         f = option(f)

#     @wraps(f)
#     def wrapper(*args: Any, **kwargs: Any) -> Any:
#         global_options.zachi = kwargs.get('zachi', False)
#         global_options.test = kwargs.get('test', False)
#         return f(*args, **kwargs)

#     return wrapper

# Define a global state to store the common flags
# class CommonFlags:
#     zachi: bool = False
#     test: bool = False

# common_flags = CommonFlags()

# class CommonOptions:
#     def __init__(self):
#         self.zachi: bool = False
#         self.test: bool = False

#     def get_context_settings(self):
#         return {
#             "zachi": self.zachi,
#             "test": self.test
#         }

# common_options = CommonOptions()

# def get_common_options():
#     return typer.Context.get_current().obj

# def common_options_decorator(func: Callable) -> Callable:
#     @wraps(func)
#     def wrapper(ctx: typer.Context, *args: Any, **kwargs: Any) -> Any:
#         ctx.ensure_object(dict)
#         ctx.obj = {**common_options.get_context_settings(), **ctx.obj}
#         return func(*args, **kwargs)
#     return wrapper

# # Common options decorator
# def common_options_decorator(func: Callable) -> Callable:
#     @wraps(func)
#     def wrapper(
#         zachi: bool = typer.Option(False, "--zachi", "-z", help="Example flag"),
#         test: bool = typer.Option(False, "--test", help="Test flag"),
#         *args: Any,
#         **kwargs: Any,
#     ) -> Any:
#         # Update global flags
#         common_flags.zachi = zachi
#         common_flags.test = test

#         # Call the original function
#         return func(*args, **kwargs)

#     # Use Typer's `wrap` utility to preserve signature compatibility
#     # return typer.Typer().command()(wrapper)
#     # Call the original function
#     # return func(*args, **kwargs)

#      # Update the wrapper to mimic the original function signature
#     # return typer.Typer().command()(typer.main._add_typer_options(func, wrapper))
#     return wrapper


def register_raspberry_pi_commands(app: typer.Typer, remote_opts: TyperRemoteOpts):
    global typer_remote_opts
    typer_remote_opts = remote_opts

    @app.command(name="raspberry-pi")
    @common_options_decorator
    def raspberry_pi(
        param: Optional[str] = typer.Option(
            None,
            show_default=False,
            help="Static IP address to set as the remote host IP address",
            envvar="PROV_RPI_STATIC_IP",
        )
    ) -> None:
        print(f"zachi: {common_state.zachi}, test: {common_state.test}, param: {param}")
        # print(f"zachi: {global_options.zachi}, test: {global_options.test}, param: {param}")
        # print(f"zachi: {param}")

    # single_board_cli_app = typer.Typer()
    # app.add_typer(
    #     single_board_cli_app,
    #     name="raspberry-pi",
    #     invoke_without_command=True,
    #     no_args_is_help=True,
    #     # callback=typer_remote_opts.as_typer_callback(),
    # )

    # @single_board_cli_app.command(name="something")
    # # @common_options
    # @common_options_decorator
    # def something(param:str) -> None:
    #     print(f"zachi: {param}")

    # single_board_cli_app.add_typer(rpi_node_cli_app, name="node", invoke_without_command=True, no_args_is_help=True)
    # register_node_commands(typer_remote_opts)

    # single_board_cli_app.add_typer(rpi_os_cli_app, name="os", invoke_without_command=True, no_args_is_help=True)
