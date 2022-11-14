<h1 id="rpi-head">RaspberryPi</h1>

To start the interactive selection flow, run the following command: 

```bash
anchor rpi select
```

<br>

<h2 id="domain-items">Domain Items</h2>

- [Nodes](#nodes)

<br>

<h2 id="nodes">Nodes</h2>

This section relates to the blog post [Setting Up a Raspberry Pi Cluster](https://levelup.gitconnected.com/setting-up-a-raspberry-pi-cluster-b0fda1ee44ba).

Installation instructions for setting up an configuring a local Raspberry Pi cluster at your home desk.

To browse through RaspberryPi's nodes actions & workflows, [click here](https://github.com/ZachiNachshon/anchorfiles-blog/blob/master/rpi/nodes/instructions.yaml).

**Install**

To setup a new RaspberryPi node as explained on the blog post:

```bash
anchor rpi run nodes --workflow=set-up-new-node
```

<h3 id="rpi-nodes-actions">Available Actions</h3>

| **Identifier** | **Description**|
| :---           | :---|
| `configure-node` | Configuring hardware and system for an initial Raspberry Pi setup|
| `authorize-ssh-key-on-node` | Set SSH as authorized key on remote RPi node|
| `check-temperature` | Check RPi nodes temperature|
| `update-apt-package-cache` | Update apt package cache|
| `upgrade-apt-packages` | Upgrade apt packages|
| `reboot-all` | Reboot all nodes|
| `shutdown-all` | Shutdown all nodes|
| `hello-world` | Print hello-world on all nodes|

All *actions* can also be executed as a non-interactive one-liner command:

```bash
anchor rpi run nodes --action=<identifier>
```

<h3 id="rpi-nodes-workflows">Available Workflows</h3>

| **Identifier** | **Description**|
| :---           | :---|
| `set-up-new-node` | Set up a new node, from A to Z configuring system, hardware and applications |

All *workflows* can also be executed as a non-interactive one-liner command:

```bash
anchor rpi run nodes --workflow=<identifier>
```

<br>

