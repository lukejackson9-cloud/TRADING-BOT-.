# Discord alerts → Trading 212 demo: setup guide

What this does: when the **Saucy Stocks** channel posts an alert, your Android
phone gets a Discord notification. A phone app forwards that notification's
text to a small program on a rented server, which buys or sells the shares on
your **Trading 212 demo account** (fake money). Every trade sends a push to
your phone.

Rules it always follows (built into the code, can't be loosened):
- Demo account only. It refuses to run against a live account.
- 5% of the account per trade, 50% invested at most, buys only.
- Each position exits at -4% or +8%, or when the author posts "Closed".
  "Trimmed" sells half.
- If the account drops 5% in a day it **pauses itself** and stays paused
  until you run `bridge resume`.
- Options alerts are ignored (Trading 212 can't trade options).

It starts in **test mode**: it reads and logs every alert but places no
orders. You switch it on yourself in step 5.

---

## 1. Rent a server (about £4–5/month)

Any provider works. Two easy ones:
- **Hetzner Cloud**: pick the smallest shared plan (e.g. CX22) with
  **Ubuntu 24.04**.
- **DigitalOcean**: pick the $6 "Basic" droplet with **Ubuntu 24.04**.

Choose password login (or SSH key if you know how). Note the server's **IP
address**.

## 2. Install the bridge

Connect to the server: on Windows open **PowerShell**, on Mac open
**Terminal**, then type the following, using your IP:

```
ssh root@YOUR.SERVER.IP
```

Then paste this one line:

```
curl -fsSL https://raw.githubusercontent.com/lukejackson9-cloud/TRADING-BOT-./ccr-471a116f-0q22sz/deploy/discord_bridge/setup.sh -o setup.sh && bash setup.sh
```

It asks for your Trading 212 **demo** API key and secret (the secret won't
show as you type). At the end it prints three things. **Keep this window
open or copy them somewhere private**:
- the **URL** (ends in `.sslip.io/alert`)
- the **secret** (a long code)
- the **ntfy topic** (starts with `bridge-`)

## 3. Trade notifications on your phone

Install **ntfy** from the Play Store → tap **+** → enter the topic from
step 2 → Subscribe. Every buy, sell and pause will now arrive here.

## 4. Forward Discord notifications (MacroDroid, free)

1. In Discord, long-press the **Saucy Stocks** channel → Notification
   settings → **All Messages**.
2. Install **MacroDroid** from the Play Store. Give it notification access
   when asked.
3. Add Macro:
   - **Trigger**: *Device Events → Notification* → *Notification Received*
     → choose the **Discord** app → any content.
   - **Action**: *Connectivity → HTTP Request*
     - Method: **POST**
     - URL: the URL from step 2
     - Header: name `X-Bridge-Secret`, value the secret from step 2
     - Body / content type: **text/plain**
     - Body text: `[notification_title]` then a **new line** then
       `[notification]`. These are MacroDroid's "magic text" items; insert
       them with its magic-text button rather than typing them, in case the
       names differ slightly on your version.
4. Save the macro and make sure it's switched on. In Android settings, set
   MacroDroid's battery usage to **Unrestricted**, or the phone may stop it
   in the background.

## 5. Check it, then switch it on

When the next Saucy Stocks alert arrives, on the server run:

```
bridge log
```

You'll see a line for every forwarded notification, e.g.
`[alert] BUY 11.398 IREN ~27.855 (250.00 GBP, 5.0% of account) ...`
(in test mode the ntfy push says **[DRY RUN]**). Press Ctrl+C to stop
watching.

**Send Claude a few of these log lines.** Claude will check that the alerts
are being read correctly, and set the channel filter so other Discord
notifications are ignored.

To switch on real demo orders, run:

```
nano /etc/discord-bridge.env
```

Change `BRIDGE_DRY_RUN=1` to `BRIDGE_DRY_RUN=0`, save (Ctrl+O, Enter, Ctrl+X),
then run:

```
systemctl restart discord-bridge
```

## Everyday commands (on the server)

| Command | What it does |
|---|---|
| `bridge log` | watch it live |
| `bridge status` | open positions and whether it's paused |
| `bridge resume` | un-pause after the daily-loss stop |
| `bridge update` | install the latest code |
| `bridge parse "some alert text"` | see how an alert would be read |

## Things to know

- **The program checks stops and targets once a minute; they are not orders
  held at Trading 212.** If the server is down, open positions have no stop
  until it's back. The server restarts the program automatically if it
  crashes.
- If your phone is off, has no signal, or MacroDroid is killed, alerts are
  missed. Nothing is placed late. A missed alert is simply missed.
- Shares bought here mirror the author's **stock** alerts only. It does not
  see what they paid, and sizes are always 5% of your demo account.
- To change the API keys: `nano /etc/discord-bridge.env`, then
  `systemctl restart discord-bridge`.
