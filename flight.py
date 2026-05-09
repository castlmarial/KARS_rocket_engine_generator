# flight.py
import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d
from config import RocketSpec, EngineDesign
from config import SIM_MAX_TIME, G0, OPT_MAX_ITER, OPT_TOLERANCE
from physics import get_isa_atmosphere

class RocketFlightSim:
    def __init__(self, spec: RocketSpec):
        self.spec = spec

    def _eom_constant(self, t, X, F_avg, tb):
        h, v = X
        if h < 0 and v < 0: return [0, 0]
        
        F = F_avg if t <= tb else 0.0
        rho, _ = get_isa_atmosphere(h)
        m = self.spec.m0 - (self.spec.mp/tb * t if t <= tb else self.spec.mp)
        D = 0.5 * rho * self.spec.CD_A * (v**2) * np.sign(v)
        
        return [v, (F - D - m * G0) / m]

    def _eom_dynamic(self, t, X, thrust_interp, tb_end):
        h, v = X
        F = float(thrust_interp(t)) if t <= tb_end else 0.0
        rho, _ = get_isa_atmosphere(h)
        m = self.spec.m0 - (self.spec.mp/tb_end * t if t <= tb_end else self.spec.mp)
        
        net_force = F - (0.5 * rho * self.spec.CD_A * (v**2) * np.sign(v)) - (m * G0)
        if h <= 0 and net_force <= 0: return [0, 0]
        
        return [v, net_force / m]

    def run_constant_thrust(self, F_avg: float, tb: float) -> tuple:
        sol = solve_ivp(
            fun=lambda t, y: self._eom_constant(t, y, F_avg, tb),
            t_span=[0, SIM_MAX_TIME], y0=[0.0, 0.0],
            t_eval=np.linspace(0, SIM_MAX_TIME, 1000), rtol=1e-6
        )
        return sol.t, sol.y

    def run_dynamic_thrust(self, time_arr: np.ndarray, thrust_arr: np.ndarray) -> tuple:
        thrust_f = interp1d(time_arr, thrust_arr, bounds_error=False, fill_value=0.0)
        tb_end = time_arr[-1]

        def hit_ground(t, y):
            if t < 0.1: return 1
            return y[0] if y[1] < 0 else 1
        hit_ground.terminal = True
        hit_ground.direction = -1

        sol = solve_ivp(
            fun=lambda t, y: self._eom_dynamic(t, y, thrust_f, tb_end),
            t_span=[0, SIM_MAX_TIME], y0=[0.0, 0.0],
            events=hit_ground, t_eval=np.linspace(0, SIM_MAX_TIME, 3000), rtol=1e-6
        )
        return sol.t, sol.y

class FlightOptimizer:
    def __init__(self, spec: RocketSpec, design: EngineDesign):
        self.sim = RocketFlightSim(spec)
        self.tb = design.tb_target
        self.spec = spec

    def find_required_thrust(self, h_target: float) -> float:
        """목표 고도 달성을 위한 필요 평균 추력 산출 (Binary Search w/ tolerance)"""
        F_min, F_max = 10.0, 2000.0
        F_req = 100.0
        
        for _ in range(OPT_MAX_ITER):
            F_test = (F_min + F_max) / 2
            _, y = self.sim.run_constant_thrust(F_test, self.tb)
            h_max = np.max(y[0])
            
            if abs(h_max - h_target) < OPT_TOLERANCE:
                F_req = F_test
                break
                
            if h_max < h_target: F_min = F_test
            else: F_max = F_test
            F_req = (F_min + F_max) / 2
            
        return F_req