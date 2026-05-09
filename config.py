# config.py
from dataclasses import dataclass
import numpy as np

# --- Physical Constants ---
G0 = 9.80665          # m/s^2 (Standard gravity)
PA_SL = 101325.0      # Pa (Sea-level atmospheric pressure)
T_SL = 288.15         # K (Sea-level temperature)
R_AIR = 287.05        # J/(kg*K) (Specific gas constant for air)
RHO_SL = 1.225        # kg/m^3 (Sea-level air density)

# --- Simulation Constants ---
SIM_MAX_TIME = 300.0  # s
GRAIN_DT = 0.005      # s
OPT_MAX_ITER = 50     # 최대 탐색 횟수
OPT_TOLERANCE = 0.5   # 고도 오차 허용 범위 (m)

# --- Data Models ---
@dataclass
class Propellant:
    density: float
    a: float  # Burn rate coefficient (m/s / Pa^n)
    n: float  # Burn rate exponent
    c_star: float

@dataclass
class RocketSpec:
    m0: float
    mp: float
    CD_A: float

@dataclass
class EngineDesign:
    tb_target: float
    k_gamma: float
    epsilon: float
    P0: float
    P_percentage: float
    efficiency: float
    D_chamber: float  # mm
    t_liner: float    # mm