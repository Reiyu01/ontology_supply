import pandas as pd
import os

# 讀取所有 Excel 檔案
files = [
    "DDB-1845, cánh nhôm, dây đồng và dây nhôm 100V-50-60Hz.xls",
    "DDB-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls",
    "DSE-1845, cánh nhôm, dây đồng và dây nhôm 100V-50-60Hz.xls",
    "DSE-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls",
    "KMH-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls",
    "KWJ-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls"
]

print("=" * 80)
print("分析 Excel 檔案結構")
print("=" * 80)

for file in files[:1]:  # 先分析第一個檔案
    print(f"\n檔案: {file}")
    print("-" * 80)
    
    try:
        # 讀取所有工作表
        excel_file = pd.ExcelFile(file)
        print(f"工作表數量: {len(excel_file.sheet_names)}")
        print(f"工作表名稱: {excel_file.sheet_names}")
        
        # 分析每個工作表
        for sheet_name in excel_file.sheet_names[:3]:  # 只看前3個工作表
            print(f"\n  工作表: {sheet_name}")
            df = pd.read_excel(file, sheet_name=sheet_name)
            print(f"  行數: {len(df)}")
            print(f"  列數: {len(df.columns)}")
            print(f"  欄位名稱: {list(df.columns)[:10]}")  # 只顯示前10個欄位
            print(f"\n  前3行資料:")
            print(df.head(3).to_string())
            
    except Exception as e:
        print(f"錯誤: {e}")

print("\n" + "=" * 80)
