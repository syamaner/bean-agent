# Autonomous Roast Loop - User Guide

Complete workflow for long-running autonomous coffee roasting with AI decision-making.

---

## What This Workflow Does

Creates a **30-minute monitoring loop** (180 iterations × 10 seconds) where an AI agent:
1. Checks roaster status every 10 seconds
2. Monitors first crack detection
3. Makes intelligent adjustments (heat, fan)
4. Decides when to drop beans
5. Logs progress throughout the roast

**Perfect for**: Fully autonomous roasting with minimal human intervention

---

## Workflow Architecture

```
Start → Get Token → Initialize → Loop (180x max, ~30 min)
                                    ↓
                            Wait 10s → Increment Counter
                                    ↓
                            AI Agent (GPT-4o)
                            ├─ Roaster Control MCP
                            └─ First Crack Detection MCP
                                    ↓
                            Preserve State → Log Progress
                                    ↓
                            Check Continue? → Loop or Complete
```

---

## Key Features

### ✅ Automatic Loop Control
- Runs for max 30 minutes (safety timeout)
- Agent can end roast early by detecting completion criteria
- 10-second intervals = ~180 checks per 30-minute roast

### ✅ State Preservation
- Auth token persists across loop iterations
- Loop counter tracks elapsed time
- Agent responses logged at each iteration

### ✅ AI Decision Making
- Agent analyzes temperature, RoR, first crack timing
- Makes gradual adjustments (10-20% changes)
- Follows roasting best practices
- Safety limits enforced

### ✅ Progress Logging
- Sticky note shows real-time updates
- Each iteration logged with timestamp
- Final summary when complete

---

## Import & Setup

### 1. Import Workflow

1. Open n8n: http://localhost:5678
2. Click **+ Add workflow**
3. Menu (⋮) → **Import from File**
4. Select: `docs/03-phase-3/workflows/autonomous-roast-loop.json`

### 2. Configure OpenAI Credential

1. Click **OpenAI Chat Model** node
2. Select your OpenAI API credential
3. (Adjust model/temperature if desired)

### 3. Verify MCP Tool Endpoints

Both MCP Tool nodes should have:
- **SSE Endpoint**: `http://host.docker.internal:5002` (roaster) or `:5001` (detection)
- **Authentication**: Bearer
- **Bearer Token**: `={{ $('Initialize Variables').item.json.auth_token }}`

---

## How to Use

### Before Starting

1. **Ensure Aspire is running** with all services
2. **Preheat the roaster** (or let the agent do it)
3. **Have beans ready** to add when temperature reaches ~180°C

### Execute the Workflow

1. Click **Test workflow**
2. Click **Execute workflow**
3. **Watch the execution**:
   - First iteration starts immediately
   - Every 10 seconds, agent checks status and adjusts
   - Progress logged in real-time

### During the Roast

The workflow will automatically:
1. **Monitor**: Check temperatures, RoR, FC status
2. **Decide**: Analyze data and determine actions
3. **Act**: Adjust heat/fan or drop beans
4. **Log**: Record decisions and metrics
5. **Repeat**: Every 10 seconds

### When to Add Beans

The agent will monitor for preheat completion. When chamber temp reaches ~180°C:
1. Manually add beans to the roaster
2. The agent will detect the temperature drop (T0)
3. Roast timing begins automatically

### Stopping Early

If you need to stop:
1. Click **Stop execution** in n8n
2. Manually drop beans if needed (via separate workflow or Aspire logs)

---

## Customizing the Workflow

### Adjust Loop Duration

In **Check Continue** node, change max iterations:
```javascript
{{ $json.loop_count < 180 ? 'continue' : 'stop' }}
//                    ^^^
// 180 = 30 minutes (180 × 10s)
// 120 = 20 minutes
// 90 = 15 minutes
```

### Change Check Interval

In **Wait 10 Seconds** node:
- **Amount**: 10 (current)
- Try 5 for faster response
- Try 15 for less frequent (cheaper API calls)

### Modify AI Behavior

Edit **AI Roast Agent** node:

#### System Message (Roasting Knowledge)
Add specific profiles:
```
Light Ethiopian Natural:
- Target FC: 8-9 minutes
- Development: 18-20%
- Drop: 196-198°C
- Post-FC: Heat 60%, Fan 50%
```

#### User Prompt (Per-Iteration Task)
Make it more/less aggressive:
```
- Conservative: "Make small adjustments only (5-10%)"
- Aggressive: "Optimize for target profile aggressively"
```

### Add Safety Checks

Insert a **Switch** node after **AI Roast Agent**:
```javascript
// Check bean temp
{{ $json.bean_temp_c > 205 ? 'emergency' : 'continue' }}
```

Branch to emergency drop if safety limit exceeded.

---

## Example Roast Timeline

**Typical 12-minute roast**:

```
00:00 - Agent starts preheat (100% heat, 0% fan)
02:00 - Chamber reaches 180°C, ready for beans
02:30 - User adds beans, temp drops to ~80°C (T0 detected)
03:00 - Drying phase begins (high heat, building RoR)
05:00 - Maillard phase (monitoring RoR, ~6°C/min)
08:00 - First crack detected! (agent reduces heat to 65%, fan to 45%)
08:00-10:30 - Development phase (monitoring temp rise)
10:30 - Bean temp 196°C, agent drops beans
10:30 - Cooling starts, roast complete
```

---

## Monitoring Execution

### n8n UI

- **Execution list**: See all iterations
- **Node outputs**: Click nodes to see data
- **Sticky notes**: Real-time progress updates

### Aspire Dashboard

- **roaster-control logs**: See MCP tool calls
- **first-crack-detection logs**: See FC status checks
- **n8n logs**: See agent reasoning (if verbose)

### Key Metrics to Watch

- **Loop count**: How many iterations completed
- **Bean temp**: Current temperature
- **RoR**: Rate of rise (°C/min)
- **First crack**: Detected or not
- **Heat/Fan**: Current settings

---

## Troubleshooting

### Workflow Stops After First Iteration

**Check**: Wait node webhook ID is set
**Fix**: Ensure **Wait 10 Seconds** node has a webhook ID

### Agent Makes No Adjustments

**Possible causes**:
1. MCP tools not connecting (check Auth0 token)
2. Agent not understanding prompt
3. Roaster already at optimal settings

**Fix**: Check MCP Tool node logs, improve system prompt

### Loop Doesn't Preserve State

**Check**: **Preserve State** node settings
**Fix**: Ensure `keepOnlySet: true` and all variables listed

### Agent Too Slow

**Optimize**:
1. Use `gpt-4o-mini` instead of `gpt-4o`
2. Reduce `maxTokens` (1500 → 1000)
3. Increase temperature (0.3 → 0.5)

---

## Advanced: Add Roast Profiles

Create multiple workflows for different roast levels:

### Light Roast Profile
- Target FC: 8-9 minutes
- Development: 18-20%
- Drop: 195-198°C
- Post-FC heat: 60%, fan: 50%

### Medium Roast Profile
- Target FC: 7-8 minutes
- Development: 15-18%
- Drop: 205-210°C
- Post-FC heat: 65%, fan: 45%

### Dark Roast Profile
- Target FC: 6-7 minutes
- Development: 12-15%
- Drop: 215-220°C
- Post-FC heat: 50%, fan: 60%

---

## Safety Notes

⚠️ **Always monitor the first roast**
⚠️ **Keep beans ready at preheat completion**
⚠️ **Have manual override ready** (stop execution button)
⚠️ **Never exceed 205°C bean temp** (agent enforces this)
⚠️ **Test with mock hardware first**

---

## Next Steps

✅ Import and test workflow  
→ Run with mock hardware  
→ Adjust AI prompts for your preferences  
→ Create roast profile variations  
→ Test with real hardware  
→ Build roast log storage  

---

**Ready to roast autonomously!** ☕🤖

Import `autonomous-roast-loop.json` and let the AI take over!
