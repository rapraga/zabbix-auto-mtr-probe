# 📡 Zabbix Configuration

## Step 1 - Create the ICMP Monitoring Hosts

Create one host for each Internet destination you want to monitor.

Example:

| Host Name | Interface |
|------------|-----------|
| PING GLOBO.COM | globo.com |
| PING UOL.COM.BR | uol.com.br |
| PING CLOUDFLARE DNS | 1.1.1.1 |
| PING QUAD9 | 9.9.9.9 |
| PING OPEN DNS | 208.67.222.222 |
| PING X.COM | x.com |
| PING STEAM | steampowered.com |
| PING NIC.BR | nic.br |
| PING ALGAR | 187.16.218.182 |

Apply the template:

```text
Template Module ICMP Ping
```

to all hosts.

---

## Step 2 - Create a Correlation Host

Create a dedicated host that will be responsible for correlating the ICMP data.

Example:

```text
MONITORAMENTO INTERNET
```

This host will not perform any checks directly.

---

## Step 3 - Create the Calculated Item

Inside the host:

```text
MONITORAMENTO INTERNET
```

create a **Calculated Item**.

Example:

| Parameter | Value |
|------------|-------|
| Name | Hosts with High Packet Loss |
| Type | Calculated |
| Key | hosts.loss.count |
| Type of information | Numeric (unsigned) |

Expression example:

```zabbix
(last(/PING GLOBO.COM/icmppingloss)>=20)
+
(last(/PING UOL.COM.BR/icmppingloss)>=20)
+
(last(/PING CLOUDFLARE DNS/icmppingloss)>=20)
+
(last(/PING QUAD9/icmppingloss)>=20)
+
(last(/PING OPEN DNS/icmppingloss)>=20)
+
(last(/PING X.COM/icmppingloss)>=20)
+
(last(/PING STEAM/icmppingloss)>=20)
+
(last(/PING NIC.BR/icmppingloss)>=20)
+
(last(/PING ALGAR/icmppingloss)>=20)
```

The item value will represent the total number of monitored hosts currently presenting packet loss greater than or equal to 20%.

---

## Step 4 - Create the Trigger

Create a trigger in the host:

```text
MONITORAMENTO INTERNET
```

Example:

```zabbix
last(/MONITORAMENTO INTERNET/hosts.loss.count)>=4
```

This trigger indicates that at least four monitored Internet destinations are experiencing packet loss simultaneously.

When this trigger enters **PROBLEM** state, the MTR collection process will be started automatically.

---

## Step 5 - Create the MTR Host

Create another host dedicated to storing MTR results.

Example:

```text
MTR-AUTOMATICO
```

Create the following items:

### MTR Report

| Parameter | Value |
|------------|-------|
| Type | Zabbix trapper |
| Key | mtr.report |
| Type of information | Text |

---

### MTR Trigger

| Parameter | Value |
|------------|-------|
| Type | Zabbix trapper |
| Key | mtr.trigger |
| Type of information | Numeric (unsigned) |

---

## Step 6 - Configure Zabbix Script

Navigate to:

```text
Alerts → Scripts
```

Create:

| Parameter | Value |
|------------|-------|
| Name | Trigger Probe |
| Scope | Action operation |
| Type | Script |
| Execute on | Zabbix server |
| Commands | /usr/lib/zabbix/externalscripts/triggerProbe.sh |

---

## Step 7 - Configure the Action

Navigate to:

```text
Alerts → Actions → Trigger actions
```

Create a new Action.

Condition:

```text
Trigger = Internet Instability Detected
```

Operation:

```text
Trigger Probe
```

The script will now execute automatically every time the trigger enters the PROBLEM state.

---

# 🧠 Internal Script Logic

The Python script executes MTR tests against all configured destinations simultaneously.

After collecting the results, the script analyses the packet loss of the **final hop** for each destination.

If:

```text
7 or more destinations present packet loss >= 20%
```

the script sends:

```text
mtr.trigger = 1
```

to Zabbix.

Otherwise:

```text
mtr.trigger = 0
```

---

# 🚨 Carrier Escalation Trigger

Create a trigger in host:

```text
MTR-AUTOMATICO
```

Expression:

```zabbix
last(/MTR-AUTOMATICO/mtr.trigger)=1
```

This trigger indicates a generalized Internet degradation and can be used to:

- Notify NOC teams.
- Escalate to upstream providers.
- Open carrier tickets automatically.
- Send alerts to Telegram, Slack or e-mail.

---

# 📊 MTR Report

All collected MTR information is automatically sent to:

```text
mtr.report
```

allowing the NOC team to analyze:

- Packet loss per hop.
- Average latency.
- Affected upstreams.
- Historical incident evidence.
