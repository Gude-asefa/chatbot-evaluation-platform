"""Anonymous, persistent device identifier stored in the browser.

A random UUID is created once per browser and kept in localStorage, so it
survives page reloads and new tabs on the same device. It contains no
personal data. Note: clearing browser data, private/incognito windows, or a
different browser on the same machine will produce a new ID.
"""

import streamlit as st

_STORAGE_KEY = "boa_chatbot_eval_device_id"
_COMPONENT_KEY = "device_id_component"

_DEVICE_ID_COMPONENT = st.components.v2.component(
    "boa_device_id",
    html="<div></div>",
    js="""
export default function (component) {
  const { data, setStateValue } = component
  const storageKey = data.storage_key

  let deviceId = null
  try {
    deviceId = window.localStorage.getItem(storageKey)
  } catch (e) {
    deviceId = null
  }

  if (!deviceId) {
    deviceId = (window.crypto && window.crypto.randomUUID)
      ? window.crypto.randomUUID()
      : Date.now().toString(36) + Math.random().toString(36).slice(2)
    try {
      window.localStorage.setItem(storageKey, deviceId)
    } catch (e) {
      // Storage blocked: the ID lasts only for this page session
    }
  }

  if (data.current !== deviceId) {
    setStateValue("device_id", deviceId)
  }
}
""",
)


def get_device_id():
    """Return this browser's device ID, or None until the browser reports it."""
    current = st.session_state.get(_COMPONENT_KEY, {}).get("device_id")

    result = _DEVICE_ID_COMPONENT(
        key=_COMPONENT_KEY,
        data={"storage_key": _STORAGE_KEY, "current": current},
        default={"device_id": None},
        on_device_id_change=lambda: None,
        height=0,
    )

    return result.device_id
