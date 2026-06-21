"""
將 Excel BOM 表轉換為關聯式資料庫
"""
import pandas as pd
import sqlite3
import re
from datetime import datetime

def extract_product_info(df):
    """從前幾行提取產品資訊"""
    info = {
        'voltage': None,
        'customer': None,
        'product_code': None,
        'dasin_code_copper': None,
        'dasin_code_aluminum': None,
        'color': None,
        'date': None,
        'notes': None
    }
    
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        
        # 電壓
        if pd.notna(row[0]) and 'ĐIỆN ÁP' in str(row[0]):
            if pd.notna(row[2]):
                info['voltage'] = str(row[2])
        
        # 客戶
        if pd.notna(row[0]) and 'KHÁCH HÀNG' in str(row[0]):
            if pd.notna(row[2]):
                info['customer'] = str(row[2])
        
        # 客戶產品代碼
        if pd.notna(row[6]) and 'MÃ SẢN PHẨM KHÁCH HÀNG' in str(row[6]):
            if pd.notna(row[7]):
                info['product_code'] = str(row[7])
        
        # DASIN 產品代碼
        if pd.notna(row[6]) and 'MÃ SẢN PHẨM DASIN' in str(row[6]):
            if pd.notna(row[7]):
                code = str(row[7])
                if 'dây đồng' in code.lower():
                    info['dasin_code_copper'] = code
                elif 'dây nhôm' in code.lower() and pd.notna(row[8]):
                    info['dasin_code_aluminum'] = str(row[8])
        
        # 顏色
        if pd.notna(row[6]) and 'MÀU SẮC' in str(row[6]):
            if pd.notna(row[7]):
                info['color'] = str(row[7])
        
        # 日期
        if pd.notna(row[0]) and 'NGÀY LẬP' in str(row[0]):
            if pd.notna(row[2]):
                info['date'] = str(row[2])
        
        # 備註
        if pd.notna(row[0]) and 'Ghi Chú' in str(row[0]):
            if pd.notna(row[2]):
                info['notes'] = str(row[2])
    
    return info

def extract_bom_items(df, product_id, start_row=7):
    """提取 BOM 項目"""
    items = []
    
    for i in range(start_row, len(df)):
        row = df.iloc[i]
        
        # 檢查是否為有效的 BOM 行
        if pd.notna(row[1]):  # MÃ NVL 不為空
            item = {
                'product_id': product_id,
                'stt': row[0] if pd.notna(row[0]) else None,
                'material_code': str(row[1]) if pd.notna(row[1]) else None,
                'quantity': float(row[2]) if pd.notna(row[2]) else None,
                'base_number': float(row[3]) if pd.notna(row[3]) else None,
                'unit': str(row[4]) if pd.notna(row[4]) else None,
                'attribute': str(row[5]) if pd.notna(row[5]) else None,
                'product_name': str(row[6]) if pd.notna(row[6]) else None,
                'specification': str(row[7]) if pd.notna(row[7]) else None,
            }
            items.append(item)
    
    return items

def create_database(db_path='supplier_bom.db'):
    """創建資料庫結構"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 產品表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT NOT NULL,
        dasin_code_copper TEXT,
        dasin_code_aluminum TEXT,
        voltage TEXT,
        customer TEXT,
        color TEXT,
        date_created TEXT,
        notes TEXT,
        source_file TEXT,
        UNIQUE(product_code, dasin_code_copper, dasin_code_aluminum)
    )
    ''')
    
    # BOM 項目表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bom_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        stt INTEGER,
        material_code TEXT NOT NULL,
        quantity REAL,
        base_number REAL,
        unit TEXT,
        attribute TEXT,
        product_name TEXT,
        specification TEXT,
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    ''')
    
    # 物料主檔表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS materials (
        material_id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_code TEXT UNIQUE NOT NULL,
        product_name TEXT,
        unit TEXT,
        attribute TEXT
    )
    ''')
    
    conn.commit()
    return conn

def process_excel_files(files, conn):
    """處理所有 Excel 檔案"""
    cursor = conn.cursor()
    
    for file_path in files:
        print(f"\n處理檔案: {file_path}")
        
        # 讀取 Excel
        df = pd.read_excel(file_path, sheet_name='Sheet', header=None)
        
        # 提取產品資訊
        product_info = extract_product_info(df)
        
        # 插入產品資料
        try:
            cursor.execute('''
            INSERT INTO products (product_code, dasin_code_copper, dasin_code_aluminum, 
                                 voltage, customer, color, date_created, notes, source_file)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_info['product_code'],
                product_info['dasin_code_copper'],
                product_info['dasin_code_aluminum'],
                product_info['voltage'],
                product_info['customer'],
                product_info['color'],
                product_info['date'],
                product_info['notes'],
                file_path
            ))
            product_id = cursor.lastrowid
            print(f"  產品 ID: {product_id}")
        except sqlite3.IntegrityError:
            # 如果產品已存在,獲取其 ID
            cursor.execute('''
            SELECT product_id FROM products 
            WHERE product_code = ? AND dasin_code_copper = ? AND dasin_code_aluminum = ?
            ''', (product_info['product_code'], product_info['dasin_code_copper'], 
                  product_info['dasin_code_aluminum']))
            product_id = cursor.fetchone()[0]
            print(f"  產品已存在,ID: {product_id}")
        
        # 提取 BOM 項目
        bom_items = extract_bom_items(df, product_id)
        print(f"  BOM 項目數量: {len(bom_items)}")
        
        # 插入 BOM 項目
        for item in bom_items:
            cursor.execute('''
            INSERT INTO bom_items (product_id, stt, material_code, quantity, base_number,
                                  unit, attribute, product_name, specification)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['product_id'],
                item['stt'],
                item['material_code'],
                item['quantity'],
                item['base_number'],
                item['unit'],
                item['attribute'],
                item['product_name'],
                item['specification']
            ))
            
            # 更新物料主檔
            cursor.execute('''
            INSERT OR REPLACE INTO materials (material_code, product_name, unit, attribute)
            VALUES (?, ?, ?, ?)
            ''', (
                item['material_code'],
                item['product_name'],
                item['unit'],
                item['attribute']
            ))
        
        conn.commit()
        print(f"  完成!")

def main():
    files = [
        "DDB-1845, cánh nhôm, dây đồng và dây nhôm 100V-50-60Hz.xls",
        "DDB-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls",
        "DSE-1845, cánh nhôm, dây đồng và dây nhôm 100V-50-60Hz.xls",
        "DSE-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls",
        "KMH-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls",
        "KWJ-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls"
    ]
    
    print("=" * 80)
    print("建立 SQLite 資料庫並匯入資料")
    print("=" * 80)
    
    # 建立資料庫
    conn = create_database('supplier_bom.db')
    
    # 處理檔案
    process_excel_files(files, conn)
    
    # 顯示統計資訊
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM products')
    product_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM bom_items')
    bom_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM materials')
    material_count = cursor.fetchone()[0]
    
    print("\n" + "=" * 80)
    print("資料庫統計:")
    print(f"  產品數量: {product_count}")
    print(f"  BOM 項目數量: {bom_count}")
    print(f"  物料種類: {material_count}")
    print("=" * 80)
    
    # 顯示範例資料
    print("\n範例產品資料:")
    cursor.execute('SELECT product_id, product_code, voltage, customer FROM products LIMIT 3')
    for row in cursor.fetchall():
        print(f"  {row}")
    
    print("\n範例 BOM 項目:")
    cursor.execute('''
    SELECT b.item_id, p.product_code, b.material_code, b.quantity, b.unit, b.product_name
    FROM bom_items b
    JOIN products p ON b.product_id = p.product_id
    LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f"  {row}")
    
    conn.close()
    print("\n資料庫已創建: supplier_bom.db")

if __name__ == '__main__':
    main()
