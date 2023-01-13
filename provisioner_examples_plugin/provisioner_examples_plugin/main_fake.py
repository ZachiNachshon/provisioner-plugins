#!/usr/bin/env python3

from provisioner_features_lib.test_lib.fake_app import fake_app

try:
    from provisioner_examples_plugin.main import append_examples
    append_examples(fake_app)
except Exception as ex:
    print(f"Failed to load python example commands. ex: {ex}")

def get_fake_app():
    return fake_app

def main():
    fake_app()
