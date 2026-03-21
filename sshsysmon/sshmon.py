#!/usr/bin/env python
import sys
import yaml
import time
import logging
import argparse
from functools import reduce
from .templates import template
from .lib.monitor import *
from .lib.util import merge

def run_check(config):
	count = 0
	count_exc = 0

	def check_server(server_name):
		logging.info("Checking server: %s..." % server_name)
		try:
			server = config["servers"][server_name]
			server = Server(server_name, server)
			num_alerts = len(server.notifyChannelsOfAlerts())
			return num_alerts, 0
		except Exception as e:
			logging.error("Error checking server %s: %s" % (server_name, e))
			return 0, 1

	from concurrent.futures import ThreadPoolExecutor
	with ThreadPoolExecutor(max_workers=10) as executor:
		results = list(executor.map(check_server, config["servers"].keys()))
	
	for c, e in results:
		count += c
		count_exc += e

	sys.stderr.write("There were %d alert(s) triggered\n" % count)

	if count_exc > 0:
		sys.exit(1)

def run_summary(config, templateName=None):
	servers = []
	count_exc = 0

	def summarize_server(server_name):
		server_item = config["servers"][server_name]
		if server_item.get('summarize', True):
			logging.debug("Checking server: %s..." % server_name)
			try:
				server = Server(server_name, server_item)
				return server.getSummary(), 0
			except Exception as e:
				logging.warning("Unable to add server summary for %s: %s" % (server_name, e))
				return None, 1
		return None, 0

	from concurrent.futures import ThreadPoolExecutor
	with ThreadPoolExecutor(max_workers=10) as executor:
		results = list(executor.map(summarize_server, config["servers"].keys()))

	for s, e in results:
		if s:
			servers.append(s)
		count_exc += e

	data = {
		"ctime" : time.ctime(),
		"servers" : servers,
		"meta" : config.get('meta', {})
	}

	sys.stdout.write(template(templateName, data))

	if count_exc > 0:
		sys.exit(1)

	if any(map(lambda x: len(x.get('errors', [])) > 0, servers)):
		sys.exit(4)

def run_serve(config_path, host='0.0.0.0', port=5000, refresh=30):
	from .lib.monitor.server_http import start_server
	start_server(host=host, port=port, config_path=config_path, refresh_interval=refresh)

def parseArgs(args):
	p = argparse.ArgumentParser(description = "Run monitoring against servers defined in config")

	p.add_argument('command', help="Command to execute", choices=['check', 'summary', 'serve'])
	p.add_argument('configs', metavar='cfg', nargs='+', help="YML config file")

	p.add_argument('-v', '--verbose', action='store_true', help="Enable verbose logging")
	p.add_argument('-m', '--merge', help="Update-merge multiple configs from left to right", action='store_true')
	p.add_argument('-f', '--format', help="Specify template format to output summary (markdown)", default="md")
	p.add_argument('-p', '--port', type=int, default=5000, help="Port for serve command (default: 5000)")
	p.add_argument('-i', '--refresh', type=int, default=30, help="Refresh interval in seconds for serve command (default: 30)")
	p.add_argument('--host', default='0.0.0.0', help="Host to bind for serve command (default: 0.0.0.0)")

	return p.parse_args(args)

def main(args):
	opts = parseArgs(args)

	logging.basicConfig(level = logging.DEBUG if opts.verbose else logging.INFO)
	logging.getLogger('paramiko').setLevel(logging.WARNING)

	if opts.command == "serve":
		if not opts.configs:
			logging.error("serve command requires a config file")
			sys.exit(1)
		run_serve(opts.configs[0], host=opts.host, port=opts.port, refresh=opts.refresh)
		return

	try:
		config = reduce(
			lambda a,b: merge(a,b, overwrite=opts.merge),
			map(
				lambda filename: yaml.safe_load(open(filename, 'r')),
				opts.configs
				)
			)
	except Exception as e:
		logging.error("Error parsing config: " + str(e))
		sys.exit(1)

	if opts.command == "check":
		run_check(config)
	elif opts.command == "summary":
		run_summary(config, opts.format)
	else:
		logging.error("Invalid command %s", opts.command)
		sys.exit(1)

if __name__=="__main__":
	main(sys.argv[1:])


