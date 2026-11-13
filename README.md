# ha-weheat-control

Home Assistant integration with **write** access for Weheat heat pumps, built on
[weheat-control](https://github.com/joriswijlens/weheat-control). Unofficial: it uses
undocumented portal endpoints and can break at any time. Runs next to the official
(read-only) Weheat integration.

Entities: hot water schedule switch, hot water target temperature, and the
`weheat_control.boost_dhw` service.

Status: draft, untested. Install via HACS as a custom repository.
