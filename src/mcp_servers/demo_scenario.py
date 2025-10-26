"""
Demo scenario configuration for coordinated simulation across MCP servers.

Both roaster control and FC detection MCP servers load the same scenario
to ensure consistent timeline and behavior in demo mode.
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DemoScenario:
    """Demo scenario parameters for coordinated simulation."""
    
    # Timeline
    fc_trigger_time: float  # seconds from roast start when FC occurs
    total_duration: float  # total roast duration in seconds
    
    # Temperature profile
    preheat_temp: float  # starting temperature (°C)
    charge_temp_drop: float  # temp drop when beans added (°C)
    fc_temp: float  # temperature at first crack (°C)
    fc_exothermic_rise: float  # temp rise during FC (°C)
    end_temp: float  # target end temperature (°C)
    
    # Response rates (how fast temp changes with controls)
    heat_rate_factor: float  # °C/sec per 10% heat
    fan_cooling_factor: float  # °C/sec per 10% fan
    
    @classmethod
    def from_env(cls, default_name: str = "quick_roast") -> "DemoScenario":
        """Load scenario from environment variables."""
        scenario_name = os.getenv("DEMO_SCENARIO", default_name)
        
        # Check if loading from predefined scenarios
        if scenario_name in PREDEFINED_SCENARIOS:
            return PREDEFINED_SCENARIOS[scenario_name]
        
        # Otherwise load from individual env vars
        return cls(
            fc_trigger_time=float(os.getenv("DEMO_FC_TIME", "90")),
            total_duration=float(os.getenv("DEMO_TOTAL_DURATION", "180")),
            preheat_temp=float(os.getenv("DEMO_PREHEAT_TEMP", "200")),
            charge_temp_drop=float(os.getenv("DEMO_CHARGE_DROP", "30")),
            fc_temp=float(os.getenv("DEMO_FC_TEMP", "196")),
            fc_exothermic_rise=float(os.getenv("DEMO_FC_RISE", "8")),
            end_temp=float(os.getenv("DEMO_END_TEMP", "210")),
            heat_rate_factor=float(os.getenv("DEMO_HEAT_RATE", "0.3")),
            fan_cooling_factor=float(os.getenv("DEMO_FAN_COOLING", "0.15"))
        )


# Predefined scenarios
PREDEFINED_SCENARIOS = {
    "quick_roast": DemoScenario(
        fc_trigger_time=45.0,  # FC at 45 seconds (more realistic)
        total_duration=52.0,  # ~52s total (45s + 15% dev = 45 + 7 = 52s)
        preheat_temp=200.0,  # Chamber preheat
        charge_temp_drop=30.0,  # Not used anymore (hardcoded to 80°C)
        fc_temp=170.0,  # FC temperature
        fc_exothermic_rise=5.0,  # Small exothermic rise during FC
        end_temp=195.0,  # Target drop temperature
        heat_rate_factor=3.0,  # Much faster heating (was 1.5)
        fan_cooling_factor=0.5  # More responsive fan for agent control
    ),
    "medium_roast": DemoScenario(
        fc_trigger_time=120.0,  # 2 minutes
        total_duration=240.0,  # 4 minutes total
        preheat_temp=200.0,
        charge_temp_drop=35.0,
        fc_temp=196.0,
        fc_exothermic_rise=8.0,
        end_temp=215.0,
        heat_rate_factor=0.25,
        fan_cooling_factor=0.15
    ),
    "light_roast": DemoScenario(
        fc_trigger_time=100.0,
        total_duration=200.0,
        preheat_temp=200.0,
        charge_temp_drop=30.0,
        fc_temp=196.0,
        fc_exothermic_rise=6.0,
        end_temp=205.0,
        heat_rate_factor=0.3,
        fan_cooling_factor=0.15
    )
}


def get_demo_scenario() -> Optional[DemoScenario]:
    """
    Get demo scenario if in demo mode, otherwise None.
    
    Returns:
        DemoScenario if DEMO_MODE env var is true, otherwise None
    """
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    if not demo_mode:
        return None
    
    return DemoScenario.from_env()
