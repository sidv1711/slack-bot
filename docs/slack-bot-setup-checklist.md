# Slack Bot @Mention Setup Checklist

## 1. Slack App Configuration (api.slack.com/apps)

### **OAuth & Permissions**
- ✅ Add these Bot Token Scopes:
  - `chat:write` (Base permission for posting messages - REQUIRED)
  - `chat:write.public` (Post in any public channel without being invited)
  - `chat:write.customize` (Customize message formatting and appearance)
  - `app_mentions:read` (View messages that directly mention @your_slack_app)
  - `reactions:write` (Add and edit emoji reactions)
  - `users:read` (View people in a workspace)
  - `commands` (Add shortcuts and/or slash commands)
  - `channels:join` (Allow bot to join public channels automatically)
  - `im:read` (View basic information about direct messages)
  - `im:write` (Start direct messages with people)
  - `im:history` (View messages and content in direct messages)

### **Event Subscriptions**
- ✅ Enable Events: **ON**
- ✅ Request URL: `https://your-domain.com/events`
- ✅ Subscribe to bot events:
  - `app_mention` (Mentions @your_slack_app)
  - `message.im` (Listen to direct messages - REQUIRED for DM functionality)
  - `message.channels` (OPTIONAL: Listen to all channel messages)
  - `message.groups` (OPTIONAL: Listen to private channel messages)

### **App Home**
- ✅ Allow users to send Slash commands and messages from the messages tab: **ON**

### **Slash Commands** (Optional)
- Configure any custom slash commands your bot supports

## 2. Bot Installation & Channel Access

### **Installation Requirements**
- ✅ Bot must be **installed to the workspace**
- ✅ Bot must be **added to channels** where you want @mentions to work

### **Channel Access Methods**

#### Option A: Add Bot to Specific Channels
```
/invite @your_bot_name
```

#### Option B: Bot Auto-Joins Channels (Requires additional scope)
Add scope: `channels:join` to allow bot to join public channels automatically

#### Option C: Global Access (Enterprise Feature)
Some enterprise features allow bots to be accessible from all channels without manual addition.

## 3. Code Verification ✅

Your current code already handles this correctly:

### Event Handler (`src/bot/handlers.py`)
```python
@router.post("/events")
async def handle_slack_event(request: Request, slack_service: SlackService = Depends(get_slack_service)):
    # Handles URL verification and app_mention events
```

### Mention Processing (`src/bot/services.py`)
```python
async def _handle_mention(self, event: Dict[str, Any]) -> SlackResponse:
    # Processes @mentions and responds with AI
```

### OAuth Scopes (`src/auth/routes.py`)
```python
scopes=[
    "chat:write",           # Base permission for posting messages
    "chat:write.public",    # Post in any public channel
    "chat:write.customize", # Customize message formatting
    "reactions:write", 
    "users:read",
    "commands",
    "app_mentions:read",
    "channels:join",
    "im:read",
    "im:write",
    "im:history"
]
```

## 4. Testing & Troubleshooting

### **Test @Mentions**
1. **In Channels**: Add bot to a channel: `/invite @your_bot_name`
2. **Channel Mention**: `@your_bot_name hello`
3. **Direct Message**: Open DM with bot and type: `hello` or `@your_bot_name hello`
4. Bot should respond with AI assistance in both cases

### **Check Bot Presence**
- Bot appears in channel member list
- Bot has green "online" indicator
- Bot profile shows correct name/avatar

### **Common Issues**

#### Bot Not Responding
- ✅ Check event subscription URL is correct
- ✅ Verify bot token is valid
- ✅ Check logs for event processing errors
- ✅ Ensure bot is added to the channel

#### Permission Errors
- ✅ Re-install bot with updated scopes
- ✅ Check workspace admin hasn't restricted bot apps
- ✅ Verify OAuth redirect URI matches deployment

#### Bot Not Visible
- ✅ Bot needs to be explicitly added to channels
- ✅ Check if workspace has app approval workflows
- ✅ Verify bot user exists and is active

## 5. Advanced Configuration

### **Slack Connect** (Optional)
If you want cross-workspace @mentions:
- Enable Slack Connect in app settings
- Add `conversations.connect:read` scope

### **Enterprise Grid** (Optional)
For organization-wide access:
- Configure as "Organization-ready app"
- Add appropriate admin scopes

### **Auto-Installation** (Optional)
To reduce friction:
- Configure app manifest for automatic permissions
- Set up workspace discovery
- Enable team directory listing

## 6. Monitoring & Maintenance

### **Health Checks**
- ✅ Monitor `/healthz` endpoint
- ✅ Check event processing logs
- ✅ Verify bot token renewal

### **Performance**
- ✅ Monitor response times to @mentions
- ✅ Check AI service availability
- ✅ Track error rates in bot interactions

### **Troubleshooting "Sending messages to this app has been turned off"**

If you see this message in DMs, follow these steps:

1. **Check Event Subscriptions** at api.slack.com/apps → Your App → Event Subscriptions:
   - ✅ Enable Events: **ON**
   - ✅ Add `message.im` event (CRITICAL for DMs)
   - ✅ Request URL: `https://a63d65233152.ngrok.app/events`

2. **Verify OAuth Scopes** at OAuth & Permissions:
   - ✅ `im:read`, `im:write`, `im:history` must be present

3. **Reinstall Bot**: Go to `https://a63d65233152.ngrok.app/auth/slack/install`

4. **Check Workspace Settings**: Some workspaces restrict bot DMs

---

## Quick Verification Commands

### Check Bot Installation
```bash
# In Slack workspace
/apps manage
# Look for your bot in installed apps list
```

### Test Bot Mention
```bash
# In any channel where bot is added
@your_bot_name What is machine learning?
```

### Test Direct Messages
```bash
# Open DM with bot and send:
Hello, can you help me with Python?

# Or with explicit mention:
@your_bot_name Write a function to sort a list
```

### Verify Event Reception
```bash
# Check your application logs
grep "app_mention\|direct_message" /path/to/logs
```

---

## Direct Message (DM) Features

### **What Works in DMs**
- ✅ Send any message directly to the bot (no @mention needed)
- ✅ Bot responds with AI assistance automatically
- ✅ All AI services work: NL2SQL, Code Generation, General Chat
- ✅ Real-time "thinking" indicators and reactions
- ✅ Help message when sending empty messages

### **DM vs Channel Behavior**
| Feature | Direct Messages | Channels |
|---------|----------------|----------|
| **Trigger** | Any message | Must @mention bot |
| **Privacy** | Private 1:1 | Visible to channel |
| **Bot Invitation** | Automatic | Manual `/invite @bot` |
| **Response Style** | Direct reply | Thread or channel reply |

### **DM Testing Checklist**
1. ✅ Find bot in Slack workspace
2. ✅ Click on bot name to open DM
3. ✅ Send: `hello` - should get help message
4. ✅ Send: `What is machine learning?` - should get AI response
5. ✅ Send: `Write Python code to reverse a string` - should get code
6. ✅ Check for "thinking" message and ✅ reaction 