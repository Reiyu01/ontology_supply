"""
使用 SPARQL 查詢 Ontop VKG 並提供 LLM 檢索範例
"""
import json

# Ontop SPARQL endpoint
SPARQL_ENDPOINT = "http://localhost:8080/sparql"

# SPARQLWrapper 是可選的,只在需要實際查詢時使用
try:
    from SPARQLWrapper import SPARQLWrapper, JSON as SPARQL_JSON
    SPARQL_AVAILABLE = True
except ImportError:
    SPARQL_AVAILABLE = False
    print("注意: SPARQLWrapper 未安裝,將只生成範例檔案")
    print("如需實際查詢功能,請執行: pip install SPARQLWrapper\n")

def query_sparql(query):
    """執行 SPARQL 查詢"""
    if not SPARQL_AVAILABLE:
        print("SPARQLWrapper 未安裝,無法執行查詢")
        return None
        
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(SPARQL_JSON)
    
    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        print(f"查詢錯誤: {e}")
        return None

def format_results(results):
    """格式化查詢結果"""
    if not results or 'results' not in results:
        return []
    
    bindings = results['results']['bindings']
    formatted = []
    
    for binding in bindings:
        row = {}
        for var, value in binding.items():
            row[var] = value['value']
        formatted.append(row)
    
    return formatted

# ===== LLM 檢索範例查詢 =====

# 1. 基礎查詢 - 列出所有產品
query_all_products = """
PREFIX : <http://example.org/supplier_bom#>
SELECT ?productCode ?voltage ?customer ?color
WHERE {
  ?product a :Product ;
           :productCode ?productCode ;
           :voltage ?voltage ;
           :customer ?customer ;
           :color ?color .
}
"""

# 2. 產品的完整 BOM 查詢
query_product_bom = """
PREFIX : <http://example.org/supplier_bom#>
SELECT ?materialCode ?materialName ?quantity ?unit ?specification
WHERE {
  ?product a :Product ;
           :productCode "DDB-1845" ;
           :hasBOMItem ?bomItem .
  ?bomItem :usesMaterial ?material ;
           :quantity ?quantity ;
           :unit ?unit .
  OPTIONAL { ?bomItem :specification ?specification . }
  ?material :materialCode ?materialCode ;
            :materialName ?materialName .
}
ORDER BY ?materialCode
"""

# 3. 物料共用分析 - 找出被多個產品使用的物料
query_shared_materials = """
PREFIX : <http://example.org/supplier_bom#>
SELECT ?materialCode ?materialName (COUNT(DISTINCT ?product) AS ?usedInProducts)
WHERE {
  ?product :hasBOMItem ?bomItem .
  ?bomItem :usesMaterial ?material .
  ?material :materialCode ?materialCode ;
            :materialName ?materialName .
}
GROUP BY ?materialCode ?materialName
HAVING (COUNT(DISTINCT ?product) > 1)
ORDER BY DESC(?usedInProducts)
"""

# 4. 自製 vs 採購物料統計
query_make_vs_buy = """
PREFIX : <http://example.org/supplier_bom#>
SELECT ?attributeType (COUNT(?material) AS ?count)
WHERE {
  ?material a :Material ;
            :attributeType ?attributeType .
}
GROUP BY ?attributeType
"""

# 5. 特定物料被哪些產品使用
query_material_usage = """
PREFIX : <http://example.org/supplier_bom#>
SELECT DISTINCT ?productCode ?quantity ?unit
WHERE {
  ?product a :Product ;
           :productCode ?productCode ;
           :hasBOMItem ?bomItem .
  ?bomItem :usesMaterial ?material ;
           :quantity ?quantity ;
           :unit ?unit .
  ?material :materialCode "P-092-13" .
}
"""

# 6. 產品成本分析 - 按產品統計物料項目數量
query_product_complexity = """
PREFIX : <http://example.org/supplier_bom#>
SELECT ?productCode (COUNT(?bomItem) AS ?componentCount)
WHERE {
  ?product a :Product ;
           :productCode ?productCode ;
           :hasBOMItem ?bomItem .
}
GROUP BY ?productCode
ORDER BY DESC(?componentCount)
"""

# 7. 尋找包含特定關鍵字的物料
query_material_by_keyword = """
PREFIX : <http://example.org/supplier_bom#>
SELECT ?materialCode ?materialName ?unit
WHERE {
  ?material a :Material ;
            :materialCode ?materialCode ;
            :materialName ?materialName ;
            :unit ?unit .
  FILTER(CONTAINS(LCASE(?materialName), "motor") || CONTAINS(LCASE(?materialName), "quạt"))
}
"""

# 8. 產品版本比較 - 銅線 vs 鋁線版本
query_copper_vs_aluminum = """
PREFIX : <http://example.org/supplier_bom#>
SELECT ?productCode ?dasinCodeCopper ?dasinCodeAluminum
WHERE {
  ?product a :Product ;
           :productCode ?productCode ;
           :dasinCodeCopper ?dasinCodeCopper ;
           :dasinCodeAluminum ?dasinCodeAluminum .
}
"""

# ===== LLM 自然語言到 SPARQL 的範例對應 =====

NL_TO_SPARQL_EXAMPLES = {
    "列出所有產品": query_all_products,
    "顯示所有產品型號": query_all_products,
    "DDB-1845 的物料清單是什麼": query_product_bom,
    "哪些物料被多個產品共用": query_shared_materials,
    "多少物料是自製的,多少是採購的": query_make_vs_buy,
    "哪些產品使用了 P-092-13 這個物料": query_material_usage,
    "哪個產品最複雜(最多零件)": query_product_complexity,
    "找出所有的電機相關物料": query_material_by_keyword,
    "產品有哪些版本差異": query_copper_vs_aluminum,
}

def llm_query_interface(natural_language_query):
    """
    LLM 查詢介面 - 將自然語言轉換為 SPARQL 查詢
    
    在實際應用中,這裡會使用 LLM 來生成 SPARQL,
    這裡只是演示概念
    """
    print(f"\n自然語言查詢: {natural_language_query}")
    
    # 簡單的關鍵字匹配(實際應該用 LLM)
    for nl, sparql in NL_TO_SPARQL_EXAMPLES.items():
        if any(keyword in natural_language_query for keyword in nl.split()):
            print(f"匹配到範例: {nl}")
            print(f"\nSPARQL 查詢:\n{sparql}\n")
            return sparql
    
    return None

def save_queries_for_llm():
    """
    儲存查詢範例供 LLM 學習
    這些範例可以用於:
    1. Few-shot learning
    2. RAG (Retrieval Augmented Generation)
    3. Fine-tuning LLM
    """
    examples = []
    
    for nl_query, sparql_query in NL_TO_SPARQL_EXAMPLES.items():
        examples.append({
            "natural_language": nl_query,
            "sparql": sparql_query,
            "domain": "supplier_bom",
            "complexity": "medium"
        })
    
    with open('llm_query_examples.json', 'w', encoding='utf-8') as f:
        json.dump(examples, indent=2, ensure_ascii=False, fp=f)
    
    print("已儲存 LLM 查詢範例到 llm_query_examples.json")

def generate_llm_prompt_template():
    """生成 LLM prompt 模板"""
    template = """
你是一個專門將自然語言轉換為 SPARQL 查詢的 AI 助手。

## 知識圖譜結構

### 類別 (Classes):
- :Product - 產品
- :Material - 物料
- :BOMItem - BOM 項目

### 屬性 (Properties):
產品屬性:
- :productCode - 產品代碼
- :voltage - 電壓
- :customer - 客戶
- :color - 顏色
- :dasinCodeCopper - DASIN 銅線代碼
- :dasinCodeAluminum - DASIN 鋁線代碼

物料屬性:
- :materialCode - 物料代碼
- :materialName - 物料名稱
- :unit - 單位
- :attributeType - 屬性類型 (M:自製 或 P:採購)

BOM 屬性:
- :sequenceNumber - 序號
- :quantity - 數量
- :specification - 規格

關係:
- :hasBOMItem - 產品包含 BOM 項目
- :usesMaterial - BOM 項目使用物料

### 範例查詢:

{examples}

## 任務
將以下自然語言查詢轉換為 SPARQL:

用戶查詢: {user_query}

請生成對應的 SPARQL 查詢:
"""
    
    examples_text = ""
    for i, (nl, sparql) in enumerate(list(NL_TO_SPARQL_EXAMPLES.items())[:3], 1):
        examples_text += f"\n{i}. 自然語言: {nl}\n   SPARQL:\n{sparql}\n"
    
    return template.format(examples=examples_text, user_query="{user_query}")

def main():
    print("=" * 80)
    print("Ontop VKG + LLM 檢索範例")
    print("=" * 80)
    
    # 儲存 LLM 訓練範例
    save_queries_for_llm()
    
    # 生成 LLM prompt 模板
    prompt_template = generate_llm_prompt_template()
    with open('llm_prompt_template.txt', 'w', encoding='utf-8') as f:
        f.write(prompt_template)
    print("已儲存 LLM prompt 模板到 llm_prompt_template.txt")
    
    print("\n" + "=" * 80)
    print("自然語言查詢範例:")
    print("=" * 80)
    
    # 演示 LLM 查詢介面
    test_queries = [
        "列出所有產品",
        "哪些物料被多個產品共用",
        "產品有哪些版本差異"
    ]
    
    for test_query in test_queries:
        sparql = llm_query_interface(test_query)
        if sparql:
            print(f"✓ 成功生成 SPARQL 查詢\n")
    
    print("\n" + "=" * 80)
    print("使用說明:")
    print("=" * 80)
    print("""
1. 啟動 Ontop 服務:
   docker-compose up -d

2. 訪問 Web 介面:
   http://localhost:8080

3. 使用 Python 查詢 (需要先安裝 SPARQLWrapper):
   pip install SPARQLWrapper
   
4. 在 LLM 中使用:
   - 提供 llm_query_examples.json 作為 few-shot examples
   - 使用 llm_prompt_template.txt 作為 prompt 模板
   - LLM 會將自然語言轉換為 SPARQL 查詢
   - 執行查詢並返回結果給用戶

5. 進階用法:
   - RAG: 將本體結構和範例查詢加入向量資料庫
   - Agent: 讓 LLM 自動規劃和執行複雜的多步驟查詢
   - Fine-tuning: 使用領域特定的查詢範例訓練專門的模型
    """)
    
    print("\n完成!")

if __name__ == '__main__':
    main()
