import pandas as pd
import json

files = [
    "DDB-1845, cánh nhôm, dây đồng và dây nhôm 100V-50-60Hz.xls",
    "DDB-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls",
    "DSE-1845, cánh nhôm, dây đồng và dây nhôm 100V-50-60Hz.xls",
    "DSE-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls",
    "KMH-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls",
    "KWJ-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls"
]

print("=" * 100)
print("完整資料結構分析")
print("=" * 100)

for file in files[:1]:
    print(f"\n檔案: {file}")
    df = pd.read_excel(file, sheet_name='Sheet', header=None)
    
    print(f"\n總行數: {len(df)}, 總列數: {len(df.columns)}")
    print("\n" + "=" * 100)
    print("前 20 行資料:")
    print("=" * 100)
    
    for i in range(min(20, len(df))):
        row_data = df.iloc[i].tolist()
        # 過濾掉 NaN
        row_data_clean = [str(x) if pd.notna(x) else '' for x in row_data]
        print(f"Row {i}: {row_data_clean}")
    
    print("\n" + "=" * 100)
    print("尋找 BOM 項目的開始位置...")
    print("=" * 100)
    
    for i in range(len(df)):
        row = df.iloc[i]
        row_str = ' '.join([str(x) for x in row if pd.notna(x)])
        if 'STT' in row_str or 'Tên linh kiện' in row_str or '項次' in row_str:
            print(f"\n可能的表頭在第 {i} 行:")
            print(f"  {row.tolist()}")
            
            # 顯示接下來的 10 行
            print(f"\n接下來的 10 行資料:")
            for j in range(i+1, min(i+11, len(df))):
                print(f"  Row {j}: {df.iloc[j].tolist()}")
            break

print("\n" + "=" * 100)
print("分析所有檔案的產品資訊")
print("=" * 100)

products_info = []
for file in files:
    df = pd.read_excel(file, sheet_name='Sheet', header=None)
    
    product_info = {
        'filename': file,
        'voltage': None,
        'customer': None,
        'product_code_customer': None,
        'product_code_dasin': [],
        'color': None
    }
    
    # 提取產品資訊
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        row_str = ' '.join([str(x) for x in row if pd.notna(x)])
        
        if 'ĐIỆN ÁP' in row_str or 'voltage' in row_str.lower():
            for val in row:
                if pd.notna(val) and 'V' in str(val) and 'Hz' in str(val):
                    product_info['voltage'] = str(val)
                    
        if 'KHÁCH HÀNG' in row_str or 'customer' in row_str.lower():
            for val in row:
                if pd.notna(val) and val not in ['KHÁCH HÀNG:', 'NaN']:
                    if 'KHÁCH HÀNG' not in str(val):
                        product_info['customer'] = str(val)
                        
        if 'MÃ SẢN PHẨM KHÁCH HÀNG' in row_str:
            for val in row:
                if pd.notna(val) and 'DDB' in str(val) or 'DSE' in str(val) or 'KMH' in str(val) or 'KWJ' in str(val):
                    if 'MÃ SẢN PHẨM' not in str(val):
                        product_info['product_code_customer'] = str(val)
                        
        if 'MÃ SẢN PHẨM DASIN' in row_str:
            for val in row:
                if pd.notna(val) and ('dây đồng' in str(val) or 'dây nhôm' in str(val) or 'Motor' in str(val)):
                    product_info['product_code_dasin'].append(str(val))
                    
        if 'MÀU SẮC' in row_str:
            for val in row:
                if pd.notna(val) and 'Màu' in str(val):
                    product_info['color'] = str(val)
    
    products_info.append(product_info)

print("\n提取的產品資訊:")
for info in products_info:
    print(f"\n檔案: {info['filename']}")
    print(f"  電壓: {info['voltage']}")
    print(f"  客戶: {info['customer']}")
    print(f"  客戶產品代碼: {info['product_code_customer']}")
    print(f"  DASIN 產品代碼: {info['product_code_dasin']}")
    print(f"  顏色: {info['color']}")
