# #!/usr/bin/env python3

# import typer

# from python_examples_lib.examples.anchor.cli import example_anchor_cli_app
# from python_examples_lib.examples.ansible.cli import example_ansible_cli_app

# def get_all_examples():
#     pass

# def register_anchor_commands(app: typer.Typer, callback_remote_args):
    
#     app.add_typer(
#         example_ansible_cli_app, 
#         name="ansible", 
#         invoke_without_command=True, 
#         no_args_is_help=True, 
#         callback=callback_remote_args)

#     app.add_typer(
#         example_anchor_cli_app, 
#         name="anchor", 
#         invoke_without_command=True, 
#         no_args_is_help=True, 
#         callback=callback_remote_args)
