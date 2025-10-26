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
from datetime import datetime
from typing import Dict, Any
import requests
from openai import OpenAI
from mcp import ClientSession
from mcp.client.sse import sse_client

# Auth0 Configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "genai-7175210165555426.uk.auth0.com")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "Jk3aF2NfkiiOIXY0eHJQxfA6jkP0Pjf7")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "05agLnSUZceYK2Yl9bYGGnV_zuy7EAJ9ZWnMuOpCHEIOx2v8xZ7XNAmsQW020m2k")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "https://coffee-roasting-api")

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
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        plan = json.loads(response.choices[0].message.content)
        print(f"📋 Roast Plan Created:", flush=True)
        print(json.dumps(plan, indent=2), flush=True)
        return plan
    
    async def start_roast(self, plan: Dict[str, Any]):
        """Start the roaster with initial parameters."""
        print("\n🔥 Starting roast...", flush=True)
        
        # Start roaster drum
        await self.roaster.call_tool("start_roaster", {})
        print("   ✓ Roaster drum started", flush=True)
        
        # Set initial parameters
        await self.roaster.call_tool("set_heat", {"level": plan["initial_heat"]})
        print(f"   ✓ Heat set to {plan['initial_heat']}%", flush=True)
        
        await self.roaster.call_tool("set_fan", {"speed": plan["initial_fan"]})
        print(f"   ✓ Fan set to {plan['initial_fan']}%", flush=True)
        
        # Start first crack detection
        await self.detection.call_tool("start_first_crack_detection", {
            "audio_source_type": "builtin_microphone"
        })
        print("   ✓ First crack detection started", flush=True)
        
        self.roast_start_time = datetime.now()
        self.log_event("Roast started", plan)
    
    async def monitor_roast(self, plan: Dict[str, Any]):
        """Monitor roast progress and make decisions."""
        print("\n👀 Monitoring roast progress...", flush=True)
        print(f"   Target: {plan['bean_type']} - {plan['target_roast']} roast", flush=True)
        
        while True:
            # Get current status
            status_result = await self.roaster.call_tool("read_roaster_status", {})
            status = json.loads(status_result.content[0].text)["data"]
            
            # Check first crack detection
            fc_result = await self.detection.call_tool("get_first_crack_status", {})
            fc_status = json.loads(fc_result.content[0].text)
            
            elapsed_min = (datetime.now() - self.roast_start_time).total_seconds() / 60
            
            # Log current state
            print(f"\n⏱️  {elapsed_min:.1f} min | "
                  f"Temp: {status['bean_temp_c']:.1f}°C | "
                  f"Heat: {status['heat_level']}% | "
                  f"Fan: {status['fan_speed']}%", flush=True)
            
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
        self.first_crack_time = datetime.now()
        fc_elapsed = (self.first_crack_time - self.roast_start_time).total_seconds() / 60
        
        print(f"\n🔊 FIRST CRACK DETECTED at {fc_elapsed:.1f} minutes!", flush=True)
        print(f"   Temperature: {status['bean_temp_c']:.1f}°C", flush=True)
        
        self.log_event("First crack detected", {
            "time_min": fc_elapsed,
            "temp_c": status['bean_temp_c']
        })
        
        # Report to roaster
        await self.roaster.call_tool("report_first_crack", {
            "timestamp": self.first_crack_time.isoformat()
        })
    
    async def make_decision(self, status: Dict, plan: Dict, elapsed_min: float) -> bool:
        """Use AI to decide on parameter adjustments."""
        fc_elapsed = (datetime.now() - self.first_crack_time).total_seconds() / 60
        
        # Ask GPT-4 for decision
        decision_prompt = f"""Current roast status:
- Time since start: {elapsed_min:.1f} minutes
- Time since first crack: {fc_elapsed:.1f} minutes
- Bean temperature: {status['bean_temp_c']:.1f}°C
- Current heat: {status['heat_level']}%
- Current fan: {status['fan_speed']}%
- Target: {plan['bean_type']} - {plan['target_roast']} roast
- Target total time: {plan['target_total_time']} minutes

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
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a coffee roasting expert making real-time decisions."},
                {"role": "user", "content": decision_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        decision = json.loads(response.choices[0].message.content)
        print(f"\n🧠 AI Decision: {decision['action'].upper()}", flush=True)
        print(f"   Reason: {decision['reason']}", flush=True)
        
        if decision["action"] == "adjust":
            if decision["heat_adjustment"] is not None:
                await self.roaster.call_tool("set_heat", {"level": decision["heat_adjustment"]})
                print(f"   ✓ Heat adjusted to {decision['heat_adjustment']}%", flush=True)
            if decision["fan_adjustment"] is not None:
                await self.roaster.call_tool("set_fan", {"speed": decision["fan_adjustment"]})
                print(f"   ✓ Fan adjusted to {decision['fan_adjustment']}%", flush=True)
            
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
        
        total_time = (datetime.now() - self.roast_start_time).total_seconds() / 60
        print(f"\n✅ Roast complete! Total time: {total_time:.1f} minutes", flush=True)
        
        self.log_event("Roast finished", {"total_time_min": total_time})
    
    def log_event(self, event: str, data: Any):
        """Log roast event."""
        self.roast_log.append({
            "timestamp": datetime.now().isoformat(),
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
                        log_file = f"roast_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    We will be roasting coffee with a small home based electric roaster.
    The user will add the beans when the bean temperature is around 180°C. Thi is due to how this machine works.
    The roast control mcp tool will provide the readings and the events when getting status.
    When you start the machine, remeber to set the heat to 100%. Fan you can decide as appropriate.
    We have two MCP servers to help us. One for first crack and second to read / manage the roaster parameters.
    Target: Light-medium roast.
    With this machine first crack happens around 6-8 minute mark and 165-175°C bean temperature.
    When you get first crack confirmation from the first crack detection tool, you should call roaster tool to flag first crack happened.
    We have an MCP tool that will tell us if FC happened and when it happened in UTC.
    After first crack we want to stretch the development time by reducing heat from 100% and also gradually increasing fan.
    The goal is to get around 15-20% of roast time in development phase before first crack ends.
    The roasts that were successful ended up around 192°C and had about 15% development time.
    The MCP tools give everything needed to evaluate and act.
    Total roast time target: 11-12 minutes.
    """
    
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    
    print(f"\n📝 Roast Request:\n{prompt}\n", flush=True)
    asyncio.run(run_autonomous_roast(prompt))
