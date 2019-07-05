#!/usr/bin/env python3

"""
Create a server to wait for the sms callback which is running in
its own thread.

Assumed callback:

External view of callback:
https://crspvr.duckdns.org:28080/sms?from={FROM}

Assumes nginx is handling the request initially and forwarding to this server
so this server sees:

http://localhost:8321/?from={FROM}

"""

import http.server
import urllib.parse
import logging
import sys
import threading

_LOGGER = logging.getLogger(__name__)

# Created via uuidgen -r
# And sent to us as part of the SMS callback from voip.ms
UUID = "138b7add02024707909b5050a62964ad"
QUERY_UUID = "uuid"

QUERY_SENDER = "from"

class VoipHandler(http.server.BaseHTTPRequestHandler):
  """Handle the voip.ms GET callback."""

  # For now, the only URL path we care about is / which
  # is coming from voip.ms to tell us we have sms messages
  # waiting for pickup...
  def __init__(self, *args):
    self.path_map = {
        "/": self.handle_sms_available,
    }
    super().__init__(*args)

  def do_GET(self):
    """Handle GET requests."""
    headers = dict(self.headers)
    _LOGGER.info("Got a GET: %s %s %s", self.client_address, self.path, headers)
    parsed = urllib.parse.urlparse(self.path)
    _LOGGER.info("parsed: %s", parsed)
    queries = urllib.parse.parse_qs(parsed.query)
    _LOGGER.info("queries: %s", queries)

    # No need to give the caller anything more than an indication of existance.
    # If it's the sms callback, they only accept ok...
    self.send_response(200)
    self.send_header("Content-Type", "text/plain")
    self.end_headers()
    self.wfile.write(bytes("ok", "utf8"))

    url_path = parsed.path
    if url_path not in self.path_map:
      _LOGGER.warning("path was really a 404")
      return

    # We tested for the path above, so this key should produce a value.
    func = self.path_map[url_path]
    result = func(queries)
    if not result:
      _LOGGER.warning("result was really a 400")
      return


  def handle_sms_available(self, query):
    """Handle the sms is available callback from voip.ms.

    Doing this as a function not associated with a class makes things a
    little easier. Someday, perhaps do a whole class thing, but not today.
    """
    _LOGGER.info("handle_sms_available: %s", query)

    # This all happens in the server thread. This is OK because
    # we don't expect more than one request at a time.
    # If we did care, we could used the threaded server in 3.7, but
    # this way we are compatible with older versions of python

    # See if the SMS is coming from the expected client
    uuids = query.get(QUERY_UUID, [])
    if not uuids:
      # Ignore it, but let voip.ms know we handled it...
      _LOGGER.warning("Ignoring callback - no uuid")
      return True

    # Is it the expected UUID?
    uuid = uuids[0]
    if uuid != UUID:
      # Ignore it, but let voip.ms know we handled it...
      _LOGGER.warning("Ignoring callback - bad uuid")
      return True

    # Right client, but is the actual SMS from someone we care about?
    senders = query.get(QUERY_SENDER, [])
    if not senders:
      # Ignore it, but let voip.ms know we handled it...
      _LOGGER.warning("Ignoring callback - no sender")
      return True

    sender = senders[0]
    if not self.server.sms_access.is_valid_sender(sender):
      # Ignore it, but let voip.ms know we handled it...
      _LOGGER.warning("Ignoring callback - wrong sender: <%s>", sender)
      return True

    _LOGGER.info("Checking for sms messages.")

    # Get messages from the voip.ms server and handle them.
    self.server.sms_access.poll_for_sms_messages()

    return True

class VoipServer():
  """Wrapper around HTTPServer to make it easier to put it in its own thread.

  Certificate handling is done by nginx, so no need to bother with it here.
  """
  def __init__(self, ip, port, sms_access):

    if not sms_access:
      _LOGGER.error("sms_access must not be empty.")
      raise ValueError("sms_access must not be empty.")

    self.server = http.server.HTTPServer((ip, port), VoipHandler)

    # sms_acccess is the callback used by the web server to validate
    # the sms message and handle as appropriate.

    # We use duck-typing and expect two methods:
    #     is_valid_sender(sender)
    #     poll_for_sms_messages()

    # pass the sms access info into the server so the handler can find it.
    self.server.sms_access = sms_access

  def run_server(self):
    """Run the server.

    This is blocking, so it's good if it's happening in its own thread.
    """
    self.server.serve_forever()
    self.server.server_close()

  def stop_server(self):
    """Stop the server.

    Needs to be run from a different thread than the one that
    started the server if using threading.
    """
    self.server.shutdown()


def server_setup(listen_ip, port, sms_access):
  """Start up the server in its own thread."""
  server = VoipServer(listen_ip, port, sms_access)

  thread = threading.Thread(None, server.run_server)
  thread.start()

  return (server, thread)


def server_shutdown(server, thread):
  """Shut down the server and wait for the server thread to complete."""
  server.stop_server()
  thread.join()


if __name__ == "__main__":
  sys.exit("Intended for import.")

# vim: set ts=2 sw=2 et sta sts smartindent:
