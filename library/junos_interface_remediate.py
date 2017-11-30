#!/usr/bin/python
#path: /usr/lib/python2.7/dist-packages/ansible/modules/network/junos
import re
import time

from ansible.modules.network.junos.junos_isis_test import configure_device
from ansible.module_utils.junos import commit_configuration

class int_remediate():

	def __init__(self,module,warnings,responses):
		self.module = module
		self.responses = responses
		self.warnings = warnings
	def action(self):
		regex = "([a-z0-9./-]+)\s+([0-9]+)\s+([\w]+)\s+(\w+)\s+(Down)\s+(.+)"
		res=self.responses.split('\n')
		for response in res:
			m = re.match(regex,response)
			if m:
				interface = m.group(1)
				lines = ['delete interfaces {} disable'.format(interface)]
				configure_device(self.module, self.warnings, lines)
            	commit_configuration(self.module)