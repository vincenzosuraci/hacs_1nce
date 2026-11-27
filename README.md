[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://hacs.xyz/docs/faq/custom_repositories/)
[![Validate](https://github.com/vincenzosuraci/hacs_1nce/actions/workflows/validate.yaml/badge.svg)](https://github.com/vincenzosuraci/hacs_1nce/actions/workflows/validate.yaml)

# 1NCE for Home Assistant

A Home Assistant integration that monitors [1NCE](https://1nce.com) IoT SIM cards through the official
1NCE Management API.

For each SIM (identified by its `ICCID`) it provides:

| Sensor         | Description                               | Unit |
|----------------|-------------------------------------------|------|
| Volume         | Remaining data volume                     | MB   |
| Total volume   | Total data volume included in the plan    | MB   |
| Expiry date    | Expiration date of the data quota / SIM   | date |

New entities get ids like `sensor.1nce_<iccid>_volume`; entities created by earlier versions keep their existing ids.

Data is polled from the cloud every **15 minutes**.

## Requirements

- Home Assistant **2024.8.0** or newer.
- The `username` and `password` of a 1NCE Portal user that can access the Management API.
- The `ICCID` of each SIM you want to monitor (you can find it in the 1NCE Portal or printed on the SIM card).

## Installation (HACS, recommended)

1. In HACS, add this repository as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories/):
   - URL: `https://github.com/vincenzosuraci/hacs_1nce`
   - Category: `Integration`
2. Search for **1NCE** in HACS and install the latest release.
3. Restart Home Assistant.

### Manual installation

Copy the `custom_components/once` folder into the `custom_components` folder of your Home Assistant
configuration directory, then restart Home Assistant.

## Configuration

The integration is configured from the UI (no YAML needed):

1. Go to **Settings → Devices & services → Add integration** and search for **1NCE**.
2. Enter the SIM `iccid`, your 1NCE `username` and `password`.
3. The integration tests the connection against the 1NCE API; if it succeeds, a device named
   `1NCE <iccid>` is created with the three sensors listed above.

To monitor more SIMs, add the integration again once per ICCID (each SIM is a separate config entry and device;
the same ICCID cannot be added twice).

- Username and password can be changed later from the integration's **Configure** button.
- If the credentials stop working, Home Assistant shows a **re-authentication** request where you can enter new ones.
- To monitor a different SIM, add a new integration entry instead of editing the existing one.

The UI is available in English and Italian.

## How it works

For every update the integration:

1. obtains an OAuth access token from `POST https://api.1nce.com/management-api/oauth/token`
   (`client_credentials` grant, HTTP Basic authentication with your username and password);
2. reads the SIM quota from `GET https://api.1nce.com/management-api/v1/sims/{iccid}/quota/data`.

The access token is cached and re-requested automatically when the API rejects it.
The expiry date is accepted both in ISO 8601 (`2034-12-02T00:00:00Z`) and in the older `2034-12-02 00:00:00` format.

## Troubleshooting

To get detailed logs, add the following to `configuration.yaml` and restart Home Assistant:

```yaml
logger:
  default: warning
  logs:
    custom_components.once: debug
```

Please report issues at <https://github.com/vincenzosuraci/hacs_1nce/issues>.

---

## Legacy stand-alone version (`1nce_account`)

> **Deprecated.** This is the original YAML-based component, kept for existing users. New installations
> should use the HACS integration above.

It supports several SIMs (ICCIDs) under the **same** account; it does not support multiple accounts.

### Installation

1. Copy the `1nce_account` folder into your
   [custom_components folder](https://developers.home-assistant.io/docs/creating_integration_file_structure/).
2. Add the following to `configuration.yaml`:

   ```yaml
   1nce_account:
     username: !secret 1nce_account_username
     password: !secret 1nce_account_password
     sim_iccids: !secret 1nce_account_sim_iccids
     scan_interval: 900  # optional, seconds (default: 900 = 15 minutes)
   ```

3. Add the following to `secrets.yaml`:

   ```yaml
   1nce_account_username: "your-username"
   1nce_account_password: "your-password"
   1nce_account_sim_iccids:
     - "iccid-of-sim-1"
     - "iccid-of-sim-2"
   ```

4. Restart Home Assistant.

For each ICCID the following entities are created:

- `1nce_account.<iccid>_volume` – remaining MB
- `1nce_account.<iccid>_total_volume` – total MB of the plan
- `1nce_account.<iccid>_expiry_date` – expiration date (`DD-MM-YYYY`)

## Disclaimer

This is an unofficial integration, not affiliated with or endorsed by 1NCE GmbH.
