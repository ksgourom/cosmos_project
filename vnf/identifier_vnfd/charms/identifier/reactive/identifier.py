from charms.reactive import when, when_not, set_flag, clear_flag
from charmhelpers.core.hookenv import (
    action_get,
    action_fail,
    action_set,
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
    status_set('active', 'Ready!')

@when('actions.start-identifier')
def start-identifier():
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
        action_set({'output': result})
    finally:
        clear_flag('actions.start-identifier')

@when('actions.start')
def start():
    # err = ''
    # ip = action_get('server-ip')
    # port = action_get('server-port')
    # try:
    #     cmd = "/usr/bin/python3 /home/ubuntu/app.py {} {}".format(ip, port)
    #     result, err = charms.sshproxy._run(cmd)
    # except:
    #     action_fail('command failed:' + err)
    # else:
    #     action_set({'output': result})
    # finally:
    #     clear_flag('actions.start')
    server_ip = action_get('server-ip')
    server_port = action_get('server-port')

    err = ''
    try:
        cmd = "sudo rm /etc/systemd/system/app.service >/dev/null 2>&1; "
        cmd += "sudo systemctl stop app.service >/dev/null 2>&1; "
        cmd += "sudo systemctl daemon-reload"
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed: ' + err)
        clear_flag('actions.start')
        return

    err = ''
    try:
        cmd = "echo '[Unit]' | sudo tee -a /etc/systemd/system/app.service > /dev/null && "
        cmd += "echo 'Description=app' | sudo tee -a /etc/systemd/system/app.service > /dev/null && "
        cmd += "echo '' | sudo tee -a /etc/systemd/system/app.service > /dev/null && "
        cmd += "echo '[Service]' | sudo tee -a /etc/systemd/system/app.service > /dev/null && "
        cmd += "echo 'Type=simple' | sudo tee -a /etc/systemd/system/app.service > /dev/null && "
        cmd += "echo 'User=ubuntu' | sudo tee -a /etc/systemd/system/app.service > /dev/null && "
        cmd += "echo 'WorkingDirectory=/home/ubuntu' | sudo tee -a /etc/systemd/system/app.service > /dev/null && "
        cmd += "echo 'ExecStart=/usr/bin/python3 app.py {0} {1}' | sudo tee -a /etc/systemd/system/app.service > /dev/null && ".format(server_ip, server_port)
        cmd += "echo 'Restart=always' | sudo tee -a /etc/systemd/system/app.service > /dev/null && "
        cmd += "echo 'RestartSec=5' | sudo tee -a /etc/systemd/system/app.service > /dev/null && "
        cmd += "echo '' | sudo tee -a /etc/systemd/system/app.service > /dev/null && "
        cmd += "echo '[Install]' | sudo tee -a /etc/systemd/system/app.service > /dev/null && "
        cmd += "echo 'WantedBy=multi-user.target' | sudo tee -a /etc/systemd/system/app.service > /dev/null && "
        cmd += "sudo systemctl daemon-reload && "
        cmd += "sudo systemctl start app.service"
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed: ' + err)
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.start')

@when('actions.stop')
def stop():
    err = ''
    try:
        cmd = "sudo systemctl stop app.service"
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed:' + err)
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.stop')
