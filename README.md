# 🚀 KNSB Solid Fuel Rocket Design & Flight Simulator

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B.svg)
![SciPy](https://img.shields.io/badge/SciPy-solve__ivp-8CAAE6.svg)

본 프로젝트는 KNSB(Potassium Nitrate/Sorbitol) 고체 추진제 로켓의 엔진 설계, 내탄도학(Internal Ballistics) 해석 및 비행 동역학(Flight Dynamics) 궤적을 예측하기 위한 통합 시뮬레이션 파이프라인입니다. 

사용자는 Streamlit 기반의 대시보드를 통해 설계 파라미터를 조정하고, 엔진 추력 곡선 및 비행 프로파일을 실시간으로 분석할 수 있습니다.

## ✨ Key Features

* **OOP 기반 아키텍처:** 물리 모델링, 엔진 상태 관리, 비행 동역학 및 UI 렌더링의 관심사 분리(Separation of Concerns)를 통한 확장성 확보.
* **정밀한 내탄도학 해석:** `scipy.optimize` 및 자체 적분 루틴을 활용하여 그레인 형상(BATES 등)의 연소 면적 변화에 따른 Chamber Pressure 및 Thrust Curve 도출.
* **6-DOF 기반 비행 시뮬레이션 (1-DOF Simplified for initial phase):** `scipy.integrate.solve_ivp` (RK45/BDF)를 활용하여 공기저항(Drag), 고도별 대기압(ISA Atmosphere Model), 질량 감소율이 반영된 정밀한 고도 및 속도 예측.
* **원클릭 데이터 파이프라인:** 모든 입력 파라미터, 설계 치수, 시뮬레이션 요약 지표 및 시계열(Time-series) 원시 데이터를 Excel(`.xlsx`) 파일로 자동 추출.

## 📂 Project Structure

프로젝트는 유지보수와 모듈화를 위해 5개의 핵심 파이썬 파일로 구성되어 있습니다.

text
'''
├── app.py         # Streamlit UI 렌더링, 사용자 입력 처리 및 컨트롤러 역할
├── config.py      # 물리 상수(Constants) 및 Dataclass 기반 설계/추진제 모델 정의
├── engine.py      # SolidMotor 클래스: 노즐 팽창비 계산 및 그레인 형상 기반 내탄도학 시뮬레이션
├── flight.py      # RocketFlightSim & FlightOptimizer 클래스: 운동 방정식(EOM) 적분 및 필요 추력 탐색
└── physics.py     # ISA 표준 대기 모델 및 루트 파인딩(Mach Number 계산) 등 순수 수학/물리 유틸리티
'''

⚙️ Installation
본 프로그램을 실행하기 위해서는 Python 3.9 이상의 환경이 권장됩니다.
가상 환경(Conda 또는 venv) 활성화 후 아래 명령어를 통해 필수 라이브러리를 설치하십시오.

pip install streamlit numpy scipy matplotlib pandas xlsxwriter

🚀 Quick Start
터미널에서 아래 명령어를 실행하여 웹 기반 GUI 대시보드를 시작합니다.

streamlit run app.py

📊 Outputs & Visualizations
시뮬레이션을 실행하면 대시보드 내에서 다음 정보를 즉각적으로 확인할 수 있습니다.

Dynamic Charts: 시간에 따른 고도(Altitude), 속도(Velocity), 챔버 압력(Pressure), 추력(Thrust) 변화 추이 그래프.
Performance Metrics: 목표 요구조건(Requirements) 대비 실제 시뮬레이션 성능(Avg Thrust, Isp, Total Impulse, Peak Pressure) 비교.
Hardware Specifications: 노즐 치수(Throat, Exit Diameter, Convergence/Divergence Angle) 및 그레인 기하 형상 치수.
Excel Export: 종합 리포트 다운로드 지원 (입력 변수, 결과 요약, 시계열 데이터 시트 포함).

🧑‍💻 Maintainer
Developed by: Engine Team Leader, KARS2026
Focus Area: Mechatronics Engineering, Control Systems, Solid Propulsion System Design & Numerical Modeling.
