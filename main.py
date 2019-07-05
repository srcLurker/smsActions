#!/usr/bin/env python3

"""
Main program to tie together:

1) Getting poked by voip.ms to request SMS polling
b) Getting sms messages from voip.ms
c) Acting on the sms messages as commands
d) Optionally sending confirmation responses back to the sender
e) Keeping it "slow" so the voip.ms people don't get angry at automation
"""

import ast
import logging
import optparse
import sys
import time

import access_sms
import server_sms

_LOGGER = logging.getLogger(__name__)

# A logging format that includes timestamps and the module
# from which the message was generated.
LOG_FORMAT = "%(levelname)0.1s|%(asctime)s|%(module)s|%(message)s"

def parse_config(fname):
  """Parse a python data file and return the resulting structure."""
  _LOGGER.info("config filename: %s", fname)
  with open(fname, "r") as fd:
    lines = fd.readlines()
  _LOGGER.info("config file: %s", lines)

  parsable = "".join(lines)
  _LOGGER.info("parsable: %s", parsable)

  val = ast.literal_eval(parsable)
  return val

def main():
  parser = optparse.OptionParser()
  parser.add_option(
      "-v", "--verbose", action="store_true",
      dest="verbose", default=False,
      help="Include more logging output for debugging.")
  parser.add_option(
      "-c", "--config", dest="config", metavar="FILE",
      help="path to configuration FILE with hue credentials")

  (options, args) = parser.parse_args()
  if args:
    parser.error("Bad arguments")

  if not options.config:
    parser.error("Must specific a config file via -c")

  if options.verbose:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
  else:
    logging.basicConfig(level=logging.WARNING, format=LOG_FORMAT)

  cfg = parse_config(options.config)

  # Setup the sms access portion
  do_sms = access_sms.AccessSms(cfg)

  _LOGGER.info("validating our ip address can access the voip.ms server")
  if not do_sms.is_allowed_ip():
    _LOGGER.error("Need to update voip.ms with this machone/site IP address.")
    sys.exit("problem with access_sms module.")

  # Now setup the server which will get the callback
  try:
    # The server gets its own thread.
    _LOGGER.info("starting sms listening server")
    voip_server, voip_thread = server_sms.server_setup("", 8321, do_sms)

    while True:
      time.sleep(101)
  except KeyboardInterrupt:
    _LOGGER.warning("Keyboard server stop")
  finally:
    # always stop the server if we run into an issue
    server_sms.server_shutdown(voip_server, voip_thread)

if __name__ == "__main__":
  main()

# vim: set ts=2 sw=2 et sta sts smartindent:
