#path: /usr/local/lib/python2.7/dist-packages/ansible/modules/network/eos/eos_interface_remediate.py

#!/usr/bin/python


import re
import time

from ansible.module_utils.eos import run_commands

class int_remediate(object):

	def __init__(self,module):
		self.module = module


	def action(self):
		command = ["show ip int brief"]
		command_response = run_commands(self.module,command)
		command_responses = command_response[0].split('\n')
		regex = "(\w+)\s+([0-9/.]+)\s+(admin down)\s+(\w+)\s+(\w+)"
				
		for response in command_responses:
			m = re.match(regex,response)
			if m:
				interface = m.group(1)
				commands = ['config','int {}'.format(interface),'no shut','wr','end']
				run_commands(self.module,commands)

		time.sleep(5)
		responses = run_commands(self.module,command)
		return responses