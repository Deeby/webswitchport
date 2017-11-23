#!/usr/bin/env python
import yaml
import random


class ParseConf:

    def __init__(self, config=None):
        if not config:
            config = './cisco.yaml'
        self.nodes = yaml.load(open(config))
        node = self.nodes['defaults']
        self.username = node['username']
        self.password = node['password']
        self.port = node['port']
        self.device_type = node['device_type']
        self.secret = node['secret']  # enable password

    def set_pass(self, password):
        self.password = password
        return

    def set_username(self, username):
        self.username = username
        return

    def set_enable(self, secret):
        self.secret = secret
        return

    def get_host_by_name(self, hostname):
        netmikobj = {}
        node = self.nodes['devices'][hostname]
        netmikobj['username'] = self.username
        netmikobj['port'] = self.port
        netmikobj['password'] = self.password
        netmikobj['device_type'] = self.device_type
        netmikobj['secret'] = self.secret
        for prop in netmikobj.keys():
            if prop in node:
                netmikobj[prop] = node[prop]
        netmikobj['ip'] = node['ip']
        netmikobj['hostname'] = hostname
        return netmikobj

    def get_all_hosts(self):
        for hostname in self.nodes['devices']:
            yield self.get_host_by_name(hostname)

    def get_all_acc_hosts(self):
        for hostname in self.nodes['devices']:
            if 'acc' in hostname:
                yield self.get_host_by_name(hostname)

    def get_random_acc_host(self):
        return random.choice(list(self.get_all_acc_hosts()))
