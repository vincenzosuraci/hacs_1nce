
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)


Monitor the 1nce sims.
Login credentials and sims' `iccid` are required.

# HACS version (suggested)
## Installation
- add `1NCE` as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories/)
- in HACS, search for `1NCE` and install the latest release
- in Home Assistant, add the `1NCE` integration, insert the `username`, `password` and the sim's `iccid` and follow the instructions  
- repeat the above steps to add more sims

# Stand-alone version

## Introduction
This custom component allows you to retrieve the following information related to <code>1nce</code> operator SIM cards:

- remaining MB (internet/data);
- total MB provided by the plan;
- SIM card expiration date.

It supports the case of 2 or more SIM cards (ICCID) associated with the same account (username and password).
It does not support the case of 2 or more accounts.

## Installation

- Copy the `1nce_account` folder into your [custom_components folder](https://developers.home-assistant.io/docs/en/creating_component_loading.html).
- Restart Home Assistant.
- After restarting Home Assistant, add the following lines to the <code>configuration.yaml</code> file (and save):

```yaml
1nce_account:
  sim_iccids: !secret 1nce_account_sim_iccids
  username: !secret 1nce_account_username
  password: !secret 1nce_account_password
```

- Go to the <code>secrets.yaml</code> file and add the following lines (and save):

```yaml
1nce_username: "inserire-qui-la-username"  
1nce_password: "inserire-qui-la-password"
1nce_sim_iccids: 
  - "inserire-qui-il-iccid-della-sim-#1"
  - "inserire-qui-il-iccid-della-sim-#2" 
```

- Restart Home Assistant.
- The following sets of entities should appear (one set for each phone number):

  - <code>1nce_account.<iccid>_volume</code> > Remaining MB
  - <code>1nce_account.<iccid>_expiry_date</code> > SIM expiration date
  - <code>1nce_account.<iccid>_total_volume</code> > Total MB of the plan

## Configuration

- By default, data is updated every 15 minutes.
- You can customize the data update interval by configuring the <code>scan_interval</code> parameter (in seconds):

```yaml
1nce_account:
  sim_iccids: !secret 1nce_account_sim_iccids
  username: !secret 1nce_account_username
  password: !secret 1nce_account_password
  scan_interval: 900
```

