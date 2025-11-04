# LLM Integration User Testing Guide

This guide explains how to test the new AI-powered personalized financial plans feature.

## Prerequisites

### 1. Install OpenAI Package
```bash
pip install openai>=1.0.0
```

### 2. Set OpenAI API Key
You need an OpenAI API key to test the AI features. Set it as an environment variable:

```bash
# On macOS/Linux
export OPENAI_API_KEY="your-api-key-here"

# On Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"

# Or add to your .env file (if using one)
echo "OPENAI_API_KEY=your-api-key-here" >> .env
```

**Note:** If you don't have an OpenAI API key, you can still test the system - it will fall back to the static catalog when AI features are requested.

### 3. Verify Database Schema
Make sure the database schema is up to date with AI consent columns:

```bash
python run.py --setup
```

This will create/update the database schema with the new `ai_consent_status` columns and `ai_plans` table.

## Testing via Web UI (Recommended)

### Step 1: Start the Server
```bash
python run.py --start
```

The server will start on `http://localhost:8000`

### Step 2: Open the User Dashboard
Open your browser and navigate to:
```
http://localhost:8000
```

### Step 3: Test the Complete Flow

#### 3.1. Load a User
1. Enter a user ID (e.g., `user_001`)
2. Click "Load Dashboard"
3. You should see the consent required message

#### 3.2. Grant Regular Consent
1. Click "Provide Consent"
2. The dashboard should load with:
   - Welcome section with persona
   - Behavioral insights
   - Standard recommendations (from static catalog)
   - Transactions and subscriptions

#### 3.3. Grant AI Consent
1. Scroll to the "AI-Powered Personalized Plans" section
2. You should see "AI consent is **not enabled**"
3. Click "Enable AI Recommendations"
4. You should see:
   - Success message: "AI consent granted successfully! Regenerating recommendations with AI..."
   - The dashboard reloading
   - If OpenAI API key is set: AI-generated recommendations appear
   - If OpenAI API key is NOT set: Error message and fallback to static catalog

#### 3.4. View AI-Generated Plan (if AI was used)
1. Scroll to the "Your AI-Generated Financial Plan" section
2. You should see:
   - Plan summary
   - Key insights
   - Action items
   - Model and token usage information

#### 3.5. Test Error Handling
**Scenario 1: No API Key**
- If `OPENAI_API_KEY` is not set, you should see:
  - Error message in the AI consent section
  - Fallback to static catalog recommendations
  - System continues to work normally

**Scenario 2: Invalid API Key**
- Set an invalid API key: `export OPENAI_API_KEY="invalid-key"`
- Grant AI consent
- You should see:
  - Error message about API failure
  - Fallback to static catalog
  - System continues to work

#### 3.6. Test AI Consent Revocation
1. Click "Disable AI Recommendations"
2. Confirm the action
3. You should see:
   - AI consent section shows "not enabled"
   - AI plan section disappears
   - Recommendations reload without AI (static catalog)

## Testing via API (Swagger UI)

### Step 1: Open Swagger UI
Navigate to:
```
http://localhost:8000/docs
```

### Step 2: Test AI Consent Endpoints

#### 2.1. Check AI Consent Status
1. Find `GET /users/{user_id}/ai-consent`
2. Click "Try it out"
3. Enter a user ID (e.g., `user_001`)
4. Click "Execute"
5. Response should show `ai_consent_status: false` initially

#### 2.2. Grant AI Consent
1. Find `POST /users/{user_id}/ai-consent`
2. Click "Try it out"
3. Enter a user ID (e.g., `user_001`)
4. Click "Execute"
5. Response should show `ai_consent_status: true`

#### 2.3. Get AI Recommendations
1. Find `GET /data/recommendations/{user_id}`
2. Click "Try it out"
3. Enter a user ID (e.g., `user_001`)
4. Set `use_ai` to `true`
5. Click "Execute"
6. Response should include:
   - `ai_used: true` (if API key is set and call succeeded)
   - `ai_error_message: null` (if successful) or error message (if failed)
   - `ai_model: "gpt-4"` (if successful)
   - `ai_tokens_used: <number>` (if successful)
   - Recommendations array with AI-generated content

#### 2.4. Get AI Plan
1. Find `GET /data/ai-plan/{user_id}`
2. Click "Try it out"
3. Enter a user ID (e.g., `user_001`)
4. Click "Execute"
5. Response should include:
   - `plan_document` with summary, insights, action items
   - `recommendations` array
   - `model_used` and `tokens_used`

#### 2.5. Revoke AI Consent
1. Find `DELETE /users/{user_id}/ai-consent`
2. Click "Try it out"
3. Enter a user ID (e.g., `user_001`)
4. Click "Execute"
5. Response should show `ai_consent_status: false`

## Testing via Command Line (cURL)

### Check AI Consent Status
```bash
curl -X GET "http://localhost:8000/users/user_001/ai-consent"
```

### Grant AI Consent
```bash
curl -X POST "http://localhost:8000/users/user_001/ai-consent"
```

### Get AI Recommendations
```bash
curl -X GET "http://localhost:8000/data/recommendations/user_001?use_ai=true"
```

### Get AI Plan
```bash
curl -X GET "http://localhost:8000/data/ai-plan/user_001"
```

### Revoke AI Consent
```bash
curl -X DELETE "http://localhost:8000/users/user_001/ai-consent"
```

## Test Scenarios

### Scenario 1: Happy Path (With API Key)
1. ✅ User loads dashboard
2. ✅ User grants regular consent
3. ✅ User grants AI consent
4. ✅ AI recommendations are generated and displayed
5. ✅ AI plan is displayed
6. ✅ Recommendations are personalized and relevant

### Scenario 2: Fallback (Without API Key)
1. ✅ User grants regular consent
2. ✅ User grants AI consent
3. ✅ Error message appears: "AI generation failed: OpenAI API key not configured"
4. ✅ Static catalog recommendations are displayed
5. ✅ System continues to work normally

### Scenario 3: API Error Handling
1. ✅ User grants AI consent
2. ✅ Set invalid API key: `export OPENAI_API_KEY="invalid"`
3. ✅ Request AI recommendations
4. ✅ Error message appears with specific error
5. ✅ Fallback to static catalog
6. ✅ System continues to work

### Scenario 4: Consent Revocation
1. ✅ User has AI consent granted
2. ✅ User has AI-generated plan displayed
3. ✅ User revokes AI consent
4. ✅ AI plan section disappears
5. ✅ Recommendations reload without AI
6. ✅ AI consent status shows "not enabled"

### Scenario 5: Multiple Users
1. ✅ Test with different users (user_001, user_002, etc.)
2. ✅ Each user should have independent AI consent status
3. ✅ Each user should get personalized AI plans
4. ✅ Revoking consent for one user doesn't affect others

## Verification Checklist

### AI Consent Management
- [ ] AI consent section appears after regular consent is granted
- [ ] AI consent can be granted via UI
- [ ] AI consent can be revoked via UI
- [ ] AI consent status persists across page reloads
- [ ] AI consent status is independent per user

### AI Recommendations
- [ ] AI recommendations are generated when consent is granted and API key is set
- [ ] AI recommendations are personalized to user's persona and signals
- [ ] AI recommendations include descriptions (not just titles)
- [ ] AI recommendations include rationales citing specific data
- [ ] Fallback to static catalog works when API fails
- [ ] Error messages are user-friendly and informative

### AI Plan Display
- [ ] AI plan section appears when AI is used
- [ ] AI plan includes summary, insights, and action items
- [ ] AI plan displays model and token usage information
- [ ] AI plan disappears when AI consent is revoked

### Error Handling
- [ ] Error messages appear when API key is missing
- [ ] Error messages appear when API call fails
- [ ] System continues to work after API errors
- [ ] Fallback to static catalog is seamless

### API Endpoints
- [ ] `POST /users/{user_id}/ai-consent` works
- [ ] `DELETE /users/{user_id}/ai-consent` works
- [ ] `GET /users/{user_id}/ai-consent` works
- [ ] `GET /data/recommendations/{user_id}?use_ai=true` works
- [ ] `GET /data/ai-plan/{user_id}` works
- [ ] All endpoints return proper error codes

## Troubleshooting

### Issue: "OpenAI API key not configured"
**Solution:** Set the `OPENAI_API_KEY` environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Issue: "AI generation failed: OpenAI API error"
**Solution:** Check your API key is valid and you have credits in your OpenAI account.

### Issue: "AI consent granted but recommendations not updating"
**Solution:** 
1. Check browser console for errors
2. Verify API endpoint is accessible
3. Check server logs for errors

### Issue: "AI plan section not showing"
**Solution:**
1. Verify AI consent is granted
2. Check that AI recommendations were successfully generated
3. Verify `GET /data/ai-plan/{user_id}` returns data
4. Check browser console for JavaScript errors

### Issue: Database errors
**Solution:** Run database setup again:
```bash
python run.py --setup
```

## Performance Testing

### Test Token Usage
1. Grant AI consent for a user
2. Generate AI recommendations
3. Check the response for `ai_tokens_used` field
4. Monitor OpenAI dashboard for actual usage

### Test Response Times
1. Measure time to generate AI recommendations
2. Should complete within the timeout (default: 30 seconds)
3. Fallback should be immediate if API fails

## Cost Considerations

- **Token Usage:** Each AI plan generation uses tokens (typically 2000-4000 tokens)
- **Cost:** Check OpenAI pricing for your model (GPT-4 is more expensive than GPT-3.5-turbo)
- **Model Selection:** Change `OPENAI_MODEL` in environment to use GPT-3.5-turbo for lower costs:
  ```bash
  export OPENAI_MODEL="gpt-3.5-turbo"
  ```

## Next Steps

After testing:
1. Review AI-generated recommendations for quality
2. Verify personalization is working correctly
3. Check error handling in various scenarios
4. Test with multiple users to ensure isolation
5. Monitor token usage and costs

## Support

For issues or questions:
1. Check server logs: `python run.py --start` (logs will show in terminal)
2. Check browser console for frontend errors
3. Verify database schema is up to date
4. Ensure all dependencies are installed

