#!/usr/bin/env python3

class DummyConfig:

    class HelloWorldConfig:

        username: str = None

        def __init__(self, username: str = None) -> None:
            self.username = username

    def __init__(self, hello_world: HelloWorldConfig = None) -> None:
        self.hello_world = hello_world

    hello_world: HelloWorldConfig = HelloWorldConfig()
