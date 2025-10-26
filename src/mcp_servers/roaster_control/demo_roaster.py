"""
Demo roaster hardware simulator.

Simulates realistic coffee roasting temperature lifecycle compressed into 1-3 minutes.
Responds dynamically to heat/fan control changes.
"""
import time
import logging
from datetime import datetime, UTC
from enum import Enum
from typing import Optional

from .hardware import HardwareInterface
from .models import SensorReading
from .exceptions import RoasterNotConnectedError


logger = logging.getLogger(__name__)


class RoastPhase(Enum):
    """Phases of roasting process."""
    PREHEAT = "preheat"
    CHARGE = "charge"  # Beans added, temp drops
    DRYING = "drying"
    APPROACHING_FC = "approaching_fc"
    FIRST_CRACK = "first_crack"
    DEVELOPMENT = "development"
    COOLDOWN = "cooldown"


class DemoRoaster(HardwareInterface):
    """
    Demo roaster with realistic temperature simulation.
    
    Simulates a full roast lifecycle:
    1. Preheat: Starting temperature
    2. Charge: Temp drop when beans added
    3. Drying: Slow temp rise
    4. Approaching FC: Faster rise
    5. First Crack: Exothermic temp rise
    6. Development: Controlled rise to target
    7. Cooldown: Rapid cooling after drop
    
    Responds to control changes:
    - set_heat(): Increases/decreases heating rate
    - set_fan(): Adds cooling effect
    - start_cooling(): Rapid cooldown
    """
    
    ROASTER_INFO = {
        "brand": "Demo",
        "model": "Simulator v2.0 (Realistic)",
        "version": "2.0.0"
    }
    
    def __init__(self, scenario):
        """
        Initialize demo roaster with scenario.
        
        Args:
            scenario: DemoScenario with timeline and temperature profile
        """
        self.scenario = scenario
        
        self._connected = False
        self._drum_running = False
        self._cooling = False
        
        # Control state
        self._heat = 0  # Start off
        self._fan = 0  # Start off
        
        # Temperature state
        # Beans start at room temp, chamber preheated
        self._bean_temp = 20.0  # Room temperature
        self._chamber_temp = scenario.preheat_temp
        
        # Timeline tracking
        self._roast_start_time: Optional[float] = None
        self._last_update: Optional[float] = None
        self._phase = RoastPhase.PREHEAT
        self._fc_triggered = False
        self._fc_trigger_time: Optional[float] = None
        self._charge_time: Optional[float] = None  # When beans were charged
        
        logger.info(f"DemoRoaster initialized with scenario: FC at {scenario.fc_trigger_time}s, "
                   f"duration {scenario.total_duration}s")
    
    def connect(self) -> bool:
        """Connect to demo roaster."""
        self._connected = True
        self._roast_start_time = time.time()
        self._last_update = time.time()
        logger.info("DemoRoaster connected")
        return True
    
    def disconnect(self):
        """Disconnect from demo roaster."""
        self._connected = False
        logger.info("DemoRoaster disconnected")
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected
    
    def get_roaster_info(self) -> dict:
        """Return demo roaster info."""
        return self.ROASTER_INFO.copy()
    
    def is_drum_running(self) -> bool:
        """Check if drum motor is running."""
        return self._drum_running
    
    def read_sensors(self) -> SensorReading:
        """
        Read simulated sensor values.
        
        Returns:
            SensorReading with current simulated values
        """
        if not self._connected:
            raise RoasterNotConnectedError()
        
        # Update simulation
        self._update_simulation()
        
        return SensorReading(
            timestamp=datetime.now(UTC),
            bean_temp_c=round(self._bean_temp, 1),
            chamber_temp_c=round(self._chamber_temp, 1),
            fan_speed_percent=self._fan,
            heat_level_percent=self._heat
        )
    
    def set_heat(self, percent: int):
        """Set heat level (affects heating rate)."""
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._validate_percentage(percent, "heat")
        old_heat = self._heat
        self._heat = percent
        logger.debug(f"Heat changed: {old_heat}% -> {percent}%")
    
    def set_fan(self, percent: int):
        """Set fan speed (affects cooling rate)."""
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._validate_percentage(percent, "fan")
        old_fan = self._fan
        self._fan = percent
        logger.debug(f"Fan changed: {old_fan}% -> {percent}%")
    
    def start_drum(self):
        """Start drum motor."""
        if not self._connected:
            raise RoasterNotConnectedError()
        
        if not self._drum_running:
            self._drum_running = True
            # Reset roast start when drum starts
            self._roast_start_time = time.time()
            self._last_update = time.time()
            self._phase = RoastPhase.PREHEAT  # Start with preheat
            logger.info("Drum started - preheating to charge point")
    
    def stop_drum(self):
        """Stop drum motor."""
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._drum_running = False
        logger.info("Drum stopped")
    
    def drop_beans(self):
        """Open bean drop door (stops drum, starts cooling)."""
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._drum_running = False
        self._cooling = True
        self._phase = RoastPhase.COOLDOWN
        logger.info("Beans dropped - cooling phase")
    
    def start_cooling(self):
        """Start cooling fan."""
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._cooling = True
        logger.debug("Cooling fan started")
    
    def stop_cooling(self):
        """Stop cooling fan."""
        if not self._connected:
            raise RoasterNotConnectedError()
        
        self._cooling = False
        logger.debug("Cooling fan stopped")
    
    def _validate_percentage(self, value: int, name: str):
        """Validate percentage is in valid range and 10% increments."""
        from .exceptions import InvalidCommandError
        
        if value < 0 or value > 100:
            raise InvalidCommandError(
                f"set_{name}",
                f"Value must be 0-100, got {value}"
            )
        if value % 10 != 0:
            raise InvalidCommandError(
                f"set_{name}",
                f"Value must be in 10% increments, got {value}"
            )
    
    def _update_simulation(self):
        """
        Update simulated temperatures based on phase, heat, fan, and time.
        
        Implements realistic roast progression through phases with
        dynamic response to control changes.
        """
        if not self._drum_running and not self._cooling:
            # No simulation updates when idle
            return
        
        now = time.time()
        dt = now - self._last_update
        self._last_update = now
        
        elapsed = now - self._roast_start_time
        
        # Update phase based on timeline
        self._update_phase(elapsed)
        
        # Calculate temperature change based on phase and controls
        if self._cooling:
            # Rapid cooldown mode
            temp_delta = -5.0 * dt  # Fast cooling
        else:
            # Normal roasting: base rate + control effects
            base_rate = self._get_phase_base_rate(elapsed)
            heat_effect = (self._heat / 100.0) * self.scenario.heat_rate_factor
            fan_effect = (self._fan / 100.0) * self.scenario.fan_cooling_factor
            
            temp_delta = (base_rate + heat_effect - fan_effect) * dt
        
        # Update temperatures
        self._bean_temp += temp_delta
        # Chamber temp follows bean temp more realistically
        self._chamber_temp = self._bean_temp + (5.0 if self._drum_running else 10.0)
        
        # Clamp to realistic ranges
        self._bean_temp = max(15.0, min(250.0, self._bean_temp))
        self._chamber_temp = max(15.0, min(300.0, self._chamber_temp))
    
    def _update_phase(self, elapsed: float):
        """Update current roast phase based on elapsed time."""
        if self._phase == RoastPhase.COOLDOWN:
            return  # Stay in cooldown
        
        # Charge at 15 seconds
        if self._phase == RoastPhase.PREHEAT and elapsed >= 15.0:
            self._phase = RoastPhase.CHARGE
            self._charge_time = time.time()
            # Gradual temp drop for T0 detection (not instant)
            # Temperature will drop naturally in next update cycle
            logger.info(f"Beans charged at 15s, temp will drop")
            return
        
        # Check for FC trigger
        if not self._fc_triggered and elapsed >= self.scenario.fc_trigger_time:
            self._fc_triggered = True
            self._fc_trigger_time = time.time()
            self._phase = RoastPhase.FIRST_CRACK
            logger.info(f"First crack triggered at {elapsed:.1f}s, temp: {self._bean_temp:.1f}°C")
            return
        
        # Phase transitions based on timeline
        if self._phase == RoastPhase.PREHEAT:
            # Stay in preheat until 15s
            pass
        elif self._phase == RoastPhase.CHARGE:
            # Move to drying after 3 seconds
            if self._charge_time and (time.time() - self._charge_time) > 3:
                self._phase = RoastPhase.DRYING
        elif self._phase == RoastPhase.DRYING:
            # Move to approaching FC at 20s (between charge and FC)
            if elapsed >= 20.0:
                self._phase = RoastPhase.APPROACHING_FC
        elif self._phase == RoastPhase.FIRST_CRACK:
            # Move to development 3 seconds after FC
            if self._fc_trigger_time and (time.time() - self._fc_trigger_time) > 3:
                self._phase = RoastPhase.DEVELOPMENT
    
    def _get_phase_base_rate(self, elapsed: float) -> float:
        """
        Get base temperature rise rate for current phase (°C/sec).
        
        This is the baseline heating rate before control adjustments.
        """
        phase = self._phase
        
        if phase == RoastPhase.PREHEAT:
            # Rapid rise from 20°C to ~180°C in 15 seconds
            # Need to gain ~160°C in 15s = ~10.7°C/s base
            return 8.0  # Base rate, will be boosted by heat setting
        
        elif phase == RoastPhase.CHARGE:
            # Simulate charge drop: first reading after charge shows big drop
            if self._charge_time and (time.time() - self._charge_time) < 0.5:
                # Force rapid drop to 80°C for T0 detection
                target_drop = 80.0
                drop_needed = self._bean_temp - target_drop
                return -drop_needed / 0.5  # Drop to 80°C in 0.5s
            # Then fast recovery (80°C -> ~140°C in ~5s)
            return 3.0  # Fast recovery
        
        elif phase == RoastPhase.DRYING:
            # Continue rise toward FC temp (~140°C -> ~160°C)
            return 2.0
        
        elif phase == RoastPhase.APPROACHING_FC:
            # Final push to FC temp (~160°C -> ~170°C)
            return 1.5
        
        elif phase == RoastPhase.FIRST_CRACK:
            # Exothermic spike
            fc_elapsed = time.time() - self._fc_trigger_time if self._fc_trigger_time else 0
            if fc_elapsed < 3:
                # Sharp rise during FC
                return self.scenario.fc_exothermic_rise / 3.0
            return 0.3  # Gentle rise after
        
        elif phase == RoastPhase.DEVELOPMENT:
            # Agent-controlled phase, minimal base rate
            return 0.2
        
        else:
            return 0.0
    
    def get_current_phase(self) -> RoastPhase:
        """Get current roast phase (useful for debugging/testing)."""
        return self._phase
    
    def has_fc_triggered(self) -> bool:
        """Check if first crack has been triggered."""
        return self._fc_triggered
