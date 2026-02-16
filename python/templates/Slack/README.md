# Slack Bot Templates — Interactive Bot with Socket Mode

Reusable Python templates for building an interactive Slack bot using **Socket Mode** (WebSocket), capable of sending messages with interactive buttons, opening modals to collect user input, and publishing results to the Slack Home Tab.

---

## Architecture Overview

```
Slack Workspace
      │
      │  WebSocket (Socket Mode)
      ▼
 slack_bot.py  (SlackClient)
      │
      ├──► Receives events (messages, button clicks)
      │
      ├──► Opens modal  ◄── modal_slack.py (form definition)
      │         │
      │         ▼
      │    User submits form data
      │         │
      │         ▼
      └──► publicar_datos_home_slack.py
                │
                ▼
           Home Tab updated with results
```

---

## Files

| File | Description |
|------|-------------|
| `slack_bot.py` | Core bot class. Handles Socket Mode connection, event processing, interactive button clicks, modal submissions, and message sending. |
| `modal_slack.py` | Defines the Slack modal (form) structure with date pickers and numeric input fields. Returns the Block Kit JSON payload. |
| `publicar_datos_home_slack.py` | Formats processed results into a text table and publishes them to the user's Slack Home Tab. |

---

## Requirements

```bash
pip install slack-sdk requests
```

You will also need a Slack App with the following configuration:
- **Socket Mode** enabled.
- **Bot Token Scopes**: `chat:write`, `views:open`, `views:publish`.
- **Event Subscriptions**: `message.channels` (or the events relevant to your use case).
- **Interactivity** enabled (for button clicks and modal submissions).

---

## Configuration

Tokens are loaded from a secrets manager or environment variables — never hardcoded.

| Variable | Description |
|----------|-------------|
| `SLACK_BOT_TOKEN` | Bot User OAuth Token (`xoxb-...`) |
| `SLACK_APP_TOKEN` | App-Level Token for Socket Mode (`xapp-...`) |
| `CHANNEL_ID` | Comma-separated channel IDs to post messages to |

```python
# Example: loading from environment variables
import os
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
CHANNEL_IDS     = os.getenv("CHANNEL_ID", "").split(",")
```

---

## Usage

### 1. Start the bot (Socket Mode)

```python
from Slack.slack_bot import slack_client

slack_client.start_socket_mode()
```

The bot will connect to Slack via WebSocket and listen for events and interactions in real time.

### 2. Send a message with an interactive button

```python
slack_client.enviar_mensaje_con_boton()
```

Posts a message to all configured channels with a button that opens the data-entry modal when clicked.

### 3. Send a plain message via WebSocket

```python
slack_client.enviar_mensaje_via_websocket("Process completed successfully.")
```

### 4. Send a message via Incoming Webhook

```python
slack_client.enviar_mensaje_via_webhook(
    endpoint="https://hooks.slack.com/services/...",
    mensaje="Scheduled job finished."
)
```

### 5. Publish results to the Home Tab

```python
from Slack.publicar_datos_home_slack import publicar_resultado_home_slack

publicar_resultado_home_slack(shared_data, resultado_final)
```

Renders the results as a formatted text table and updates the Home Tab for the user who submitted the modal.

---

## Interaction Flow

1. Bot sends a message with a **button** to one or more channels.
2. User clicks the button → bot opens a **modal** (date pickers + numeric fields).
3. User fills and submits the form → bot captures the data in `shared_data`.
4. External processing logic uses `shared_data` to compute results.
5. Bot publishes a **formatted table** with results to the user's **Home Tab**.

---

## Key Concepts

**Socket Mode** connects your Slack app via WebSocket instead of a public HTTP endpoint, making it ideal for internal tools, local development, or environments without a public URL.

**Block Kit** is Slack's UI framework for building rich interactive messages and modals using JSON. The modal in `modal_slack.py` uses Block Kit's `input`, `datepicker`, and `number_input` elements.

**Home Tab** is a persistent surface in Slack (the App Home) where bots can publish dynamic content per user, used here to display processing results.

---

## Dependencies

```
slack-sdk
requests
```

---

## References

- [Slack Socket Mode](https://api.slack.com/apis/connections/socket)
- [Slack Block Kit](https://api.slack.com/block-kit)
- [Slack Views (Modals & Home Tab)](https://api.slack.com/surfaces/modals)
- [slack-sdk Python documentation](https://slack.dev/python-slack-sdk/)
