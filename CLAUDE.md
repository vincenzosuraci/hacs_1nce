# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

Home Assistant custom integration (distributed via HACS) that reads data-quota information of
1NCE IoT SIM cards from the 1NCE Management API. One config entry = one SIM (ICCID) = one device
with three sensors: volume, total volume, expiry date.

- Repo: https://github.com/vincenzosuraci/hacs_1nce
- HA domain: `once` (a Python package name cannot start with a digit, hence not `1nce`).
- Minimum HA version: 2024.8.0 (keep `manifest.json` and `hacs.json` in sync).
- Code comments, log messages and commit messages are mostly in **Italian**; keep that style.

## Layout

```
custom_components/once/      # the HACS integration (the only thing HACS ships)
  __init__.py                # async_setup_entry / async_unload_entry; HA imports wrapped in try/except
                             # ModuleNotFoundError so once.py can be imported outside HA
  config_flow.py             # user step (iccid, username, password), reauth, options (credentials only)
  coordinator.py             # DataUpdateCoordinator, polls every UPDATE_INTERVAL_S (900 s)
  once.py                    # Once: pure aiohttp API client, NO Home Assistant imports
  once_device.py             # OnceDevice(Once): adds HA logging + device id/name ("1NCE <iccid>")
  sensor.py                  # OnceSensorEntityDescription list + OnceSensor (CoordinatorEntity)
  const.py                   # DOMAIN, PLATFORMS, CONF_* keys, sensor data keys, intervals
  translations/en.json, it.json  # config-flow texts and entity names
  manifest.json              # version, min HA version, iot_class cloud_polling
1nce_account/                # LEGACY YAML component (sync, requests + threads). Not shipped by HACS.
main.py                      # manual test script outside HA; reads ICCID/USER/PASS from .env
hacs.json                    # HACS metadata
.github/workflows/validate.yaml  # HACS validation action (push, PR, nightly)
```

## Data flow

1. `config_flow._async_try_connect` builds an `OnceDevice` with HA's shared aiohttp session and calls
   `test_connection()`. Unique id of the config entry = ICCID (set on setup for old entries too).
2. `async_setup_entry` creates `OnceCoordinator`, does the first refresh, forwards to `sensor`.
3. `Once.fetch_data()`:
   - `POST https://api.1nce.com/management-api/oauth/token`, Basic auth `username:password`,
     body `{"grant_type": "client_credentials"}` → `access_token` (cached on the instance);
   - `GET https://api.1nce.com/management-api/v1/sims/{iccid}/quota/data` with Bearer token;
   - on non-200 it drops the token and retries once (`MAX_NUM_RETRIES = 1`);
   - calls closer than `MIN_INTERVAL_S` (2 s) return the cached data.
   - A session passed to the constructor is reused and never closed; otherwise `Once` creates and
     closes its own (used by `main.py`).
4. Returned dict is keyed by the constants in `const.py`:
   `{"volume": float|None, "total volume": float|None, "expiry date": datetime.date|None}`.
   The API's `expiry_date` is ISO 8601 (`2034-12-02T00:00:00Z`); the old `%Y-%m-%d %H:%M:%S`
   format is still accepted (`Once._parse_expiry_date`).
5. Each `OnceSensorEntityDescription` has `key` (unique-id suffix), `data_key` (key in the dict above)
   and `translation_key` (name in `translations/*.json`). Entities use `has_entity_name = True`.
   Unique id: `1nce_<iccid>_<key>` — **do not change `key`**, it would orphan existing entities.

Errors: `OnceError(message, code)` → `UpdateFailed`; `OnceAuthError` → `ConfigEntryAuthFailed`
(starts the reauth flow). Codes: 100/101/102 token (timeout/connection/HTTP status or missing token),
103 token rejected (HTTP 400/401/403 → `OnceAuthError`), 200/201/202 quota (timeout/connection/HTTP status).

## Running / testing

There is no test suite and no linter config.

- Local API check without HA (Python ≥ 3.11, needs `aiohttp`, `python-dotenv`): copy `.env.example`
  to `.env`, fill `ICCID`, `USER`, `PASS`, run `python main.py`. `.env` is git-ignored — never commit it.
- `Once` can be tested against a local `aiohttp.web` mock by overriding `once.TOKEN_URL` / `once.QUOTA_URL`.
- In HA: copy `custom_components/once` into a dev instance's `config/custom_components/`, restart,
  enable `custom_components.once: debug` logging.
- CI only runs `hacs/action` (category `integration`).

## Releasing

Bump `version` in `custom_components/once/manifest.json`, then create a GitHub release/tag
(`hacs.json` has `hide_default_branch: true`, so HACS installs from releases only).
