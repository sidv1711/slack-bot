# User Mapping Strategies: Slack to External Auth

## Overview

This document analyzes different approaches for mapping Slack users to external authentication systems (like PropelAuth), comparing trade-offs and industry best practices.

## Current Implementation: Manual `/connect-slack` Command

### How It Works
1. User runs `/connect-slack` in Slack
2. Bot sends OAuth link to PropelAuth
3. User authenticates with PropelAuth
4. System creates explicit user mapping
5. User returns to Slack

### Pros & Cons
✅ **Explicit user consent** - Users actively choose to connect  
✅ **Works with any auth provider** - Not dependent on email matching  
✅ **Handles edge cases** - Works even if emails don't match  
✅ **Clear audit trail** - Record of when user initiated connection  
✅ **Privacy compliant** - User controls the linking process  

❌ **Manual friction** - Users must remember to run command  
❌ **Adoption challenge** - Some users may never connect  
❌ **Extra onboarding step** - Not seamless  

## Alternative Strategies

### 1. Automatic Email-Based Mapping

```python
async def auto_map_by_email(slack_user_id: str):
    slack_user = await slack_client.users_info(user=slack_user_id)
    slack_email = slack_user["user"]["profile"]["email"]
    
    # Look up in PropelAuth by email
    propel_user = await propelauth.fetch_user_by_email(slack_email)
    if propel_user:
        await create_mapping(slack_user_id, propel_user.user_id)
```

**When to use:** High confidence in email matching (same domain, SSO)  
**Examples:** Zoom, Google Workspace integrations  

**Pros:**
✅ Zero friction - automatic  
✅ High adoption - all users mapped  
✅ Seamless experience  

**Cons:**
❌ Privacy concerns - no explicit consent  
❌ Email mismatch failures  
❌ Security risk - could link wrong accounts  
❌ Requires `users:read.email` scope  

### 2. Just-In-Time (JIT) Mapping

```python
async def handle_command(slack_user_id: str, command: str):
    mapping = await get_mapping(slack_user_id)
    if not mapping:
        return await prompt_connection()
    
    # Process authenticated command
    return await process_with_auth(mapping, command)
```

**When to use:** Context-aware applications  
**Examples:** Jira, GitHub integrations  

**Pros:**
✅ Only prompts when needed  
✅ Context-aware  
✅ Reduces unnecessary connections  

**Cons:**
❌ Interrupts user workflow  
❌ May delay critical actions  

### 3. Installation-Time OAuth

```python
# During Slack app installation
async def installation_flow():
    # Redirect installing user to PropelAuth
    # Auto-link their accounts
    pass
```

**When to use:** Single-user or admin-controlled installations  
**Examples:** Personal productivity apps  

**Pros:**
✅ One-time setup  
✅ Admin can control  

**Cons:**
❌ Only works for installer  
❌ Doesn't scale to team apps  

### 4. Hybrid Smart Mapping

```python
async def smart_mapping(slack_user_id: str):
    # 1. Check existing mapping
    existing = await get_mapping(slack_user_id)
    if existing:
        return existing
    
    # 2. Try email-based auto-mapping
    auto_mapped = await try_auto_map(slack_user_id)
    if auto_mapped:
        return auto_mapped
    
    # 3. Fall back to manual prompt
    await prompt_manual_connection(slack_user_id)
```

**When to use:** Best of both worlds approach  
**Examples:** Notion, sophisticated integrations  

## Industry Examples

### Notion Slack App
- **Strategy:** Manual command (`/notion`)
- **Reasoning:** Explicit consent, works across domains
- **UX:** Clear prompts, good onboarding

### GitHub Slack App  
- **Strategy:** JIT mapping on mention (`@username`)
- **Reasoning:** Natural workflow integration
- **UX:** Contextual prompts when relevant

### Jira Slack App
- **Strategy:** JIT when accessing Jira content
- **Reasoning:** Only when user needs Jira access
- **UX:** "Connect to view this issue" prompts

### Zoom Slack App
- **Strategy:** Email-based auto-mapping
- **Reasoning:** High confidence in corporate email matching
- **UX:** Seamless, works immediately

### Salesforce Slack App
- **Strategy:** Admin-configured SSO mapping
- **Reasoning:** Enterprise SSO integration
- **UX:** IT-managed, transparent to users

## Recommendations by Use Case

### 🏢 **Enterprise B2B SaaS (Our Case)**
**Recommended:** Manual `/connect-slack` + Smart fallbacks

**Reasoning:**
- Explicit consent for compliance
- Works across different email domains  
- Clear audit trail for security
- Professional user experience

**Enhanced Implementation:**
```bash
/connect-slack          # Smart mode (current)
/connect-slack manual   # Force OAuth flow
/connect-slack auto     # Try email matching
/connect-slack status   # Check connection
```

### 🏠 **Consumer Apps**
**Recommended:** Automatic email mapping + manual fallback

**Reasoning:**
- Minimize friction for consumers
- Higher adoption rates
- Less privacy sensitivity

### 🏢 **Enterprise with SSO**
**Recommended:** SSO attribute mapping

**Reasoning:**
- Leverage existing identity infrastructure
- IT-controlled and compliant
- Seamless for end users

### 🔧 **Developer Tools**
**Recommended:** JIT mapping on first use

**Reasoning:**
- Context-aware prompting
- Only when actually needed
- Developer-friendly workflow

## Security Considerations

### Email-Based Mapping Risks
- **Account takeover** if emails are compromised
- **Wrong user linking** with shared/forwarded emails
- **Privacy violations** without explicit consent

### Mitigation Strategies
- **Email verification** before auto-linking
- **User confirmation** for auto-detected mappings
- **Audit logging** of all mapping operations
- **Easy unlinking** mechanisms

## Implementation Recommendations

### Phase 1: Current Manual Approach ✅
- Keep `/connect-slack` as primary method
- Ensure robust error handling
- Add status checking capabilities

### Phase 2: Enhanced UX
- Add `/connect-slack status` for checking connections
- Improve messaging and onboarding
- Add connection management features

### Phase 3: Smart Hybrid (Optional)
- Add email-based auto-detection with consent
- Implement JIT prompting for key workflows
- A/B test different approaches

### Phase 4: Enterprise Features
- SSO integration for enterprise customers
- Admin management of user mappings
- Bulk connection tools

## Conclusion

Our current **manual `/connect-slack` command approach is the right choice** for a B2B SaaS integration because:

1. **Compliance-friendly** - Explicit user consent
2. **Secure** - No automatic account linking risks  
3. **Reliable** - Works regardless of email matching
4. **Professional** - Clear, controlled user experience
5. **Auditable** - Clear record of user actions

The enhanced version with multiple modes (`auto`, `manual`, `status`) provides flexibility while maintaining the security and compliance benefits of explicit user consent. 