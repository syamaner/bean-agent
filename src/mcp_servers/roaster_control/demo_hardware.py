"""
Demo Hardware Simulator for Coffee Roasting

Simulates a realistic roast lifecycle in 1-3 minutes for demos.
Configurable duration with proper temperature curves and phases.
"""
import time
import threading
from datetime import datetime, timedelta, UTC
from typing import Optional
from .models import RoasterState, SensorReading


class DemoRoaster:
    """
    Fast demo roaster that simulates a realistic roast in 1-3 minutes.
    
    Phases:
    1. Preheat (0-15% of time): Heat to 180°C
    2. Charge beans (15%): Temp drops to ~100°C
    3. Drying (15-45%): Gradual rise to 165°C
    4. First Crack (45-50%): Reaches 170-175°C
    5. Development (50-85%): Controlled rise to 192-196°C
    6. Drop (85%+): Hold until finish
    """
    
    def __init__(self, roast_duration_sec: int = 120):
        """
        Initialize demo roaster.
        
        Args:
            roast_duration_sec: Total roast duration in seconds (60-180)
                               Default 120s (2 min) for quick demos
        """
        self.roast_duration_sec = max(60, min(180, roast_duration_sec))
        self.state = RoasterState.DISCONNECTED
        self.running = False
        
        # Roast tracking
        self.roast_start_time: Optional[datetime] = None
        self.beans_charged_time: Optional[datetime] = None
        self.first_crack_time: Optional[datetime] = None
        
        # Current values
        self.bean_temp = 20.0  # Room temperature
        self.env_temp = 20.0
        self.heat_level = 0
        self.fan_speed = 0
        self.cooling_active = False
        
        # Simulation thread
        self._sim_thread: Optional[threading.Thread] = None
        self._stop_sim = threading.Event()
        
        # Phase timing (as fraction of total duration)
        self.PREHEAT_END = 0.15      # 15%
        self.CHARGE_AT = 0.15         # 15%
        self.DRYING_END = 0.45        # 45%
        self.FC_START = 0.45          # 45%
        self.FC_END = 0.50            # 50%
        self.DEVELOPMENT_END = 0.85   # 85%
        
        # Target temperatures
        self.PREHEAT_TEMP = 180.0
        self.CHARGE_DROP_TEMP = 100.0
        self.DRYING_END_TEMP = 165.0
        self.FC_TEMP = 172.0
        self.DEVELOPMENT_END_TEMP = 194.0
        
    def connect(self) -> bool:
        """Connect to demo roaster."""
        self.state = RoasterState.IDLE
        return True
    
    def disconnect(self):
        """Disconnect from demo roaster."""
        self.stop_roaster()
        self.state = RoasterState.DISCONNECTED
    
    def is_connected(self) -> bool:
        """Check if roaster is connected."""
        return self.state != RoasterState.DISCONNECTED
    
    def start_roaster(self):
        """Start roaster drum and simulation."""
        if not self.is_connected():
            raise RuntimeError("Roaster not connected")
        
        self.running = True
        self.state = RoasterState.PREHEATING
        self.roast_start_time = datetime.now(UTC)
        
        # Start simulation thread
        self._stop_sim.clear()
        self._sim_thread = threading.Thread(target=self._simulate_roast, daemon=True)
        self._sim_thread.start()
    
    def stop_roaster(self):
        """Stop roaster drum and simulation."""
        self.running = False
        self._stop_sim.set()
        if self._sim_thread:
            self._sim_thread.join(timeout=1.0)
        self.state = RoasterState.IDLE
    
    def set_heat(self, level: int):
        """Set heat level (0-100)."""
        self.heat_level = max(0, min(100, level))
    
    def set_fan(self, speed: int):
        """Set fan speed (0-100)."""
        self.fan_speed = max(0, min(100, speed))
    
    def drop_beans(self):
        """Drop beans into cooling tray."""
        self.running = False
        self.cooling_active = True
        self.state = RoasterState.COOLING
    
    def start_cooling(self):
        """Start cooling fan."""
        self.cooling_active = True
    
    def stop_cooling(self):
        """Stop cooling fan."""
        self.cooling_active = False
        if self.state == RoasterState.COOLING:
            self.state = RoasterState.IDLE
    
    def read_sensors(self) -> SensorReading:
        """Read current sensor values."""
        return SensorReading(
            bean_temp_c=self.bean_temp,
            env_temp_c=self.env_temp,
            timestamp=datetime.now(UTC)
        )
    
    def _simulate_roast(self):
        """Simulate realistic roast progression."""
        UPDATE_INTERVAL = 0.5  # Update twice per second
        
        while not self._stop_sim.is_set() and self.running:
            elapsed = (datetime.now(UTC) - self.roast_start_time).total_seconds()
            progress = min(1.0, elapsed / self.roast_duration_sec)
            
            # Determine current phase and update temperature
            if progress < self.PREHEAT_END:
                # Phase 1: Preheat
                self._simulate_preheat(progress / self.PREHEAT_END)
                
            elif progress < self.CHARGE_AT + 0.01:
                # Phase 2: Charge beans (instant drop)
                if self.beans_charged_time is None:
                    self.beans_charged_time = datetime.now(UTC)
                    self.state = RoasterState.ROASTING
                self.bean_temp = self.CHARGE_DROP_TEMP
                
            elif progress < self.DRYING_END:
                # Phase 3: Drying phase
                phase_progress = (progress - self.CHARGE_AT) / (self.DRYING_END - self.CHARGE_AT)
                self._simulate_drying(phase_progress)
                
            elif progress < self.FC_END:
                # Phase 4: First crack
                if self.first_crack_time is None:
                    self.first_crack_time = datetime.now(UTC)
                phase_progress = (progress - self.FC_START) / (self.FC_END - self.FC_START)
                self._simulate_first_crack(phase_progress)
                
            elif progress < self.DEVELOPMENT_END:
                # Phase 5: Development
                phase_progress = (progress - self.FC_END) / (self.DEVELOPMENT_END - self.FC_END)
                self._simulate_development(phase_progress)
                
            else:
                # Phase 6: Hold at finish temp
                self.bean_temp = self.DEVELOPMENT_END_TEMP
            
            # Update env temp (follows bean temp with lag)
            self.env_temp = self.bean_temp * 0.85 + 20
            
            # Apply cooling if active
            if self.cooling_active:
                self.bean_temp = max(20, self.bean_temp - 10 * UPDATE_INTERVAL)
            
            time.sleep(UPDATE_INTERVAL)
    
    def _simulate_preheat(self, progress: float):
        """Simulate preheat phase."""
        self.bean_temp = 20 + (self.PREHEAT_TEMP - 20) * progress
        # Heat effect: higher heat = faster rise
        heat_factor = self.heat_level / 100.0
        self.bean_temp *= (0.7 + 0.3 * heat_factor)
    
    def _simulate_drying(self, progress: float):
        """Simulate drying phase with realistic RoR."""
        # Temperature rises from charge drop to drying end
        target_temp = self.CHARGE_DROP_TEMP + (self.DRYING_END_TEMP - self.CHARGE_DROP_TEMP) * progress
        
        # Apply heat influence
        heat_factor = self.heat_level / 100.0
        fan_factor = 1.0 - (self.fan_speed / 200.0)  # Fan slows heating
        
        self.bean_temp += (target_temp - self.bean_temp) * 0.1 * heat_factor * fan_factor
    
    def _simulate_first_crack(self, progress: float):
        """Simulate first crack phase."""
        # Rapid temperature rise during FC
        target_temp = self.DRYING_END_TEMP + (self.FC_TEMP - self.DRYING_END_TEMP) * progress
        
        heat_factor = self.heat_level / 100.0
        fan_factor = 1.0 - (self.fan_speed / 150.0)
        
        # FC is exothermic, add extra heat
        exothermic_boost = 2.0 * progress
        self.bean_temp += (target_temp - self.bean_temp) * 0.15 * heat_factor * fan_factor + exothermic_boost
    
    def _simulate_development(self, progress: float):
        """Simulate development phase with controlled rise."""
        # Slower, controlled rise to finish temp
        target_temp = self.FC_TEMP + (self.DEVELOPMENT_END_TEMP - self.FC_TEMP) * progress
        
        heat_factor = self.heat_level / 100.0
        fan_factor = 1.0 - (self.fan_speed / 180.0)
        
        # Development should be slow and controlled
        self.bean_temp += (target_temp - self.bean_temp) * 0.08 * heat_factor * fan_factor
    
    def get_roast_progress(self) -> dict:
        """Get roast progress information."""
        if not self.roast_start_time:
            return {"progress": 0, "phase": "not_started"}
        
        elapsed = (datetime.now(UTC) - self.roast_start_time).total_seconds()
        progress = min(1.0, elapsed / self.roast_duration_sec)
        
        # Determine phase
        if progress < self.PREHEAT_END:
            phase = "preheat"
        elif progress < self.CHARGE_AT + 0.01:
            phase = "charge"
        elif progress < self.DRYING_END:
            phase = "drying"
        elif progress < self.FC_END:
            phase = "first_crack"
        elif progress < self.DEVELOPMENT_END:
            phase = "development"
        else:
            phase = "finishing"
        
        return {
            "progress": progress,
            "phase": phase,
            "elapsed_sec": elapsed,
            "remaining_sec": self.roast_duration_sec - elapsed,
            "bean_temp": self.bean_temp,
            "first_crack_time": self.first_crack_time.isoformat() if self.first_crack_time else None
        }
