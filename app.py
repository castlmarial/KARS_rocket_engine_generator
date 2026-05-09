import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import io
from datetime import datetime

# 리팩토링된 모듈 임포트
from config import Propellant, RocketSpec, EngineDesign, G0
from engine import SolidMotor
from flight import RocketFlightSim, FlightOptimizer

# --- 1. 페이지 설정 (최상단에 한 번만!) ---
st.set_page_config(
    page_title="KNSB Rocket Simulator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 메인 화면: 인트로 섹션 (버전 정보 및 프로젝트 개요) ---
# 버튼을 누르기 전(결과가 나오기 전)에 보여줄 초기 화면입니다.
def show_welcome_page():
    st.title("🚀 KNSB Solid Fuel Rocket Design & Flight Simulator")
    
    # 상단 3개 카드 레이아웃
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("### 🧪 Internal Ballistics\nBATES 그레인 형상 및 추진제 연소 특성을 기반으로 한 정밀한 챔버 압력 예측")
    with col2:
        st.success("### 🛰️ 1-DOF Simulation\nISA 표준 대기 모델과 RK45 솔버를 결합한 해석")
    with col3:
        st.warning("### 📊 Engineering Report\n입력 변수부터 시계열 데이터까지 원클릭 Excel 리포트 생성 및 추출")

    st.markdown("---")
    
    # 중간 상세 설명 섹션
    m_col1, m_col2 = st.columns([1.5, 1])
    with m_col1:
        st.subheader("📌 System Overview")
        st.markdown("""
        본 시뮬레이터는 **KNSB 고체 추진제** 로켓의 설계부터 비행 고도 예측까지의 전 과정을 수치해석적으로 모델링합니다. 
        왼쪽 사이드바에서 설계 파라미터를 입력하고 **Run Simulation** 버튼을 눌러 시뮬레이션을 시작하세요.
        
        * **OOP Architecture:** 물리 모델과 UI의 철저한 분리.
        * **Physics-Based:** Saint-Robert's Law ($r = aP_c^n$) 기반 연소 모델.
        * **Professional Specs:** 노즐 팽창비 및 최적 그레인 치수 자동 산출.
        """)
        
    with m_col2:
        st.subheader("📝 Physics Engine")
        # 수식 표시 (LaTeX 활용)
        st.latex(r"r = a \cdot P_c^n")
        st.latex(r"P_c = \left( \frac{a \rho_p A_b}{C_d A_t} \right)^{\frac{1}{1-n}}")
        st.caption("Theoretical Chamber Pressure Balance Equation")

# --- 푸터 함수 정의 ---
def show_footer():
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; padding: 40px 0px 20px 0px; color: #64748b;">
            <p style="font-size: 14px; letter-spacing: 1px; margin-bottom: 10px;">
                © 2026 KNSB Rocket Project
            </p>
            <p style="font-size: 18px; font-weight: 700; color: #3b82f6;">
                KARS2026 | Propulsion Team Leader | PARK SEONG-JAE
            </p>
            <div style="margin-top: 15px; font-family: monospace; font-size: 13px;">
                Mechatronics Engineering & Control Systems Focus
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Sidebar: 모든 설계 파라미터 입력 ---
with st.sidebar:
    st.header("🛠️ Design Parameters")
    
    st.subheader("🧪 Propellant Properties")
    prop_rho = st.number_input("Density (kg/m³)", value=1650.0, step=10.0)
    c_star_input = st.number_input("C* (m/s)", value=910.0, step=1.0)
    prop = Propellant(density=prop_rho, a=0.1007/1000.0, n=0.319, c_star=c_star_input)

    st.subheader("🎯 Target Settings")
    h_target = st.number_input("Target Altitude (m)", value=280.0, format="%.1f")

    st.subheader("🚀 Rocket Specifications")
    m0 = st.number_input("Total Mass (kg)", value=6.00, format="%.2f")
    mp = st.number_input("Propellant Mass (kg)", value=0.400, format="%.3f")
    CD_A = st.number_input("Drag Coeff × Area (m²)", value=0.00264, format="%.5f")
    spec = RocketSpec(m0=m0, mp=mp, CD_A=CD_A)

    st.subheader("🔥 Engine/Nozzle Design")
    tb = st.number_input("Burn Time (s)", value=1.5, format="%.2f")
    k_gamma = st.number_input("Specific Heat Ratio", value=1.137, format="%.3f")
    epsilon = st.number_input("Expansion Ratio", value=5.000, format="%.3f")
    P0 = st.number_input("Max Target Pressure (Pa)", value=3_000_000, step=100_000)
    P_percentage = st.number_input("Avg to Max P Ratio (%)", value=61.5) / 100.0
    efficiency_factor = st.slider("Efficiency (η)", 0.5, 1.0, 0.92, 0.01)
    
    alpha_div = st.number_input("Divergence Half Angle (°)", value=15.0, format="%.1f")
    beta_conv = st.number_input("Convergence Half Angle (°)", value=45.0, format="%.1f")
    
    st.subheader("📏 Grain Geometry Inputs")
    D_chamber_in = st.number_input("Chamber ID (mm)", value=54.0)
    t_liner_in = st.number_input("Liner Thickness (mm)", value=2.0)
    
    design = EngineDesign(
        tb_target=tb, k_gamma=k_gamma, epsilon=epsilon, 
        P0=P0, P_percentage=P_percentage, efficiency=efficiency_factor,
        D_chamber=D_chamber_in, t_liner=t_liner_in
    )

    run_button = st.button("Run Simulation & Design", type="primary", use_container_width=True)

if not run_button:
    show_welcome_page()
else:
    # 1. 시뮬레이션 계산 엔진 가동
    optimizer = FlightOptimizer(spec, design)
    F_req = optimizer.find_required_thrust(h_target)
    
    motor = SolidMotor(design, prop)
    nozzle_res = motor.design_nozzle(F_req)
    grain_res = motor.optimize_grain_geometry(spec.mp)
    
    flight_sim = RocketFlightSim(spec)
    t_sim, y_sim = flight_sim.run_dynamic_thrust(grain_res['sim_time'], grain_res['sim_thrust'])
    
    # 지표 산출
    h_max = np.max(y_sim[0])
    v_max = np.max(y_sim[1])
    initial_weight = spec.m0 * G0
    twr = np.max(grain_res['sim_thrust']) / initial_weight
    isp_target = F_req / ((spec.mp / design.tb_target) * G0)
    sim_impulse = grain_res['sim_total_impulse']
    sim_isp = sim_impulse / (spec.mp * G0)
    req_impulse = F_req * design.tb_target

    # ---------------------------------------------------------
    # [1] 그래프 섹션 (4종)
    # ---------------------------------------------------------
    st.markdown("---")
    st.header("📈 Flight & Engine Dynamics")
    
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))
    axs[0, 0].plot(t_sim, y_sim[0], color='dodgerblue', lw=2)
    axs[0, 0].set_title('Altitude vs Time', fontweight='bold')
    axs[0, 0].grid(True, linestyle='--', alpha=0.6)

    axs[0, 1].plot(t_sim, y_sim[1], color='mediumseagreen', lw=2)
    axs[0, 1].set_title('Velocity vs Time', fontweight='bold')
    axs[0, 1].grid(True, linestyle='--', alpha=0.6)

    if 'sim_pressure_bar' in grain_res:
        axs[1, 0].plot(grain_res['sim_time'], grain_res['sim_pressure_bar'], color='darkorange', lw=2)
    axs[1, 0].set_title('Chamber Pressure vs Time', fontweight='bold')
    axs[1, 0].grid(True, linestyle='--', alpha=0.6)

    axs[1, 1].plot(grain_res['sim_time'], grain_res['sim_thrust'], color='crimson', lw=2)
    axs[1, 1].axhline(initial_weight, color='gray', ls='--', label='Initial Weight')
    axs[1, 1].set_title('Thrust vs Time', fontweight='bold')
    axs[1, 1].legend(); axs[1, 1].grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    st.pyplot(fig)

    # 피크값 메트릭
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("Maximum Altitude (Apogee)", f"{h_max:.2f} m", f"{h_max - h_target:+.2f} m vs Target")
    m_col2.metric("Maximum Velocity (V-max)", f"{v_max:.2f} m/s")

    # ---------------------------------------------------------
    # [2] 정보 (Information) 섹션 - UI 출력용
    # ---------------------------------------------------------
    st.markdown("---")
    st.header("📋 Specifications & Results")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Requirements")
        st.write(f"* **Avg Thrust:** `{F_req:.2f} N`")
        st.write(f"* **Total Impulse:** `{req_impulse:.2f} N·s`")
        st.write(f"* **Target Isp:** `{isp_target:.2f} s`")
        st.write(f"* **Target Pc:** `{design.P0 / 1e5:.1f} bar`")
        st.subheader("🛠️ Nozzle Specs")
        st.write(f"* **Throat (Dt):** `{nozzle_res['Dt']*1000:.2f} mm`")
        st.write(f"* **Exit (De):** `{nozzle_res['De']*1000:.2f} mm`")
        st.write(f"* **Div Angle:** `{alpha_div:.1f}°`")
        st.write(f"* **Conv Angle:** `{beta_conv:.1f}°`")
        st.write(f"* **Efficiency:** `{design.efficiency*100:.1f}%`")

    with col2:
        st.subheader("🧪 Simulation Values")
        st.write(f"* **Sim Avg Thrust:** `{sim_impulse/grain_res['sim_time'][-1]:.2f} N`")
        st.write(f"* **Sim Impulse:** `{sim_impulse:.2f} N·s`")
        st.write(f"* **Sim Isp:** `{sim_isp:.2f} s`")
        st.write(f"* **Peak Pressure:** `{grain_res['sim_max_pressure_bar']:.2f} bar`/ **Avg Pressure:** `{grain_res['sim_avg_pressure_bar']:.2f} bar`")
        st.subheader("📏 Grain Specs")
        st.write(f"* **Outer Dia:** `{grain_res['D_grain_mm']:.2f} mm`")
        st.write(f"* **Core Dia:** `{grain_res['d_core_mm']:.2f} mm`")
        st.write(f"* **Length:** `{grain_res['L_grain_mm']:.2f} mm`")
        st.write(f"* **Density:** `{prop.density:.1f} kg/m³`")

    # ---------------------------------------------------------
    # [3] Excel Export 섹션 - 입력값 및 모든 사양 포함
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📤 Export Comprehensive Data")

    # A. 설계 입력 파라미터 데이터프레임
    df_inputs = pd.DataFrame({
        "Category": ["Target", "Propellant", "Propellant", "Rocket", "Rocket", "Rocket", "Engine", "Engine", "Engine", "Engine", "Engine", "Engine", "Nozzle", "Nozzle", "Geometry", "Geometry"],
        "Parameter": ["Target Altitude", "Density", "C*", "Initial Mass", "Propellant Mass", "CD_A", "Burn Time", "Specific Heat Ratio", "Expansion Ratio", "Max Target Pressure", "Avg to Max P Ratio", "Efficiency", "Divergence Half Angle", "Convergence Half Angle", "Chamber ID", "Liner Thickness"],
        "Value": [h_target, prop.density, prop.c_star, spec.m0, spec.mp, spec.CD_A, design.tb_target, design.k_gamma, design.epsilon, design.P0, P_percentage * 100, design.efficiency, alpha_div, beta_conv, design.D_chamber, design.t_liner],
        "Unit": ["m", "kg/m³", "m/s", "kg", "kg", "m²", "s", "-", "-", "Pa", "%", "-", "deg", "deg", "mm", "mm"]
    })

    # B. 출력값 데이터프레임
    df_output = pd.DataFrame({
        "Metric": [
            "Avg Thrust", "Total Impulse", "Target Isp",
            "Sim Avg Thrust", "Sim Impulse", "Sim Isp",
            "Peak Pressure", "Avg Pressure",
            "Nozzle Throat", "Nozzle Exit",
            "Div Angle", "Conv Angle", "Nozzle Efficiency",
            "Grain Outer Diameter", "Grain Core Diameter", "Grain Length", "Grain Density",
            "Maximum Altitude", "Maximum Velocity"
        ],
        "Value": [
            F_req, req_impulse, isp_target,
            sim_impulse/grain_res['sim_time'][-1], sim_impulse, sim_isp,
            grain_res['sim_max_pressure_bar'], grain_res['sim_avg_pressure_bar'],
            nozzle_res['Dt']*1000, nozzle_res['De']*1000,
            alpha_div, beta_conv, design.efficiency*100,
            grain_res['D_grain_mm'], grain_res['d_core_mm'], grain_res['L_grain_mm'], prop.density,
            h_max, v_max
        ],
        "Unit": [
            "N", "N·s", "s",
            "N", "N·s", "s",
            "bar", "bar",
            "mm", "mm",
            "deg", "deg", "%",
            "mm", "mm", "mm", "kg/m³",
            "m", "m/s"
        ]
    })

    # C. 시계열 데이터
    df_series = pd.DataFrame({
        "Time (s)": grain_res['sim_time'],
        "Thrust (N)": grain_res['sim_thrust'],
        "Pressure (bar)": grain_res['sim_pressure_bar'] if 'sim_pressure_bar' in grain_res else 0
    })

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df_inputs.to_excel(writer, sheet_name='Design_Inputs', index=False)
        df_output.to_excel(writer, sheet_name='Output_Data', index=False)
        df_series.to_excel(writer, sheet_name='Raw_Time_Series', index=False)
    
    st.download_button(
        label="💾 Download All Data as Excel (.xlsx)",
        data=excel_buffer.getvalue(),
        file_name=f"KARS_SimInput_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# 시뮬레이션 결과 화면 하단에 푸터 표시
show_footer()
