
# path: /usr/local/lib/python2.7/dist-packages/ansible/modules/network/eos/eos_isis_test.py

#!/usr/bin/python



import time
import json
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.six import string_types
from ansible.module_utils.netcli import Conditional
from ansible.module_utils.network_common import ComplexList
from ansible.module_utils.eos import run_commands
from ansible.module_utils.eos import eos_argument_spec, check_args
from ansible.modules.network.eos.eos_interface_remediate import *

# function to give output in a standard line format
def to_lines(stdout):
    lines = list()
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        lines.append(item)
    return lines


def main():

	argument_spec = dict(
        command=dict(type='list', required=True),
        isis_interface=dict(type='int', required=True)
        )


	argument_spec.update(eos_argument_spec)

	module = AnsibleModule(argument_spec=argument_spec,supports_check_mode=True
                           )

	result = dict()
	warnings = list()
	check_args(module, warnings)


	command = module.params['command']
	isis_interface = module.params['isis_interface']

# appending warning messages in result warnings as keyword
	if warnings:
		result['warnings'] = warnings
	

# checking if command is not 'show isis summary' then failing tasks
	if(command[0] == 'show isis summary'):
		command_response = run_commands(module,command)
	else:
		module.fail_json(msg = 'please provide coorect command (hint: show isis summary)')
	

# searching number of active isis interfaces
	regex = "(Number active interfaces:)\s(\d+)"
	m = re.search(regex,command_response[0])
	active_int = int(m.group(2))

# if number of configured isis interface and active isis interface is not equal then run remediation script
	if(active_int!=isis_interface):
		obj = isis_remediate(module)
		responses = obj.action()
		result.update({
			'remediation': 'Done'
			})
	else:
		result.update({
			'remediation': 'Not Needed'
			})


	result.update({
		'changed': False,
		'command': command,
		'isis_interface': isis_interface,
		'active_interface': active_int,
		'stdout_lines': to_lines(command_response)
		})

	module.exit_json(**result)

main()

