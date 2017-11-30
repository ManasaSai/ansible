#!usr/bin/python
# -*- coding: utf-8 -*-
#path: /usr/lib/python2.7/dist-packages/ansible/modules/network/junos


from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}



import time
import re
import shlex

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import junos_argument_spec, check_args, get_configuration
from ansible.module_utils.netcli import Conditional, FailedConditionalError
from ansible.module_utils.netconf import send_request
from ansible.module_utils.junos import load_config
from ansible.module_utils.six import string_types, iteritems
from ansible.modules.network.junos.junos_interface_remediate import *
from ansible.modules.network.junos.junos_config import guess_format
from ansible.module_utils._text import to_native
from ansible.module_utils.junos import get_diff, load_config
from ansible.module_utils.junos import commit_configuration, discard_changes, locked_config
from ansible.module_utils.junos import junos_argument_spec, load_configuration
from ansible.module_utils.junos import check_args as junos_check_args
try:
	from lxml.etree import Element, SubElement, tostring
except ImportError:
	from xml.etree.ElementTree import Element, SubElement, tostring

try:
	import jxmlease
	HAS_JXMLEASE = True
except ImportError:
	HAS_JXMLEASE = False

USE_PERSISTENT_CONNECTION = True


def to_lines(stdout):
	lines = list()
	for item in stdout:
		if isinstance(item, string_types):
			item = str(item).split('\n')
		lines.append(item)
	return lines

def rpc(module, items):

    responses = list()

    for item in items:
        name = item['name']
        xattrs = item['xattrs']
        fetch_config = False
        text = item.get('text')
        name = str(name)
        if name == 'command' and text.startswith('show configuration') or name == 'get-configuration':
            fetch_config = True

        element = Element(name, xattrs)

        if text:
            element.text = text
        if fetch_config:
            reply = get_configuration(module, format=xattrs['format'])
        else:
            reply = send_request(module, element, ignore_warning=False)
        responses.append(tostring(reply))

    return responses
def filter_delete_statements(module, candidate):
    reply = get_configuration(module, format='set')
    match = reply.find('.//configuration-set')
    if match is None:
        # Could not find configuration-set in reply, perhaps device does not support it?
        return candidate
    config = to_native(match.text, encoding='latin-1')

    modified_candidate = candidate[:]
    for index, line in reversed(list(enumerate(candidate))):
        if line.startswith('delete'):
            newline = re.sub('^delete', 'set', line)
            if newline not in config:
                del modified_candidate[index]

    return modified_candidate

def split(value):
    lex = shlex.shlex(value)
    lex.quotes = '"'
    lex.whitespace_split = True
    lex.commenters = ''
    return list(lex)
"""def configure_device(module, warnings, candidate):

    kwargs = {}
    candidate = filter_delete_statements(module, candidate)
    kwargs['format'] = 'text'
    kwargs['action'] = 'set'

    return load_config(module, candidate, warnings, **kwargs)
"""
def configure_device(module, warnings, candidate):

    kwargs = {}
    config_format = None

    if module.params['src']:
        config_format = module.params['src_format'] or guess_format(str(candidate))
        if config_format == 'set':
            kwargs.update({'format': 'text', 'action': 'set'})
        else:
            kwargs.update({'format': config_format, 'action': module.params['update']})

    if isinstance(candidate, string_types):
        candidate = candidate.split('\n')

    # this is done to filter out `delete ...` statements which map to
    # nothing in the config as that will cause an exception to be raised
    if any((module.params['lines'], config_format == 'set')):
        #candidate = filter_delete_statements(module, candidate)
        kwargs['format'] = 'text'
        kwargs['action'] = 'set'

    return load_config(module, candidate, warnings, **kwargs)


def parse_commands(module, warnings):
    items = list()

    for command in (module.params['commands'] or list()):
        parts = command.split('|')
        text = parts[0]

        display = module.params['display'] or 'text'

        if '| display json' in command:
            display = 'json'

        elif '| display xml' in command:
            display = 'xml'

        if display == 'set' or '| display set' in command:
            if command.startswith('show configuration'):
                display = 'set'
            else:
                module.fail_json(msg="Invalid display option '%s' given for command '%s'" % ('set', command))

        xattrs = {'format': display}
        items.append({'name': 'command', 'xattrs': xattrs, 'text': text})

    return items

def main():

    argument_spec = dict(
        commands=dict(type='list', required=True),
        display=dict(choices=['text', 'json', 'xml', 'set'], aliases=['format', 'output']),
        src=dict(type='path'),
        src_format=dict(choices=['xml', 'text', 'set', 'json']),
        lines=dict(type='list'),
        # update operations
        update=dict(default='merge', choices=['merge', 'override', 'replace', 'update']),

    )

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    result={'changed': False}
  
    items = list()
    items.extend(parse_commands(module, warnings))
    responses = rpc(module, items)
    regex = "Down"
    m = re.search(regex,responses[0])
    if m:
        obj = int_remediate(module,warnings,responses[0])
        obj.action()
        result.update({
            'remediation': 'Done'
            })
    else:
        result.update({
            'remediation': 'Not Needed'
            })
    time.sleep(10)
    responses = rpc(module, items)
    result.update({
        'changed': False,
        'warnings': warnings,
        'stdout_lines': to_lines(responses)
    })
    module.exit_json(**result)
	
if __name__ == '__main__': 
    main()
