import csv
import os
import sys

# 🛠️ 將包含 simulation_core 的那一層父資料夾加入搜尋路徑
# 這樣 Python 就會把 simulation_core 當成一個合法的頂層 Package
PARENT_DIR = r"C:\hospital-simulation\simulation-service"
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# 🔥 改用核心資料夾作為 Package 起點匯入
from simulation_core.models import SimulationParameters
from simulation_core.simulation import run_simulation


def generate_comparison_csv(filename="strategy_comparison_report.csv"):
    strategies = ["SBP", "IFP", "ALT"]
    comparison_rows = []

    print("🚀 完美對齊套件結構！開始批次執行 8/8/5 醫師班表下的跨策略模擬...")

    for strategy in strategies:
        print(f"正在執行 {strategy} 策略模擬...")
        
        # 建立參數物件，確保醫師人數是修改後的 8/8/5
        params = SimulationParameters(
            scheduling_strategy=strategy,
            num_general_doctors=5,
            num_senior_doctors=3,
            num_doctors_night=5,
            num_senior_doctors_night=2
        )
        
        # 執行該策略的模擬
        result = run_simulation(params)
        summary = result.summary
        
        # 擷取關鍵 KPI 指標
        comparison_rows.append({
            "排程策略 (Strategy)": strategy,
            "病人總數 (Total Patients)": summary.total_patients,
            "平均初診等待時間 (Avg Waiting Min)": round(summary.average_waiting_time, 2),
            "P95初診等待時間 (P95 Waiting Min)": round(summary.p95_waiting_time, 2),
            "平均總在院時間 (Avg LoS Min)": round(summary.average_time_in_system, 2),
            "平均醫療服務時間 (Avg Service Min)": round(summary.average_service_time, 2),
            "醫師總利用率 (Doctor Utilization)": f"{round(summary.resource_utilization.get('doctors', 0) * 100, 2)}%"
        })

    # 寫入 CSV (存放在專案大根目錄 C:\hospital-simulation 下)
    fieldnames = [
        "排程策略 (Strategy)", 
        "病人總數 (Total Patients)", 
        "平均初診等待時間 (Avg Waiting Min)", 
        "P95初診等待時間 (P95 Waiting Min)", 
        "平均總在院時間 (Avg LoS Min)", 
        "平均醫療服務時間 (Avg Service Min)", 
        "醫師總利用率 (Doctor Utilization)"
    ]
    
    output_path = os.path.join(r"C:\hospital-simulation", filename)
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comparison_rows)
        
    print(f"\n🎉 跨策略對比報告已成功產出！\n檔案路徑位於: {output_path}")


if __name__ == "__main__":
    generate_comparison_csv()