#!/usr/bin/env python3
"""
Autonomous Coffee Roasting AI Agent

Monitors roast progress and makes intelligent decisions using GPT-4.
Starts from user prompt, executes roast plan, monitors sensors, adjusts parameters.
"""
import os
import sys
import asyncio
import json
from datetime import datetime, UTC
from typing import Dict, Any
import requests
from openai import OpenAI
from mcp import ClientSession
from mcp.client.sse import sse_client

# Auth0 Configuration
# IMPORTANT: Set these as environment variables - do NOT hardcode credentials
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "https://coffee-roasting-api")

if not all([AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET]):
    raise ValueError("AUTH0_DOMAIN, AUTH0_CLIENT_ID, and AUTH0_CLIENT_SECRET must be set as environment variables")

# MCP Server URLs
ROASTER_SSE_URL = os.getenv("services__roaster-control__http__0", "http://localhost:5002") + "/sse"
DETECTION_SSE_URL = os.getenv("services__first-crack-detection__http__0", "http://localhost:5001") + "/sse"

# Agent configuration
MONITOR_INTERVAL = 5  # seconds between status checks
FC_CHECK_INTERVAL = 2  # seconds between FC status checks


def get_auth0_token():
    """Get Auth0 M2M access token."""
    response = requests.post(
        f"https://{AUTH0_DOMAIN}/oauth/token",
        json={
            "client_id": AUTH0_CLIENT_ID,
            "client_secret": AUTH0_CLIENT_SECRET,
            "audience": AUTH0_AUDIENCE,
            "grant_type": "client_credentials"
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]


class RoastingAgent:
    """Autonomous coffee roasting agent."""
    
    def __init__(self, openai_client: OpenAI, roaster_session, detection_session):
        self.ai = openai_client
        self.roaster = roaster_session
        self.detection = detection_session
        self.roast_start_time = None
        self.first_crack_time = None
        self.first_crack_detected = False
        self.roast_log = []
        
    async def create_roast_plan(self, prompt: str) -> Dict[str, Any]:
        """Ask GPT-4 to create a detailed roast plan."""
        print("\n🤔 Creating roast plan with AI...", flush=True)
        
        system_prompt = """You are an expert coffee roasting assistant. 
        Create a detailed roasting plan based on the user's requirements.
        
        Return a JSON object with:
        {
          "bean_type": "string",
          "target_roast": "string (light/medium/dark)",
          "initial_heat": number (0-100),
          "initial_fan": number (0-100),
          "target_fc_temp": number (celsius),
          "target_fc_time": number (minutes),
          "post_fc_adjustments": "string with instructions",
          "target_total_time": number (minutes),
          "drop_criteria": "string describing when to drop"
        }"""
        
        response = self.ai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt + "\n\nIMPORTANT: All timestamps use UTC. Return ONLY valid JSON, no other text."},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.choices[0].message.content
        # Try to extract JSON from response (might have markdown backticks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        plan = json.loads(content)
        print(f"📋 Roast Plan Created:", flush=True)
        print(json.dumps(plan, indent=2), flush=True)
        return plan
    
    async def start_roast(self, plan: Dict[str, Any]):
        """Start the roaster with initial parameters."""
        print("\n🔥 Starting roast...", flush=True)
        
        # Start roaster drum
        await self.roaster.call_tool("start_roaster", {})
        print("   ✓ Roaster drum started", flush=True)
        
        # Set initial parameters (override plan to ensure correct demo settings)
        initial_heat = 100  # Always 100% for fast demo roast
        initial_fan = 0     # Always 0% at start per demo requirements
        
        heat_result = await self.roaster.call_tool("set_heat", {"level": initial_heat})
        print(f"   🔍 Heat tool response: {heat_result.content[0].text}", flush=True)
        print(f"   ✓ Heat set to {initial_heat}%", flush=True)
        
        fan_result = await self.roaster.call_tool("set_fan", {"speed": initial_fan})
        print(f"   🔍 Fan tool response: {fan_result.content[0].text}", flush=True)
        print(f"   ✓ Fan set to {initial_fan}%", flush=True)
        
        # Start first crack detection
        await self.detection.call_tool("start_first_crack_detection", {
            "audio_source_type": "builtin_microphone"
        })
        print("   ✓ First crack detection started", flush=True)
        
        self.roast_start_time = datetime.now(UTC)
        self.log_event("Roast started", plan)
    
    async def monitor_roast(self, plan: Dict[str, Any]):
        """Monitor roast progress and make decisions."""
        print("\n👀 Monitoring roast progress...", flush=True)
        print(f"   Target: {plan['bean_type']} - {plan['target_roast']} roast", flush=True)
        
        while True:
            try:
                # Get current status
                status_result = await self.roaster.call_tool("read_roaster_status", {})
                status_response = json.loads(status_result.content[0].text)
                
                # Debug: print raw response first time
                if not hasattr(self, '_debug_printed'):
                    print(f"\n🔍 DEBUG - Raw status response: {json.dumps(status_response, indent=2)}", flush=True)
                    self._debug_printed = True
                
                # Handle both {"data": {...}} and {"status": "success", "data": {...}} formats
                if "data" in status_response:
                    status = status_response["data"]
                else:
                    status = status_response  # Assume direct format
                
                # Check first crack detection
                fc_result = await self.detection.call_tool("get_first_crack_status", {})
                fc_response = json.loads(fc_result.content[0].text)
                fc_status = fc_response.get("result", fc_response)  # Handle both formats
                
                # Debug FC status once
                if not hasattr(self, '_fc_debug_printed'):
                    print(f"\n🔍 DEBUG - FC status response: {json.dumps(fc_response, indent=2)}", flush=True)
                    self._fc_debug_printed = True
                
                elapsed_min = (datetime.now(UTC) - self.roast_start_time).total_seconds() / 60
                
                # Extract sensor data from nested structure
                sensors = status.get('sensors', {})
                temp = sensors.get('bean_temp_c') or sensors.get('bean_temperature') or sensors.get('temperature') or 0
                heat = sensors.get('heat_level_percent') or sensors.get('heat_level') or sensors.get('heat_percent') or sensors.get('heat') or 0
                fan = sensors.get('fan_speed_percent') or sensors.get('fan_speed') or sensors.get('fan_percent') or sensors.get('fan') or 0
                
                # Log current state
                print(f"\n⏱️  {elapsed_min:.1f} min | "
                      f"Temp: {temp:.1f}°C | "
                      f"Heat: {heat}% | "
                      f"Fan: {fan}%", flush=True)
            except Exception as e:
                print(f"\n❌ Error reading status: {e}", flush=True)
                print(f"   Status response was: {status_response if 'status_response' in locals() else 'not available'}", flush=True)
                await asyncio.sleep(MONITOR_INTERVAL)
                continue
            
            # Check for first crack
            if not self.first_crack_detected and fc_status.get("first_crack_detected"):
                await self.handle_first_crack(status, plan)
            
            # After FC, make AI decisions
            if self.first_crack_detected:
                should_continue = await self.make_decision(status, plan, elapsed_min)
                if not should_continue:
                    break
            
            await asyncio.sleep(MONITOR_INTERVAL)
    
    async def handle_first_crack(self, status: Dict, plan: Dict):
        """Handle first crack detection."""
        self.first_crack_detected = True
        self.first_crack_time = datetime.now(UTC)
        fc_elapsed = (self.first_crack_time - self.roast_start_time).total_seconds() / 60
        
        # Get temperature from sensors
        sensors = status.get('sensors', {})
        temp = sensors.get('bean_temp_c') or sensors.get('bean_temperature') or 0
        
        print(f"\n🔊 FIRST CRACK DETECTED at {fc_elapsed:.1f} minutes!", flush=True)
        print(f"   Temperature: {temp:.1f}°C", flush=True)
        
        self.log_event("First crack detected", {
            "time_min": fc_elapsed,
            "temp_c": temp
        })
        
        # Report to roaster
        await self.roaster.call_tool("report_first_crack", {
            "timestamp": self.first_crack_time.isoformat(),
            "temperature": temp
        })
    
    async def make_decision(self, status: Dict, plan: Dict, elapsed_min: float) -> bool:
        """Use AI to decide on parameter adjustments."""
        fc_elapsed = (datetime.now(UTC) - self.first_crack_time).total_seconds() / 60
        
        # Extract sensor data
        sensors = status.get('sensors', {})
        temp = sensors.get('bean_temp_c') or sensors.get('bean_temperature') or 0
        heat = sensors.get('heat_level_percent') or sensors.get('heat_level') or 0
        fan = sensors.get('fan_speed_percent') or sensors.get('fan_speed') or 0
        
        # Extract metrics (especially development time)
        metrics = status.get('metrics', {})
        dev_time_pct = metrics.get('development_time_percent') or 0
        dev_time_sec = metrics.get('development_time_seconds') or 0
        ror = metrics.get('rate_of_rise_c_per_min') or 0
        
        # Ask GPT-4 for decision
        decision_prompt = f"""POST-FIRST CRACK Decision Making

Current status ({fc_elapsed:.1f} min since FC):
- Bean temperature: {temp:.1f}°C
- Rate of rise: {ror:.1f}°C/min
- Current heat: {heat}%
- Current fan: {fan}%

DEVELOPMENT TIME (time since FC as % of total roast):
- Current: {dev_time_pct:.1f}%
- Target: 15-20%
- Status: {"ON TRACK" if 15 <= dev_time_pct <= 20 else "NEEDS ADJUSTMENT"}

DROP CRITERIA:
IDEAL: Development time 15-20% AND bean temperature 192-195°C
ACCEPTABLE: Development time 15-25% AND bean temperature 190-200°C
MANDATORY DROP: Temperature > 205°C (approaching burn)

Current status:
- Dev time: {dev_time_pct:.1f}% (target: 15-20%)
- Temperature: {temp:.1f}°C (target: 192-195°C)

RULES:
- Heat/fan values must be ABSOLUTE values between 0-100% in 10% increments (0,10,20,30...100)
- Current heat is {heat}% - to reduce, suggest lower value (e.g., 60, 70)
- Current fan is {fan}% - to increase, suggest higher value (e.g., 50, 60)
- NEVER suggest negative values or values > 100
- If dev time >= 15% and temp >= 190°C, consider dropping (good roast)
- If temp > 205°C, MUST drop immediately to prevent burning
- Goal: Stretch development to 15-20% while approaching 192-195°C

Should we:
1. Continue roasting with current settings
2. Adjust heat/fan
3. Drop beans and finish

Respond with JSON:
{{
  "action": "continue|adjust|drop",
  "reason": "explanation",
  "heat_adjustment": number or null,
  "fan_adjustment": number or null
}}"""
        
        response = self.ai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a coffee roasting expert making real-time decisions. All timestamps use UTC. Return ONLY valid JSON, no other text."},
                {"role": "user", "content": decision_prompt}
            ]
        )
        
        content = response.choices[0].message.content
        # Try to extract JSON from response (might have markdown backticks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        decision = json.loads(content)
        print(f"\n🧠 AI Decision: {decision['action'].upper()}", flush=True)
        print(f"   Reason: {decision['reason']}", flush=True)
        
        # EMERGENCY: Hard cutoff at 205°C - drop immediately
        if temp >= 205.0:
            print(f"\n⚠️  EMERGENCY DROP: Temperature {temp:.1f}°C exceeds 205°C safety limit!", flush=True)
            await self.finish_roast()
            return False
        
        # AUTO-DROP: If dev time is good and temp is acceptable, suggest drop
        if dev_time_pct >= 15.0 and temp >= 190.0 and decision["action"] != "drop":
            print(f"   ℹ️  Note: Drop criteria met (dev={dev_time_pct:.1f}%, temp={temp:.1f}°C) but AI chose to {decision['action']}", flush=True)
        
        if decision["action"] == "adjust":
            if decision["heat_adjustment"] is not None:
                # Validate and clamp heat to 0-100
                heat_val = max(0, min(100, int(decision["heat_adjustment"])))
                if heat_val != decision["heat_adjustment"]:
                    print(f"   ⚠️  Heat clamped from {decision['heat_adjustment']}% to {heat_val}%", flush=True)
                await self.roaster.call_tool("set_heat", {"level": heat_val})
                print(f"   ✓ Heat adjusted to {heat_val}%", flush=True)
            if decision["fan_adjustment"] is not None:
                # Validate and clamp fan to 0-100
                fan_val = max(0, min(100, int(decision["fan_adjustment"])))
                if fan_val != decision["fan_adjustment"]:
                    print(f"   ⚠️  Fan clamped from {decision['fan_adjustment']}% to {fan_val}%", flush=True)
                await self.roaster.call_tool("set_fan", {"speed": fan_val})
                print(f"   ✓ Fan adjusted to {fan_val}%", flush=True)
            
            self.log_event("AI adjustment", decision)
            return True
        
        elif decision["action"] == "drop":
            await self.finish_roast()
            return False
        
        else:  # continue
            return True
    
    async def finish_roast(self):
        """Drop beans and start cooling."""
        print("\n🎯 Finishing roast...", flush=True)
        
        # Stop detection
        await self.detection.call_tool("stop_first_crack_detection", {})
        print("   ✓ Detection stopped", flush=True)
        
        # Drop beans
        await self.roaster.call_tool("drop_beans", {})
        print("   ✓ Beans dropped", flush=True)
        
        # Start cooling
        await self.roaster.call_tool("start_cooling", {})
        print("   ✓ Cooling started", flush=True)
        
        total_time = (datetime.now(UTC) - self.roast_start_time).total_seconds() / 60
        print(f"\n✅ Roast complete! Total time: {total_time:.1f} minutes", flush=True)
        
        # Get final stats
        try:
            final_status_result = await self.roaster.call_tool("read_roaster_status", {})
            final_status_response = json.loads(final_status_result.content[0].text)
            final_status = final_status_response.get("data", final_status_response)
            
            print("\n📊 Final Roast Statistics:", flush=True)
            print(json.dumps(final_status, indent=2, default=str), flush=True)
        except Exception as e:
            print(f"\n⚠️  Could not retrieve final stats: {e}", flush=True)
        
        self.log_event("Roast finished", {"total_time_min": total_time})
    
    def log_event(self, event: str, data: Any):
        """Log roast event."""
        self.roast_log.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "event": event,
            "data": data
        })


async def run_autonomous_roast(roast_prompt: str):
    """Run autonomous roasting with user prompt."""
    import logging
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, force=True)
    sys.stdout.reconfigure(line_buffering=True)
    
    print("🤖 Autonomous Coffee Roasting Agent", flush=True)
    print("=" * 60, flush=True)
    
    # Authenticate
    print("\n🔐 Authenticating...", flush=True)
    token = get_auth0_token()
    print("   ✓ Authenticated", flush=True)
    
    # Connect to MCP servers
    print("\n🔌 Connecting to MCP servers...", flush=True)
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        async with sse_client(ROASTER_SSE_URL, headers=headers) as (roaster_read, roaster_write):
            async with ClientSession(roaster_read, roaster_write) as roaster_session:
                await roaster_session.initialize()
                print("   ✓ Roaster connected", flush=True)
                
                async with sse_client(DETECTION_SSE_URL, headers=headers) as (detection_read, detection_write):
                    async with ClientSession(detection_read, detection_write) as detection_session:
                        await detection_session.initialize()
                        print("   ✓ Detection connected", flush=True)
                        
                        # Initialize AI
                        if not os.getenv("OPENAI_API_KEY"):
                            print("   ✗ OPENAI_API_KEY not set", flush=True)
                            return
                        
                        ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                        print("   ✓ AI ready", flush=True)
                        
                        # Create agent
                        agent = RoastingAgent(ai_client, roaster_session, detection_session)
                        
                        # Create roast plan
                        plan = await agent.create_roast_plan(roast_prompt)
                        
                        # Execute roast
                        await agent.start_roast(plan)
                        await agent.monitor_roast(plan)
                        
                        # Save log
                        log_file = f"roast_log_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
                        with open(log_file, 'w') as f:
                            json.dump(agent.roast_log, f, indent=2)
                        print(f"\n📝 Roast log saved to: {log_file}", flush=True)
                        
    except Exception as e:
        print(f"\n✗ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Default roast prompt - adjust as needed
    prompt = """
    Demo roast with fast timeline (45s to first crack, 52s total).
    
    START SETTINGS (FIXED - no AI control):
    - Heat: 100% (full power to reach FC quickly)
    - Fan: 0% (no cooling at start)
    
    PRE-FC PHASE (0-45s) - NO AI ADJUSTMENTS:
    - 0-15s: Preheat phase (20°C -> ~180°C)
    - 15s: Beans charged (temp drops to 80°C)
    - 15-45s: Fast rise to first crack (~170°C)
    - Goal: MAXIMUM rate of rise to reach FC quickly
    - AI does NOT make adjustments - just monitors
    
    POST-FC PHASE (45-52s) - AI TAKES CONTROL:
    When first crack is detected, AI must:
    1. IMMEDIATELY reduce heat to 60-70%
    2. Gradually increase fan to 50-60%
    3. Monitor development_time_percent (time since FC / total roast time)
    4. Stretch development to 15-20% while approaching 192-195°C
    
    DROP CRITERIA (both required):
    - Development time: 15-20% of total roast
    - Bean temperature: 192-195°C
    - Do NOT drop until BOTH are met
    - Emergency drop if temp > 200°C (burnt!)
    
    CRITICAL UNDERSTANDING:
    - Development time = (time since FC) / (total roast time) * 100%
    - Before FC: development time is 0% (not relevant yet)
    - After FC: AI adjusts heat/fan to slow temp rise and stretch development
    - This is a FAST demo - only ~7 seconds for development phase
    """
    
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    
    print(f"\n📝 Roast Request:\n{prompt}\n", flush=True)
    asyncio.run(run_autonomous_roast(prompt))
