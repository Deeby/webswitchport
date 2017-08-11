from app import app
from flask import render_template
from flask import request, redirect, url_for
import parseconf
import ciscoios
from app.forms import DeviceSelectForm, LoginForm

user = {'login': '', 'password': ''}


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            user['login'] = form.login_fld.data
            user['password'] = form.pass_fld.data
            #  TODO check login and password
            return redirect(url_for('device'))
        else:
            return render_template('login.html', form=form, user=user)
    return render_template('login.html', user=user, form=form)


@app.route('/device', methods=['GET', 'POST'])
def device():
    if not user['login']:
        return redirect(url_for('login'))
    form = DeviceSelectForm(request.form)
    conf = parseconf.ParseConf()
    conf.set_pass(user['password'])
    conf.set_username(user['login'])
    data = conf.get_all_hosts()  # TODO need show only endpoint switch
    form.device.choices = [('', 'select device')] + [(c['hostname'], c['hostname']) for c in data]
    form.text.data = 'First: select the device'
    if request.method == 'POST':
        if form.is_submitted() and 'Сохранить' not in request.form.values():
            #  Get submit from device selector form
            sel_device = request.form.get('device')
            if sel_device:
                dev = conf.get_host_by_name(sel_device)
                try:
                    cisco = ciscoios.CiscoIOS(dev)
                    #  TODO filter by ports and vlans!
                    form.ports.choices = [(c['name'], c['name']) for c in cisco.get_interfaces()]
                    form.vlans.choices = [(c, c) for c in cisco.get_all_vlans()]
                    form.text.data = 'select vlan and port'
                except ciscoios.NetMikoAuthenticationException:
                    form.text.data = 'Authentication failure'
                except ciscoios.NetMikoTimeoutException:
                    form.text.data = 'Connection failure'
                except Exception as err:
                    form.text.data = err
        if 'Сохранить' in request.form.values():
            #  Submit from save button:
            sel_device = request.form.get('device')
            if sel_device:
                dev = conf.get_host_by_name(sel_device)
                try:
                    cisco = ciscoios.CiscoIOS(dev)
                    ret = cisco.switch_access_vlan(port=request.form.get('ports'), vlan=request.form.get('vlans'))
                    ret += '\n' + cisco.write_memory() + '\n'
                except ciscoios.NetMikoAuthenticationException:
                    ret = 'Authentication failure'
                except ciscoios.NetMikoTimeoutException:
                    ret = 'Connection failure'
                except Exception as err:
                    form.text.data = err
            else:
                ret = 'Second: select port and vlan'
            form.device.default = ''
            form.process()
            form.text.data = ret
            # TODO:
            # if 'devicesel' in request.form.values():
            #     print('need send ports ans vlans to client')
    return render_template('device.html', user=user, form=form)
