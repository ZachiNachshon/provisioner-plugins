<h3 align="center" id="provisioner-logo"><img src="assets/provisioner-plugins.svg" height="300"></h3>

<p align="center">
  <a href="#requirements">Requirements</a> •
  <a href="#quickstart">QuickStart</a> •
  <a href="#available-plugins">Plugins</a> •
  <a href="#overview">Overview</a> •
  <a href="#contribute">Contribute</a> •
  <a href="#support">Support</a> •
  <a href="#license">License</a>
</p>
<br>

**Provisioner plugins** are the pluggable extensions for **Provisioner CLI**. 

Every plugin is installed as a pip package. During Provisioner CLI runtime, the commands of any pip installed plugin are dynamically loaded into Provisioner's CLI main menu.

Plugins are using the Provisioner CLI as the runtime and also as the development framework i.e. package dependency.

| :heavy_exclamation_mark: WARNING |
| :--------------------------------------- |
| Provisioner plugins are still in **alpha stage**, breaking changes might occur. |

<br>

<h2 id="requirements">🏴‍☠️ Requirements</h2>

- A Unix-like operating system: macOS, Linux
- Python `v3.10` and above
- [Provisioner CLI](https://github.com/ZachiNachshon/provisioner) installed and ready to use

<br>

<h2 id="quickstart">⚡️ QuickStart</h2>

Installing Provisioner plugins is as simple as installing a pip package:

```bash
pip install <plugin-name>
```

<br>

<h2 id="available-plugins">🔌 Available Plugins</h2>

| Name        | Path |
| :---        |:---  | 
| [Installers](./provisioner_installers_plugin/)  | Install anything anywhere on any OS/Arch either on a local or remote machine | 
| [Single Board](./provisioner_single_board_plugin)     | Single boards management as simple as it gets | 
| [Examples](./provisioner_examples_plugin)     | Playground for using the CLI framework with basic dummy commands | 

<br>

<h2 id="overview">⚓️ Overview</h2>

- [How to create a Provisioner plugin?](#how-create-plugin)
- [Plugin environment](#plugin-environment)
- [Documentation](#documentation)
- [Playground](#playground)

**Maintainers / Contributors:**

- [Contribute guides](https://add.contribute.guide.com)

<br>

<h3 id="how-create-plugin">🔨 How to create a <code>Provisioner</code> plugin?</h3>

1. Duplicate the `provisioner_examples_plugin` plugin folder with your plugin name

1. Search for `examples` keyword under your new plugin folder scope and replace where necessary

1. Update the plugin `<my-plugin>/Makefile` build command

1. Append the newly added plugin commands to the `provisioner_examples_plugin` repository outer `Makefile`

1. Define plugin configuration under `<my-plugin>/domain/config.py`

1. Manage plugin version under `<my-plugin>/pyproject.toml` under `[tool.poetry]`

1. Create a Python plugin entrypoint at `<my-plugin>/main.py`

| ❕ INFO |
| :--------------------------------------- |
| A `provisioner plugin genereate` command will get added soon to simplify a new plugin scaffolding. |

<br>

<h3 id="playground">🐳 Playground</h3>

Using `provisioner`, **every** command is a playground.

Use the `--dry-run` (short: `-d`) to check command execution breakdown, you can also add the `--verbose` (short: `-v`) flag to read `DEBUG` information. 

*All dry-run actions are no-op, you can safely run them as they only print to stdout.*

<br>

<h2 id="contribute">Contribute</h2>

Please follow our contribution guidelines if you with to contribute:

* PRs need to have a clear description of the problem they are solving
* PRs should be small
* Code without tests is not accepted, code coverage should keep the same level or higher
* Contributions must not add additional dependencies
* Before creating a PR, make sure your code is well formatted, abstractions are named properly and design is simple
* In case your contribution can't comply with any of the above please start a github issue for discussion

<br>

<h2 id="support">Support</h2>

Provisioner is an open source project that is currently self maintained in addition to my day job, you are welcome to show your appreciation by sending me cups of coffee using the the following link as it is a known fact that it is the fuel that drives software engineering ☕

<a href="https://www.buymeacoffee.com/ZachiNachshon" target="_blank"><img src="docs-site/site/static/docs/latest/assets/img/bmc-orig.svg" height="57" width="200" alt="Buy Me A Coffee"></a>

<br>

<h2 id="license">License</h2>

MIT

