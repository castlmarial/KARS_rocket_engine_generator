# physics.py
import numpy as np
from scipy.optimize import root_scalar
from config import PA_SL, T_SL, R_AIR, G0, RHO_SL

def get_isa_atmosphere(h: float) -> tuple[float, float]:
    """Calculate air density and pressure using ISA standard atmosphere model."""
    if h < 0:
        return RHO_SL, PA_SL
        
    if h < 11000:
        T = T_SL - 0.0065 * h
        Pa = PA_SL * (T / T_SL)**5.2561
        rho = Pa / (R_AIR * T)
    else:
        T_11km = 216.65
        Pa_11km = 22632.0
        exponent = -G0 * (h - 11000) / (R_AIR * T_11km)
        Pa = Pa_11km * np.exp(exponent)
        rho = Pa / (R_AIR * T_11km)
        
    return rho, Pa

def calculate_exit_mach(epsilon: float, k: float) -> float:
    """Calculate exit Mach number safely using root_scalar bounded search."""
    def equation(Ma):
        if Ma <= 0: return 999 
        term1 = 1.0 / Ma
        term2 = (2 / (k + 1)) * (1 + (k - 1) / 2 * Ma**2)
        exponent = (k + 1) / (2 * (k - 1))
        return term1 * (term2 ** exponent) - epsilon

    # 안전하게 1.0에서 15.0 마하 사이에서 근을 찾음
    res = root_scalar(equation, bracket=[1.0, 15.0], method='brentq')
    return res.root