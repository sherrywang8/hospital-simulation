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
from simulation_core.simulation import build_strategy_comparison_rows


def generate_comparison_csv(filename="strategy_comparison_report.csv"):
    print("🚀 完美對齊套件結構！開始批次執行 8/8/5 醫師班表下的跨策略模擬...")

    # 對齊目前三班制護理師 schema，使用現行預設值作為跨策略公平比較基準
    params = SimulationParameters(
        num_general_doctors=5,
        num_senior_doctors=3,
        num_doctors_night=5,
        num_senior_doctors_night=2,
        num_nurses_day=16,
        num_nurses_evening=16,
        num_nurses_night=8,
    )
    comparison_rows = build_strategy_comparison_rows(params)

    # 寫入 CSV (存放在專案大根目錄 C:\hospital-simulation 下)
    fieldnames = [
        "排程策略 (Strategy)", 
        "病人總數 (Total Patients)", 
        "平均初診等待時間 (Avg Waiting Min)", 
        "P95初診等待時間 (P95 Waiting Min)", 
        "平均總在院時間 (Avg LoS Min)", 
        "平均醫療服務時間 (Avg Service Min)", 
        "醫師總利用率 (Doctor Utilization)",
        "護理師總利用率 (Nurse Utilization)",
    ]
    
    output_path = os.path.join(r"C:\hospital-simulation", filename)
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comparison_rows)
        
    print(f"\n🎉 跨策略對比報告已成功產出！\n檔案路徑位於: {output_path}")


if __name__ == "__main__":
    generate_comparison_csv()
