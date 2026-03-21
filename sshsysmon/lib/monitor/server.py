from .channelgroup import *
from .alert import *
from ..util import sanitize
from ..plugins import loadPlugin
import logging
import traceback

class Server:
	def __init__(self, name, config):
		self._name = name
		self._driver = loadPlugin("drivers", config.get("driver"), config.get("config", {}))
		self._monitors = config.get('monitors', []) + config.get('monitors+', [])
		self._channels = config.get('channels', []) + config.get('channels+', [])
		self._meta = config.get('meta', {})


	def createAlerts(self):
		alerts = []

		def process_monitor(monitor):
			monitor_type = monitor.get('type')
			monitor_alarms = monitor.get('alarms', {})
			monitor_config = monitor.get('config', {})
			monitor_alerts = []

			logging.debug("Creating inspector: %s..." % monitor_type)

			try:
				inspector = loadPlugin("inspectors", monitor_type, self._driver, monitor_config)
				if not inspector:
					raise Exception("Unknown inspector type: %s" % monitor_type)

				metrics = inspector.getMetricsCached()
				if not metrics:
					raise Exception("Inspector returned no data: %s" % inspector.getName())

				for alarm_name, statement in monitor_alarms.items():
					monitor_alerts.append(Alert(self._name, monitor_type, alarm_name, statement, metrics))

			except Exception as e:
				logging.warning("Error executing inspector %s: %s" % (monitor_type, e))
				logging.debug(traceback.format_exc())
				monitor_alerts.append(Alert(self._name, monitor_type, "NO_DATA", "True", {}))
			return monitor_alerts

		import concurrent.futures
		with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
			results = list(executor.map(process_monitor, self._monitors))
		
		for res in results:
			alerts.extend(res)

		return alerts

	def getFailedAlerts(self):
		failedAlerts = []
		for alert in self.createAlerts():
			logging.debug("Evaluating alert " + alert.name)
			if alert.eval():
				logging.info("ALERT: %s", alert.name)
				failedAlerts.append(alert)
		return failedAlerts

	#Notify all channels of any alerts that have been fired
	def notifyChannelsOfAlerts(self):
		channels = ChannelGroup(self._channels)

		alerts = self.getFailedAlerts()
		for alert in alerts:
			logging.debug("Notifying channel of alert: %s" % alert)
			channels.notify(alert)

		return alerts

	# Prints out summary to stdout
	def getSummary(self):
		errors = []
		results = []

		def process_monitor(monitor):
			if monitor.get('summarize', True): #Ability to hide at monitor level
				monitor_type = monitor.get('type')
				monitor_config = monitor.get('config', {})
				monitor_alarms = monitor.get('alarms', {})

				logging.debug('Creating summary for %s...' % monitor_type)
				try:
					logging.debug("Creating inspector...")
					inspector = loadPlugin("inspectors", monitor_type, self._driver, monitor_config)
					
					logging.debug("Retrieving metrics...")
					metrics = inspector.getMetricsCached()

					logging.debug("Processing alarms...")
					alarms = []
					for alarm_name, statement in monitor_alarms.items():
						alert = Alert(self._name, monitor_type, alarm_name, statement, metrics)
						alarms.append({
							"name" : alarm_name,
							"fired" : alert.eval(),
							"statement" : statement
							})

					logging.debug("Generating summary metrics...")
					return {
						"type" : monitor_type,
						"config" : monitor_config,
						"text" : inspector.getSummary(),
						"name" : inspector.getName(),
						"metrics" : metrics,
						"alarms" : alarms
					}, None

				except Exception as e:
					logging.warning("Error executing inspector %s: %s" % (monitor_type, e))
					logging.debug(traceback.format_exc())
					return None, e
			return None, None

		import concurrent.futures
		with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
			monitor_results = list(executor.map(process_monitor, self._monitors))

		for res, err in monitor_results:
			if res:
				results.append(res)
			if err:
				errors.append(err)

		return {
			"name" : self._name,
			"inspectors" : results,
			"meta" : self._meta,
			"errors" : errors,
		}


