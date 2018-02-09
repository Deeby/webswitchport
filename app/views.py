from flask import render_template, session, request, redirect, url_for

import ciscoios
import parseconf
from app import app
from app.forms import DeviceSelectForm, LoginForm, FindForm
from findport import search_port_by_mac, mac_normalize


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    session['auth'] = False
    if request.method == 'POST':
        if form.is_submitted() and form.validate():
            session['login'] = form.login_fld.data
            session['password'] = form.pass_fld.data
            conf = parseconf.ParseConf()
            conf.set_username(session.get('login'))
            conf.set_pass(session.get('password'))
            try:  # Check login and password...
                cisco = ciscoios.CiscoIOS(conf.get_random_acc_host())
                session['auth'] = True
            except ciscoios.NetMikoAuthenticationException:
                session['auth'] = False
                return render_template('login.html', form=form, user=session)
            priv = cisco.show_priv()
            session['priv'] = priv
            return redirect(url_for('findport'))
        else:
            return render_template('login.html', form=form, user=session)
    return render_template('login.html', user=session, form=form)


@app.route('/device', methods=['GET', 'POST'])
def device():
    if not session.get('auth'):
        return redirect(url_for('login'))
    form = DeviceSelectForm(request.form)
    conf = parseconf.ParseConf()
    conf.set_username(session.get('login'))
    conf.set_pass(session.get('password'))
    data = conf.get_all_acc_hosts()
    data = sorted(data, key=lambda host: host['hostname'])
    form.device.choices = [('', 'select device')] + [(c['hostname'], c['hostname']) for c in data]
    form.text.data = 'Select the device...'
    if request.method == 'POST':
        if form.is_submitted() and 'Save' not in request.form.values():
            #  Get submit from device selector form
            sel_device = request.form.get('device')
            if sel_device:
                dev = conf.get_host_by_name(sel_device)
                try:
                    cisco = ciscoios.CiscoIOS(dev)
                    form.ports.choices = [('', 'select port')] + [
                        (c['name'], c['name'] + ' - ' + c['vlan'] + ' - ' + c['status']) for c in
                        cisco.get_all_acc_int()]
                    form.vlans.choices = [('', 'select vlan')] + [(c['vlan'], c['vlan'] + ' - ' + c['name']) for c in
                                                                  cisco.get_all_vlans()]
                    form.text.data = 'Select vlan and port...'
                except ciscoios.NetMikoAuthenticationException:
                    form.text.data = 'ERROR: Authentication failure!'
                except ciscoios.NetMikoTimeoutException:
                    form.text.data = 'ERROR: Connection failure!'
                except Exception as err:
                    form.text.data = err
        if 'Save' in request.form.values():
            ret = None
            #  Submit from save button:
            sel_device = request.form.get('device')
            if session.get('priv') >= 5:
                if sel_device:
                    dev = conf.get_host_by_name(sel_device)
                    port = request.form.get('ports')
                    vlan = request.form.get('vlans')
                    if port and vlan:
                        try:
                            cisco = ciscoios.CiscoIOS(dev)
                            ret = cisco.switch_access_vlan(port=port, vlan=vlan)
                            ret += '\n' + cisco.write_memory() + '\n'
                        except ciscoios.NetMikoAuthenticationException:
                            ret = 'ERROR: Authentication failure!'
                        except ciscoios.NetMikoTimeoutException:
                            ret = 'ERROR: Connection failure!'
                        except Exception as err:
                            form.text.data = err
                    else:
                        ret = 'ERROR: port or vlan not selected!'
                else:
                    ret = 'ERROR: device not selected!'
            else:
                ret = 'ERROR: low priv level'
            form.device.default = ''
            form.process()
            form.text.data = ret
    return render_template('device.html', user=session, form=form)


@app.route('/findport', methods=['GET', 'POST'])
def findport():
    if not session.get('auth'):
        return redirect(url_for('login'))
    form = FindForm()
    form.text.data = 'Enter mac address...'
    if request.method == 'POST':
        if form.is_submitted() and 'Find' in request.form.values() and form.validate():
            conf = parseconf.ParseConf()
            conf.set_username(session.get('login'))
            conf.set_pass(session.get('password'))
            root = conf.get_host_by_name("core-sw-root")
            # TODO - брать настройки из конфига
            ret = search_port_by_mac(conf, root, mac_normalize(form.mac.data), "domain.ru")
            if type(ret) is tuple:
                form.text.data = ret[0] + '\t' + ret[1]
            else:
                form.text.data = ret
            # TODO - сделать кнопку редиректа на заполненную форму device
            # return redirect(url_for('device'))
        else:
            return render_template('findport.html', form=form, user=session)
    return render_template('findport.html', user=session, form=form)
