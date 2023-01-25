#!/usr/bin/env python3

from provisioner_features_lib.test_lib.fake_app import fake_app

def get_fake_app():
    try:
        from provisioner_single_board_plugin.main import append_single_boards
        append_single_boards(fake_app)
    except Exception as ex:
        print(f"Fake provisioner single board CLI commands failed to load. ex: {ex.with_traceback()}")

    return fake_app

def main():
    fake_app()
