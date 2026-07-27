# RAG評価レポート

- 評価モード: `all`

## Retrieval評価

- 評価ケース数: 8

### ケース別結果

| ID | 正解文書 | 検索結果 | 正解順位 |
|---|---|---|---:|
| exact_form_number | doc_2 | doc_2, doc_1, doc_3 | 1位 |
| pc_procedure | doc_2 | doc_2 | 1位 |
| confidential_information | doc_1 | なし | 見つからない |
| travel_expense | doc_3 | なし | 見つからない |
| travel_form_number | doc_3 | doc_3, doc_1, doc_2 | 1位 |
| unknown_deadline | 該当文書なし | なし | 見つからない |
| unknown_book | 該当文書なし | なし | 見つからない |
| security_team | doc_2 | doc_2 | 1位 |

### 指標

- Hit@1: 4/6 (66.67%)
- Hit@3: 4/6 (66.67%)
- MRR: 0.6667
- 未回答正解率: 100.00%

---

## Generation評価

- 評価ケース数: 8

### ケース別結果

| ID | 生成回答 | Grounded | Relevance | 正解 |
|---|---|:---:|---:|:---:|
| exact_form_number | 様式第4号の提出先は、セキュリティチームです。 | True | 1.00 | True |
| pc_procedure | 社外PCを外に持ち出すときの手続きは、社外PC持出許可申請書（様式第4号）をセキュリティチームに提出することです。 | True | 1.00 | True |
| confidential_information | 参考情報に記載されていません。 | False | 1.00 | False |
| travel_expense | 参考情報に記載されていません。 | False | 1.00 | False |
| travel_form_number | 様式第9号の提出先は、総務部経費精算係です。 | True | 1.00 | True |
| unknown_deadline | 参考情報に記載されていません。 | False | 1.00 | True |
| unknown_book | 参考情報に記載されていません。 | False | 1.00 | True |
| security_team | 社外PC持出許可申請書の提出先は、セキュリティチームです。 | True | 1.00 | True |

### 指標

- Grounded率: 4/8 (50.00%)
- 正解率: 6/8 (75.00%)
- 平均Relevance: 1.00
