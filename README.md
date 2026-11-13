# ha-weheat-control

Home Assistant integration with **write** access for Weheat heat pumps, built on
[weheat-control](https://github.com/joriswijlens/weheat-control). Unofficial: it uses
undocumented portal endpoints and can break at any time. Runs next to the official
(read-only) Weheat integration.

## Entities

- Switch: hot water schedule on/off
- Number: hot water target temperature (40-60 °C)
- Service `weheat_control.boost_dhw` (`minutes`, default 60, max 720): heat the tank now

## Install

1. HACS → Custom repositories → add this repo as *Integration*.
2. Install **Weheat Control**, restart Home Assistant.
3. Settings → Devices & services → Add integration → *Weheat Control*, and sign in with your
   Weheat portal account. If the password changes, Home Assistant asks for the new one.

Requires Home Assistant 2026.2 or newer.

## Development

```
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python pytest-homeassistant-custom-component \
  "weheat-control @ git+https://github.com/joriswijlens/weheat-control@3499aed"
.venv/bin/python -m pytest
```

Not yet tested against a real Blackbird.
