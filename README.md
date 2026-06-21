# Supplier BOM 虛擬知識圖譜 (VKG) 系統

## 📊 專案概述

本專案將 6 個 Excel BOM 表格轉換為虛擬知識圖譜 (Virtual Knowledge Graph)，並使用 Ontop 提供 SPARQL 查詢介面，讓 LLM 可以透過自然語言檢索產品與物料資訊。

---

## 🗂️ 原始資料

### 6 個 Excel 檔案 (BOM 表格)
```
1. DDB-1845, cánh nhôm, dây đồng và dây nhôm 100V-50-60Hz.xls
2. DDB-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls
3. DSE-1845, cánh nhôm, dây đồng và dây nhôm 100V-50-60Hz.xls
4. DSE-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls
5. KMH-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls
6. KWJ-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls
```

### Excel 結構
- **前 6 行**: 產品元資料 (電壓、客戶、產品代碼、顏色、日期、備註)
- **第 7 行**: BOM 表頭 (STT, MÃ NVL, Lượng dùng, Đơn Vị, Thuộc Tính, 等)
- **第 8 行起**: BOM 項目資料 (物料代碼、數量、單位、規格)

---

## 🔄 資料處理流程

### 步驟 1: Excel → SQLite 資料庫

**腳本**: `excel_to_db.py`

#### 建立 3 個關聯式資料表：

**1. `products` 表 (產品主檔)**
```sql
- product_id (主鍵)
- product_code (產品代碼: DDB-1845, DSE-1845, 等)
- dasin_code_copper (銅線版本代碼)
- dasin_code_aluminum (鋁線版本代碼)
- voltage (電壓: 100V/50-60Hz)
- customer (客戶名稱)
- color (顏色)
- date_created (建立日期)
- notes (備註)
- source_file (來源檔案名稱)
```

**2. `bom_items` 表 (BOM 項目)**
```sql
- item_id (主鍵)
- product_id (外鍵 → products)
- stt (序號)
- material_code (物料代碼: P-092-13, O-001-1, 等)
- quantity (用量)
- base_number (基數)
- unit (單位: pcs, kg, 等)
- attribute (屬性: M:自製, P:採購)
- product_name (物料名稱)
- specification (規格說明)
```

**3. `materials` 表 (物料主檔)**
```sql
- material_id (主鍵)
- material_code (物料代碼, 唯一)
- product_name (物料名稱)
- unit (單位)
- attribute (屬性類型)
```

#### 資料統計：
- ✅ **6 個產品**
- ✅ **962 個 BOM 項目**
- ✅ **223 種不重複物料**

**輸出**: `supplier_bom.db` (SQLite 資料庫)

---

## 🧠 步驟 2: 設計 OWL 本體 (Ontology)

**檔案**: `supplier_bom_ontology.ttl`

### 本體結構

#### 類別 (Classes)
```turtle
:Product        # 產品
:BOMItem        # BOM 項目
:Material       # 物料
:Manufacturer   # 製造商
:Attribute      # 屬性 (自製/採購)
  ├─ :SelfMade  # 自製 (M:自製)
  └─ :Purchased # 採購 (P:採購)
```

#### 物件屬性 (Object Properties)
```turtle
:hasBOMItem      # Product → BOMItem
:usesMaterial    # BOMItem → Material
:hasManufacturer # Product → Manufacturer
:hasAttribute    # Material → Attribute
```

#### 資料屬性 (Datatype Properties)
```turtle
產品屬性:
  :productCode, :voltage, :customer, :color
  :dasinCodeCopper, :dasinCodeAluminum
  :dateCreated, :notes

物料屬性:
  :materialCode, :materialName, :unit, :specification

BOM 屬性:
  :sequenceNumber, :quantity, :baseNumber, :attributeType
```

---

## 🔗 步驟 3: OBDA 映射 (資料庫 → 本體)

**檔案**: `supplier_bom.obda`

### 5 個映射規則：

1. **Product 映射**: 將 products 表映射到 :Product 類別
2. **Material 映射**: 將 materials 表映射到 :Material 類別
3. **BOMItem 映射**: 將 bom_items 表映射到 :BOMItem 類別
4. **Product-BOM 關係**: 建立 :hasBOMItem 關係
5. **BOM-Material 關係**: 建立 :usesMaterial 關係

### 映射範例：
```obda
mappingId	Product
target		:product/{product_id} a :Product ; 
            :productCode {product_code}^^xsd:string ; 
            :voltage {voltage}^^xsd:string .
source		SELECT product_id, product_code, voltage FROM products
```

---

## ⚙️ 步驟 4: Ontop 配置

### 配置檔案：

**1. `supplier_bom.properties`** - JDBC 連接設定
```properties
jdbc.url=jdbc:sqlite:supplier_bom.db
jdbc.driver=org.sqlite.JDBC
```

**2. `docker-compose.yml`** - Docker 容器配置
```yaml
services:
  ontop:
    image: ontop/ontop-endpoint:latest
    ports:
      - "8080:8080"
    volumes:
      - 掛載 .db, .ttl, .obda, .properties 檔案
```

**3. `supplier_bom.portal.toml`** - Web UI 預設查詢範例

---

## 🤖 步驟 5: LLM 檢索整合

**檔案**: `llm_sparql_query.py`

### LLM 查詢流程：

```
用戶自然語言查詢
    ↓
LLM 理解意圖 (使用 prompt template)
    ↓
生成 SPARQL 查詢
    ↓
向 Ontop SPARQL endpoint 發送查詢
    ↓
Ontop 將 SPARQL 轉換為 SQL
    ↓
查詢 SQLite 資料庫
    ↓
結果返回給 LLM
    ↓
LLM 以自然語言回答用戶
```

### 9 個 SPARQL 查詢範例：

1. ✅ 列出所有產品
2. ✅ 查詢特定產品的完整 BOM
3. ✅ 物料共用分析 (哪些物料被多個產品使用)
4. ✅ 自製 vs 採購統計
5. ✅ 查詢特定物料的使用情況
6. ✅ 產品複雜度分析 (按零件數量排序)
7. ✅ 關鍵字搜尋物料
8. ✅ 產品版本比較 (銅線 vs 鋁線)
9. ✅ 物料使用頻率排名

### 生成的 LLM 輔助檔案：

- **`llm_query_examples.json`**: Few-shot learning 範例
- **`llm_prompt_template.txt`**: Prompt 模板 (含本體結構說明)

---

## 🚀 使用方式

### 1. 啟動 Ontop 服務
```bash
docker-compose up -d
```

### 2. 訪問 Web 介面
```
http://localhost:8080
```

### 3. 使用 Python 查詢
```python
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://localhost:8080/sparql")
sparql.setQuery("""
    PREFIX : <http://example.org/supplier_bom#>
    SELECT ?productCode ?voltage
    WHERE {
        ?product a :Product ;
                 :productCode ?productCode ;
                 :voltage ?voltage .
    }
""")
results = sparql.query().convert()
```

### 4. LLM 自然語言查詢範例

**用戶問**: "DDB-1845 產品需要哪些物料?"

**LLM 生成 SPARQL**:
```sparql
PREFIX : <http://example.org/supplier_bom#>
SELECT ?materialCode ?materialName ?quantity ?unit
WHERE {
  ?product a :Product ;
           :productCode "DDB-1845" ;
           :hasBOMItem ?bomItem .
  ?bomItem :usesMaterial ?material ;
           :quantity ?quantity ;
           :unit ?unit .
  ?material :materialCode ?materialCode ;
            :materialName ?materialName .
}
```

**LLM 回答**: "DDB-1845 產品需要 157 種物料，包括 P-092-13 (Mặt nạ 網子商標環)、O-001-1 (Hạt nhựa 塑膠粒 ABS 707) 等..."

---

## 📁 專案檔案結構

```
suppiler_onto/
├── 📊 原始資料
│   ├── DDB-1845, cánh nhôm, dây đồng và dây nhôm 100V-50-60Hz.xls
│   ├── DDB-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls
│   ├── DSE-1845, cánh nhôm, dây đồng và dây nhôm 100V-50-60Hz.xls
│   ├── DSE-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls
│   ├── KMH-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls
│   └── KWJ-1845, cánh nhựa, dây đồng và dây nhôm 100V-50-60Hz.xls
│
├── 🗄️ 資料庫
│   └── supplier_bom.db (SQLite)
│
├── 🧠 本體 & 映射
│   ├── supplier_bom_ontology.ttl (OWL 本體)
│   ├── supplier_bom.obda (OBDA 映射)
│   ├── supplier_bom.properties (JDBC 配置)
│   └── supplier_bom.portal.toml (Web UI 配置)
│
├── 🐳 部署
│   └── docker-compose.yml
│
├── 🐍 Python 腳本
│   ├── excel_to_db.py (資料轉換)
│   ├── analyze_full_structure.py (資料分析)
│   └── llm_sparql_query.py (LLM 查詢介面)
│
└── 📖 說明文件
    └── README.md (本檔案)
```

---

## 🎯 核心優勢

### 1. **虛擬化 (Virtualization)**
- ❌ 不需要將關聯式資料複製到圖資料庫
- ✅ 保持原始 SQLite 資料庫不變
- ✅ Ontop 即時將 SPARQL 轉換為 SQL

### 2. **語義化 (Semantic)**
- ✅ 使用標準 OWL 本體描述領域知識
- ✅ 支援推理和語義查詢
- ✅ 易於與其他本體整合

### 3. **LLM 友善**
- ✅ 提供自然語言到 SPARQL 的轉換範例
- ✅ 結構化的 prompt template
- ✅ 支援 RAG (Retrieval Augmented Generation)

### 4. **標準化**
- ✅ 使用 W3C 標準 (OWL, SPARQL, R2RML)
- ✅ 可與任何支援 SPARQL 的工具整合
- ✅ 跨平台、跨語言支援

---

## 💡 進階應用

### 1. RAG (檢索增強生成)
將本體和查詢範例加入向量資料庫，讓 LLM 更準確地生成 SPARQL

### 2. Agent 系統
讓 LLM Agent 自動規劃和執行多步驟查詢任務

### 3. Fine-tuning
使用領域特定的查詢範例訓練專門的 Text-to-SPARQL 模型

### 4. 多資料源整合
擴展本體以整合 ERP、PLM 等其他資料源

---

## 📊 資料處理摘要

| 項目 | 來源格式 | 目標格式 | 數量 |
|------|---------|---------|------|
| 產品檔案 | 6 個 Excel | SQLite 表 | 6 產品 |
| BOM 項目 | Excel 行 | SQLite 記錄 | 962 項 |
| 物料種類 | Excel 資料 | SQLite 去重 | 223 種 |
| 語義類別 | - | OWL 類別 | 6 類 |
| 屬性定義 | - | OWL 屬性 | 20+ 個 |
| 映射規則 | - | OBDA 映射 | 5 個 |
| 查詢範例 | - | SPARQL | 9+ 個 |

---

## 🔧 技術堆疊

- **資料庫**: SQLite 3
- **本體語言**: OWL 2 (Turtle 格式)
- **查詢語言**: SPARQL 1.1
- **VKG 引擎**: Ontop
- **容器化**: Docker & Docker Compose
- **程式語言**: Python 3.11
- **Python 套件**: pandas, sqlite3, SPARQLWrapper (可選)

---

## ✅ 完成狀態

- [x] Excel 資料分析與結構理解
- [x] SQLite 資料庫設計與資料轉換
- [x] OWL 本體設計 (類別、屬性、關係)
- [x] OBDA 映射規則建立
- [x] Ontop 服務配置 (Docker)
- [x] SPARQL 查詢範例撰寫
- [x] LLM 整合範例 (prompt template, few-shot examples)
- [x] 完整文件撰寫

---

## 📝 下一步建議

1. **啟動測試**: 執行 `docker-compose up -d` 並測試查詢
2. **LLM 整合**: 將 prompt template 整合到您的 LLM 應用
3. **擴展本體**: 根據業務需求添加更多語義關係
4. **效能優化**: 為高頻查詢建立資料庫索引
5. **權限控制**: 添加使用者認證和查詢權限管理

---

**建立日期**: 2026-06-21  
**作者**: GitHub Copilot  
**版本**: 1.0.0
