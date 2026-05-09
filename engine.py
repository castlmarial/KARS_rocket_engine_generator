# engine.py
import numpy as np
from config import GRAIN_DT, PA_SL
from config import Propellant, EngineDesign
from physics import calculate_exit_mach

class SolidMotor:
    def __init__(self, design: EngineDesign, prop: Propellant):
        self.design = design
        self.prop = prop
        self.nozzle_data = {}
        self.grain_data = {}

    def design_nozzle(self, F_req: float) -> dict:
        """목표 추력을 기반으로 노즐 치수 및 CF를 계산합니다."""
        Ma = calculate_exit_mach(self.design.epsilon, self.design.k_gamma)
        k = self.design.k_gamma
        
        Pe_ratio = (1 + (k - 1) / 2 * Ma**2)**(-k / (k - 1))
        Pc = self.design.P0 * self.design.P_percentage
        
        term1 = (2 * k**2 / (k - 1))
        term2 = (2 / (k + 1))**((k + 1) / (k - 1))
        term3 = (1 - Pe_ratio**((k - 1) / k))
        
        CF_ideal_momentum = np.sqrt(term1 * term2 * term3)
        CF_ideal_pressure = (Pe_ratio - PA_SL / Pc) * self.design.epsilon
        CF_real = (CF_ideal_momentum + CF_ideal_pressure) * self.design.efficiency
        
        At = F_req / (Pc * CF_real)
        
        self.nozzle_data = {
            "At": At,
            "Dt": np.sqrt(4 * At / np.pi),
            "Ae": At * self.design.epsilon,
            "De": np.sqrt(4 * At * self.design.epsilon / np.pi),
            "CF_real": CF_real,
            "Ma_exit": Ma,
            "Pc_avg": Pc
        }
        return self.nozzle_data

    def _run_internal_ballistics(self, d_core: float, D_grain: float, L_grain: float) -> tuple:
        """개별 그레인 형상에 대한 내탄도학 시뮬레이션 (상태 기반 시뮬레이션)"""
        rho, a, n, c_star = self.prop.density, self.prop.a, self.prop.n, self.prop.c_star
        At = self.nozzle_data['At']
        
        time_axis, thrust_axis, pressure_axis = [0.0], [0.0], [PA_SL]
        burn_depth, total_impulse = 0.0, 0.0
        
        while True:
            curr_d = d_core + 2 * burn_depth
            curr_L = L_grain - 2 * burn_depth
            if curr_d >= D_grain or curr_L <= 0: break
                
            Ab = (np.pi * curr_d * curr_L) + 2 * (np.pi/4 * (D_grain**2 - curr_d**2))
            Kn = Ab / At
            Pc = (Kn * rho * a * c_star) ** (1 / (1 - n))
            
            Cf_real = 1.45 * self.design.efficiency * (0.85 if Pc < 10*PA_SL else 1.0)
            F_inst = Pc * At * Cf_real
            
            time_axis.append(time_axis[-1] + GRAIN_DT)
            pressure_axis.append(Pc)
            thrust_axis.append(F_inst)
            
            total_impulse += F_inst * GRAIN_DT
            burn_depth += (a * (Pc ** n)) * GRAIN_DT
            
            if time_axis[-1] > 15.0: break # 안전망

        return np.array(time_axis), np.array(thrust_axis), np.array(pressure_axis), total_impulse

    def optimize_grain_geometry(self, mp: float) -> dict:
        """목표 연소시간(tb_target)에 맞춘 그레인 코어 반경 최적화 (이분탐색)"""
        D_grain = (self.design.D_chamber - 2 * self.design.t_liner) / 1000.0
        min_core, max_core = 0.005, D_grain - 0.005
        best_res = None

        for _ in range(15):
            test_core = (min_core + max_core) / 2.0
            area_cross = (np.pi/4) * (D_grain**2 - test_core**2)
            test_L = (mp / self.prop.density) / area_cross if area_cross > 0 else 0
            
            t_a, f_a, p_a, imp = self._run_internal_ballistics(test_core, D_grain, test_L)
            burn_time = t_a[-1]
            
            if abs(burn_time - self.design.tb_target) < 0.01:
                best_res = (test_core, test_L, t_a, f_a, p_a, imp)
                break
                
            if burn_time > self.design.tb_target: min_core = test_core
            else: max_core = test_core
            best_res = (test_core, test_L, t_a, f_a, p_a, imp)

        c, l, t_a, f_a, p_a, imp = best_res
        
        self.grain_data = {
            "D_grain_mm": D_grain * 1000.0, 
            "d_core_mm": c * 1000.0, 
            "L_grain_mm": l * 1000.0,
            "sim_time": t_a, 
            "sim_thrust": f_a, 
            "sim_total_impulse": imp,
            "sim_avg_pressure_bar": np.mean(p_a) / 1e5,
            "sim_max_pressure_bar": np.max(p_a) / 1e5,
            "sim_pressure_bar": p_a / 1e5
        }
        return self.grain_data