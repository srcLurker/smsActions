#!/usr/bin/env python3

"""
Access the voip.ms API's to send and receive SMS messages.
"""

import logging
import pprint
import sys
import time

import requests

import qhue

_LOGGER = logging.getLogger(__name__)

# Light to turn on for paging
PAGE_LIGHT = [3]

# for the staticmethod
STATIC_ALLOWED_SENDERS = []

class AccessSms:
  """Access the voip.ms API's.

  Focused on accessing SMS related things.
  """
  def __init__(self, cfg):
    global STATIC_ALLOWED_SENDERS
    account = cfg["account"]
    self.did = account["phone"]

    api = cfg["api"]
    self.allowed_ips = api["allowed_ips"]
    self.url = api["url"]
    self.user = api["user"]
    self.password = api["password"]

    allowed = cfg["allowed_senders"]
    self.special_senders = allowed["special"]
    STATIC_ALLOWED_SENDERS = allowed["special"] + allowed["regular"]

    self.bridge = cfg["hue"]

    self.pretty = pprint.PrettyPrinter(indent=2, stream=sys.stderr)

    # Sometimes SMS can duplicate a message. This lets us avoid
    # acting on the duplicate.
    self._last_message = {}
    self._last_message["date"] = ""
    self._last_message["sender"] = ""
    self._last_message["recv"] = ""
    self._last_message["sms_msg"] = ""

  @staticmethod
  def is_valid_sender(sender):
    """True if the sender matches an allowed sender."""
    global STATIC_ALLOWED_SENDERS
    if len(sender) != 10:
      _LOGGER.warning("sender must be a 10-digit phone number: %s", sender)
      return False
    return sender in STATIC_ALLOWED_SENDERS

  def is_allowed_ip(self):
    """True if our IP is in the voip.ms valid list."""
    result = self.get_ip()
    if result["status"] != "success":
      _LOGGER.error("Can't talk to voip.ms: %s", result)
      return False

    my_ip = result["ip"]
    if my_ip not in self.allowed_ips:
      _LOGGER.error("IP (%s) not in allowed list: %s", my_ip, self.allowed_ips)
      return False

    return True

  def get_ip(self):
    """Gets our ip address as seen by the voip.ms people.

    It's important for the ip address returned here to match
    the addresses allowed to make voip.ms API calls.

    TODO: Provide a sanity check method to flag if the dynamic
    ip address from att/comcast has changed.
    """
    payload = {
        "api_username": self.user,
        "api_password": self.password,
        "method": "getIP"
    }
    req = requests.get(self.url, params=payload)
    result = req.json()
    return result

  def get_registration_status(self, account):
    """See if an account is registered and online."""
    payload = {
        "api_username": self.user,
        "api_password": self.password,
        "method": "getRegistrationStatus",
        "account": account
    }
    req = requests.get(self.url, params=payload)
    result = req.json()
    return result

  def get_sub_accounts(self, account):
    """Get the list of sub accounts for this account."""
    payload = {
        "api_username": self.user,
        "api_password": self.password,
        "method": "getSubAccounts",
        "account": account
    }
    req = requests.get(self.url, params=payload)
    result = req.json()
    return result

  def get_dids_info(self):
    """Get did (aka phone) info."""
    payload = {
        "api_username": self.user,
        "api_password": self.password,
        "method": "getDIDsInfo",
        "did": self.did
    }
    req = requests.get(self.url, params=payload)
    result = req.json()
    return result

  def send_sms(self, dst, message):
    """Send an sms message."""
    if len(dst) != 10:
      raise ValueError("dst must be a 10-digit number: %s" % dst)

    payload = {
        "api_username": self.user,
        "api_password": self.password,
        "method": "sendSMS",
        "did": self.did,
        "dst": dst,
        "message": message
    }
    req = requests.get(self.url, params=payload)
    result = req.json()
    if result["status"].lower() != "success":
      _LOGGER.error("Problem sending SMS: %s", result["status"])
    return result

  def _match_last(self, mdate, sender, recv, sms_msg):
    """Check if we've seen this message before."""

    # Have we seen this before?
    if (self._last_message["date"] == mdate and
        self._last_message["sender"] == sender and
        self._last_message["recv"] == recv and
        self._last_message["sms_msg"] == sms_msg):
      return True

    # Nope, so keep this one in case we see it again.
    self._last_message["date"] = mdate
    self._last_message["sender"] = sender
    self._last_message["recv"] = recv
    self._last_message["sms_msg"] = sms_msg
    return False

  def get_sms(self):
    """Get sms messages from a did (aka phone number).

    We get all the sms'es (both sent and received). The
    caller should look at the type to determine which is
    which and discard what is not wanted.

    Returns:
      {"sms": [{'contact': '6502482628',
                'date': '2018-10-02 01:34:42',
                'did': '4084626769',
                'id': '24392211',
                'message': 'testing sms',
                'type': '1'}, ...],
       "status": "success"}
    """
    now = int(time.time())
    now_utc = time.gmtime(now)
    now_str = time.strftime("%Y-%m-%d", now_utc)

    week = now - ((24 * 3600) * 7)
    week_utc = time.gmtime(week)
    week_str = time.strftime("%Y-%m-%d", week_utc)

    _LOGGER.info("week: %s, now: %s", week_str, now_str)

    payload = {
        "api_username": self.user,
        "api_password": self.password,
        "method": "getSMS",
        "did": self.did,
        "from": week_str,
        "to": now_str,
        "timezone": 0,
    }

    req = requests.get(self.url, params=payload)
    result = req.json()
    if result["status"].lower() != "success":
      _LOGGER.error("Problem accessing list of SMS: %s", result["status"])
    return result

  def delete_sms(self, sms_id):
    """Remove an sms from the server."""
    payload = {
        "api_username": self.user,
        "api_password": self.password,
        "method": "deleteSMS",
        "id": sms_id
    }
    req = requests.get(self.url, params=payload)
    result = req.json()
    if result["status"].lower() != "success":
      _LOGGER.error("Problem deleting SMS: %s", result["status"])
    return result

  def parse_sms_message(self, sender, msg):
    """Parse an sms message.

    All "authorized users" to take additional actions. If not authorize,
    assume it was a page. In the future, could set the light color
    based on the contents of the page.

    Args:
      sender: string with 10 digites of sender phone number
      msg: stirng of the text message

    Returns:
      text for reply or None for no reply.
    """
    _LOGGER.warning("Saw sms from: %s msg: %s", sender, msg)

    reply = None
    # Let special senders take actions
    if sender in self.special_senders:
      action = msg.lower()
      if action == "off":
        self.page_light(False)
        reply = "light off"
      elif action == "on":
        self.page_light(True)
        reply = "light on"
      elif action == "page":
        self.page()
      else:
        reply = "Actions: on, off, page"
    else:
      self.page()

    # Don't reply to the sms
    # More advanced, reply if it is a test from my number? To sanity
    # check things are working?
    return reply

  # Hue and light related methods
  def get_bridge_info(self):
    """Get bridge info."""
    bip = sorted(self.bridge.keys())[0]
    code = self.bridge[bip]["username"]
    _LOGGER.info("hue bringe info bridge ip: %s code: %s", bip, code)
    return (bip, code)

  @staticmethod
  def set_light_by_hsl(bridge, lid, hsl, trans):
    """Turn on a light and set it to a particular color."""
    _LOGGER.info("set_light_by_hsl id: %s hsl: %s", lid, hsl)
    bridge.lights[lid]("state", hue=hsl[0], sat=hsl[1], bri=hsl[2],
                       on=True, transitiontime=trans, http_method="put")

  @staticmethod
  def turn_light_off(bridge, lid, trans):
    """Turn off a light."""
    _LOGGER.info("turn_light_off id: %s", lid)
    bridge.lights[lid]("state", on=False, transitiontime=trans,
                       http_method="put")

  def page(self):
    """Action to take when a page occurs."""
    _LOGGER.info("It is time to page")
    self.page_light(True)

  def page_light(self, turn_on):
    """Turn a light used to indicate a page either on or off."""
    (bridge_ip, bridge_code) = self.get_bridge_info()
    bridge = qhue.Bridge(bridge_ip, bridge_code)
    for lid in PAGE_LIGHT:
      if turn_on:
        self.set_light_by_hsl(bridge, lid, (255, 1, 1), 10)
      else:
        self.turn_light_off(bridge, lid, 10)

  def poll_for_sms_messages(self):
    """Poll to get any sms messages - either sent or received.

    Process the messages received, delete everything
    we've looked at (sent or received). This keeps the
    voip.ms sms list clean.
    """
    global STATIC_ALLOWED_SENDERS
    result = self.get_sms()
    sms_nosort = result.get("sms", [])
    if not sms_nosort:
      _LOGGER.info("no sms in queue")
      return

    # sort the sms'es so that we process the oldest ones first.
    smses = sorted(sms_nosort, key=lambda v: v["id"])
    _LOGGER.info("voip sms: %s", self.pretty.pformat(smses))

    want_deleted = set()
    for sms in smses:
      _LOGGER.info("checking: %s", sms)
      sms_id = sms["id"]
      sender = sms["contact"].strip().lower()
      sms_msg = sms["message"].strip().lower()
      mdate = sms["date"].strip().lower()
      recv = int(sms["type"]) == 1

      _LOGGER.info("checking: %s %s %s %s %s", sms_id, sender,
                   sms_msg, mdate, recv)

      # We are processing this sms id, so put it on the set of
      # ids to be deleted.
      want_deleted.add(sms_id)

      if not recv:
        _LOGGER.warning("skipping sent sms: %s [%s]", sender, sms_msg)
        continue

      if sender not in STATIC_ALLOWED_SENDERS:
        _LOGGER.warning("skipping sender: %s [%s]", sender, sms_msg)
        continue

      if self._match_last(mdate, sender, recv, sms_msg):
        _LOGGER.warning("skipping duplicate sms: %s [%s]", sender, sms_msg)
        continue

      _LOGGER.info("saw an allowed sender: %s <id:%s> [%s]",
                   sender, sms_id, sms_msg)
      response_msg = self.parse_sms_message(sender, sms_msg)
      if response_msg:
        _LOGGER.info("id: %s sender: %s response: <%s>", sms_id,
                     sender, response_msg)
        self.send_sms(sender, response_msg)
      else:
        _LOGGER.warning("id: %s has no response message", sms_id)

    # Now that we've processed all the sms'es, delete them
    for sms in want_deleted:
      self.delete_sms(sms)

if __name__ == "__main__":
  sys.exit("Intended for import.")

# vim: set ts=2 sw=2 et sta sts smartindent:
