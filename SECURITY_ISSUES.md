# Critical Security Issues

## ⚠️ MUST FIX BEFORE PRODUCTION DEPLOYMENT

---

## 1. Hardcoded Secrets in Code (CRITICAL)

### Issue
**File:** `app/config.py`

```python
secret_key: str = Field("super-secret-key", env="SECRET_KEY")
super_admin_access_token: str = Field("Ckdgml9788@", env="SUPER_ADMIN_ACCESS_TOKEN")
```

**Risk Level:** 🔴 **CRITICAL**

**Impact:**
- Anyone with access to your GitHub repository can:
  - Forge authentication tokens
  - Access admin panel
  - Impersonate any user
  - Bypass all authentication

**Why This Is Dangerous:**
- Default values are committed to public repository
- If .env is not configured, these weak defaults are used in production
- Attackers can see the exact admin password in your code

### Fix Required:
1. Generate secure random keys:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. Set environment variables (NEVER commit):
```bash
SECRET_KEY=<your-random-key>
SUPER_ADMIN_ACCESS_TOKEN=<your-random-token>
```

3. Remove default values from config.py:
```python
secret_key: str = Field(..., env="SECRET_KEY")  # No default!
super_admin_access_token: str = Field(..., env="SUPER_ADMIN_ACCESS_TOKEN")  # No default!
```

4. **Immediately rotate** these secrets if the code has been committed to a public repo

---

## 2. Database File Committed to Repository (HIGH)

### Issue
The SQLite database `app/app.db` may contain user data, passwords, and sensitive information.

**Risk Level:** 🔴 **HIGH**

**Impact:**
- Exposes user accounts, emails, hashed passwords
- Leaks subscription data, API keys stored in DB
- Anyone cloning the repo gets a copy of your production data

### Fix Required:
1. Remove from repository:
```bash
git rm --cached app/app.db
git commit -m "Remove database from repository"
```

2. Already added to `.gitignore` ✅

3. If this was a production database:
   - Reset all user passwords
   - Invalidate all sessions
   - Rotate API keys stored in database
   - Notify affected users (if applicable under GDPR/privacy laws)

---

## 3. Payment/Subscription System Has No Security (CRITICAL)

### Issue
**File:** `app/routers/subscriptions.py`

```python
@router.post("/subscriptions/change")
def change_subscription(
    tier: SubscriptionTier = Form(...),
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    # NO PAYMENT VERIFICATION
    # NO PAYMENT GATEWAY INTEGRATION
    # NO VALIDATION
    subscription.tier = tier  # User can set any tier!
```

**Risk Level:** 🔴 **CRITICAL**

**Impact:**
- Any authenticated user can upgrade to PRO or ENTERPRISE for free
- No payment processing = no revenue
- Users can bypass account limits by self-upgrading
- No audit trail of subscription changes

**Current Flow:**
1. User calls `/subscriptions/change` with `tier=ENTERPRISE`
2. System immediately grants access
3. No payment required ❌
4. No email confirmation ❌
5. No admin approval ❌

### Fix Required:
Implement a proper payment flow:

1. **Add Payment Gateway Integration:**
   - Stripe, PayPal, or similar
   - Verify payment before changing tier

2. **Add Validation:**
```python
@router.post("/subscriptions/upgrade")
async def upgrade_subscription(
    tier: SubscriptionTier,
    payment_token: str,  # From payment gateway
    user: User = Depends(get_current_user),
):
    # 1. Validate payment with payment gateway
    payment = await stripe.charge.create(
        amount=get_price(tier),
        source=payment_token,
        description=f"Upgrade to {tier}"
    )

    if payment.status != "succeeded":
        raise HTTPException(400, "Payment failed")

    # 2. Update subscription
    subscription.tier = tier
    subscription.payment_id = payment.id

    # 3. Log the change
    audit_log.create(user, "subscription_upgrade", tier)

    return {"success": True}
```

3. **Add Downgrade Protection:**
```python
# Don't allow instant upgrades without payment
if new_tier > current_tier and not payment_verified:
    raise HTTPException(403, "Payment required for upgrade")
```

4. **Add Rate Limiting:**
- Prevent abuse of subscription endpoint
- Log all subscription changes

---

## 4. Missing Authentication on Critical Endpoints

### Issue
Some endpoints may be missing proper authentication checks.

**Risk Level:** 🟡 **MEDIUM**

**Check Required:**
Review all routes in:
- `app/routers/admin.py` - Should require super admin
- `app/routers/dashboard.py` - Should require authenticated user
- `app/routers/channels.py` - Should verify channel ownership

### Fix Required:
Ensure all sensitive routes have proper dependencies:
```python
@router.get("/admin/users")
def list_users(
    admin: User = Depends(require_super_admin),  # ✅ Protected
):
    ...

@router.delete("/channels/{channel_id}")
def delete_channel(
    channel_id: int,
    user: User = Depends(get_current_user),
    session = Depends(get_session)
):
    # ⚠️ Verify channel belongs to user!
    channel = session.get(Channel, channel_id)
    if channel.user_id != user.id:
        raise HTTPException(403, "Not your channel")
    ...
```

---

## 5. Social OAuth Credentials in Config

### Issue
**File:** `app/config.py`

OAuth secrets are stored in config with empty defaults:
```python
facebook_app_secret: str = Field("", env="FACEBOOK_APP_SECRET")
google_client_secret: str = Field("", env="GOOGLE_CLIENT_SECRET")
```

**Risk Level:** 🟡 **MEDIUM**

**Impact:**
- If these are filled and committed, attackers can:
  - Impersonate your app
  - Steal user OAuth tokens
  - Access user data from Facebook/Google

### Fix Required:
1. ✅ Already using environment variables (good!)
2. Ensure `.env` is in `.gitignore` ✅ (done)
3. Never commit OAuth secrets to repository
4. Use secret management in production (AWS Secrets Manager, GCP Secret Manager, etc.)

---

## 6. Mock Data Being Served as Real Data

### Issue
**File:** `app/services/social_fetcher.py`

When API credentials are missing or fail, the system serves **fake random data** to users:

```python
def get_channel_metrics(channel):
    try:
        return real_api_call(channel)
    except:
        return generate_mock_data()  # ⚠️ Serves fake data on error
```

**Risk Level:** 🟡 **MEDIUM** (Trust & Legal Issue)

**Impact:**
- Users see fake "real-time metrics"
- Cannot distinguish between real and mock data
- False analytics could lead to bad business decisions
- Potential legal issues if users pay for "real analytics"

### Fix Required:
1. **Never cache or serve mock data on error:**
```python
def get_channel_metrics(channel):
    try:
        return real_api_call(channel)
    except Exception as e:
        # Log error
        logger.error(f"Failed to fetch data: {e}")
        # Return error state, not fake data
        return {"error": "Unable to fetch metrics", "status": "api_error"}
```

2. **Add visual indicators in UI:**
```html
{% if metrics.is_mock %}
    <div class="alert alert-warning">
        ⚠️ Demo data - Connect your account to see real metrics
    </div>
{% endif %}
```

---

## Summary of Required Actions

### Before ANY deployment:
- [ ] Rotate `SECRET_KEY` and `SUPER_ADMIN_ACCESS_TOKEN`
- [ ] Remove default secrets from `app/config.py`
- [ ] Remove `app/app.db` from git history
- [ ] Set all secrets in environment variables
- [ ] Never commit `.env` file

### Before accepting payments:
- [ ] Implement real payment gateway (Stripe recommended)
- [ ] Add payment verification to subscription endpoints
- [ ] Add audit logging for all payment/subscription changes
- [ ] Add rate limiting to prevent abuse
- [ ] Test payment flow end-to-end

### Before launch:
- [ ] Review all API endpoints for proper authentication
- [ ] Add ownership checks to delete/update operations
- [ ] Stop serving mock data without clear user notification
- [ ] Set up monitoring for failed API calls
- [ ] Enable HTTPS only (disable HTTP)

---

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Stripe Payment Integration](https://stripe.com/docs/payments/quickstart)
- [FastAPI Security Guide](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Secrets Module](https://docs.python.org/3/library/secrets.html)

---

## Disclosure

If this repository is public and you've committed secrets:
1. **Assume they are compromised**
2. Immediately rotate all keys and passwords
3. Check for unauthorized access
4. Consider using tools like [GitGuardian](https://www.gitguardian.com/) to scan for leaked secrets
