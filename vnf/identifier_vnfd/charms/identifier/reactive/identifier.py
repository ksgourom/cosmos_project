from charms.reactive import (
    when, when_not,
    set_flag,
    set_state, remove_state
)

from charmhelpers.core.hookenv import (
    action_fail,
    action_get,
    action_set,
    config,
    status_set,
)

import charms.sshproxy


@when_not('identifier.installed')
def install_identifier():
    # Do your setup here.
    #
    # If your charm has other dependencies before it can install,
    # add those as @when() clauses above., or as additional @when()
    # decorated handlers below
    #
    # See the following for information about reactive charms:
    #
    #  * https://jujucharms.com/docs/devel/developer-getting-started
    #  * https://github.com/juju-solutions/layer-basic#overview
    #
    set_flag('identifier.installed')


cfg = config()


@when('config.changed')
def config_changed():
    err = ''
    try:
        cmd = "echo '' | sudo tee -a /etc/network/interfaces.d/50-cloud-init.cfg > /dev/null && "
        cmd += "echo 'auto ens4' | sudo tee -a /etc/network/interfaces.d/50-cloud-init.cfg > /dev/null && "
        cmd += "echo 'iface ens4 inet dhcp' | sudo tee -a /etc/network/interfaces.d/50-cloud-init.cfg > /dev/null && "
        cmd += "sudo timeout 5 ifup ens4"
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed: ' + err)
    else:
        set_state('identifier.configured')
        status_set('active', 'ready!')


@when('identifier.configured')
@when('actions.start_identifier')
def start_identifier():
    host = action_get('host')
    port = action_get('port')

    err = ''
    try:
        cmd = "sudo rm /etc/systemd/system/cosmos.service >/dev/null 2>&1; "
        cmd += "sudo systemctl stop cosmos.service >/dev/null 2>&1; "
        cmd += "sudo systemctl daemon-reload"
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed: ' + err)
        remove_state('actions.start_identifier')
        return

    err = ''
    try:
        cmd = "echo '[Unit]' | sudo tee -a /etc/systemd/system/cosmos.service > /dev/null && "
        cmd += "echo 'Description=Cosmos' | sudo tee -a /etc/systemd/system/cosmos.service > /dev/null && "
        cmd += "echo '' | sudo tee -a /etc/systemd/system/cosmos.service > /dev/null && "
        cmd += "echo '[Service]' | sudo tee -a /etc/systemd/system/cosmos.service > /dev/null && "
        cmd += "echo 'Type=simple' | sudo tee -a /etc/systemd/system/cosmos.service > /dev/null && "
        cmd += "echo 'User=cosmos' | sudo tee -a /etc/systemd/system/cosmos.service > /dev/null && "
        cmd += "echo 'WorkingDirectory=/home/cosmos' | sudo tee -a /etc/systemd/system/cosmos.service > /dev/null && "
        cmd += "echo 'ExecStart=/usr/bin/python app.py --host {0} --port {1}' | sudo tee -a /etc/systemd/system/cosmos.service > /dev/null && ".format(host, port)
        cmd += "echo 'Restart=always' | sudo tee -a /etc/systemd/system/cosmos.service > /dev/null && "
        cmd += "echo 'RestartSec=5' | sudo tee -a /etc/systemd/system/cosmos.service > /dev/null && "
        cmd += "echo '' | sudo tee -a /etc/systemd/system/cosmos.service > /dev/null && "
        cmd += "echo '[Install]' | sudo tee -a /etc/systemd/system/cosmos.service > /dev/null && "
        cmd += "echo 'WantedBy=multi-user.target' | sudo tee -a /etc/systemd/system/cosmos.service > /dev/null && "
        cmd += "sudo systemctl daemon-reload && "
        cmd += "sudo systemctl start cosmos.service"
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed: ' + err)
    else:
        action_set({'output': result, 'errors': err})
    finally:
        remove_state('actions.start_identifier')
