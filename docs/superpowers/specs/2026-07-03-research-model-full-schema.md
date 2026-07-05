# research-model.json 完整结构

> **Deprecated.** 参见 `references/research-model-schema.md` (2026-07-04)。本文档保留仅作历史参考。

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-07-03T12:00:00Z",

  // ═══ 公司识别 ═══
  "identity": {
    "name": "Howmet Aerospace",
    "ticker": "HWM.US",
    "market": "us",
    "currency": "USD",
    "accounting_standard": "us_gaap",
    "cik": 4281,
    "sic": "3350",
    "fiscal_year_end": "1231",
    "filer_category": "Large accelerated filer",
    "employees": 24100
  },

  // ═══ 模型配置 ═══
  "meta": {
    "p&l_depth": "ebitda",
    "basis": "non-gaap",
    "base_fy": 2025,
    "proj_years": 5,
    "sotp_offset": 2,
    "q_actual_count": 4,
    "q_proj_count": 4,
    "q_start_yr": 2025,
    "q_start_q": 1,
    "price": 270.41,
    "shares_m": 400.1,
    "mcap_m": 108193,
    "net_debt": 2471
  },

  // ═══ 历史披露（GAAP + non-GAAP）════
  "actuals": {
    "FY2023": {
      "annual": {
        "gaap": {
          "is": {
            "rev": 6640, "cogs": 4773, "gp": 1867,
            "sga": 333, "rnd": 36,
            "oi": 1203,
            "interest_expense": -218,
            "pretax": 975, "tax": 210,
            "ni": 765, "ni_attr_parent": 763,
            "eps_diluted": 1.83,
            "da": 272,
            "other_items": {}
          },
          "bs": {
            "cash": 610, "total_debt": 3835, "total_equity": 4037,
            "total_assets": 10428, ...
          },
          "cf": {
            "da": 272, "op_cf": null, "capex": null, ...
          },
          "segments": [
            { "type": "operating", "name": "Engine Products", "rev": 3266 },
            { "type": "operating", "name": "Fastening Systems", "rev": 1349 },
            { "type": "operating", "name": "Engineered Structures", "rev": 878 },
            { "type": "operating", "name": "Forged Wheels", "rev": 1147 }
          ],
          "segments._source": {
            "Engine Products.rev": "sec_10k"
          }
        },
        "non_gaap": {
          "is": {
            "ebitda": 1750, "op": 1480, "ni": 960
          },
          "adj": {
            "sbc": 50, "restructuring": 15, "fx": 2, "other": 13
          },
          "segments": [
            { "type": "operating", "name": "Engine Products", "ebitda": 947, "margin": 0.29 }
          ],
          "reconciliation": {
            "ebitda": {
              "gaap_ebitda": 1475, "total_adjustments": 80,
              "expected_non_gaap": 1750, "actual_non_gaap": 1750,
              "diff": 0, "covered": true
            }
          }
        }
      },
      "Q1": {
        "gaap": {
          "is": { "rev": null, "gp": null, "oi": null, "ni": null, "tax": null },
          "segments": []
        },
        "non_gaap": {
          "is": { "ebitda": null },
          "segments": []
        }
      },
      "Q2": {}, "Q3": {}, "Q4": {}
    },

    "FY2024": {
      "annual": {
        "gaap": {
          "is": { "rev": 7430, "gp": 2311, "oi": 1633, "ni": 1155, "tax": 228, "da": 277, ... },
          "segments": [
            { "type": "operating", "name": "Engine Products", "rev": 3735 }
          ]
        },
        "non_gaap": {
          "is": { "ebitda": 1880, "op": 1633, "ni": 1155 },
          "adj": { "sbc": 63, "restructuring": 0, "fx": -13, "other": -19 },
          "segments": [
            { "type": "operating", "name": "Engine Products", "ebitda": 1040, "margin": 0.28 }
          ]
        }
      },
      "Q1": {}, "Q2": {}, "Q3": {}, "Q4": {}
    },

    "FY2025": {
      "annual": {
        "gaap": {
          "is": { "rev": 8252, "gp": 2820, "oi": 2046, "ni": 1508, "tax": 332, "da": 283, ... },
          "segments": [
            { "type": "operating", "name": "Engine Products", "rev": 4320 },
            { "type": "operating", "name": "Fastening Systems", "rev": 1745 },
            { "type": "operating", "name": "Engineered Structures", "rev": 1148 },
            { "type": "operating", "name": "Forged Wheels", "rev": 1039 }
          ]
        },
        "non_gaap": {
          "is": { "ebitda": 2390, "op": 2046, "ni": 1508 },
          "adj": { "sbc": 73, "restructuring": 15, "amort_intangible": 32, "fx": 3, "other": -7 },
          "segments": [
            { "type": "operating", "name": "Engine Products", "ebitda": 1438, "margin": 0.333 }
          ]
        }
      },
      "Q1": {
        "gaap": {
          "is": { "rev": 1942, "gp": 652, "oi": 490, "ni": 344, "tax": 102 },
          "segments": [
            { "type": "operating", "name": "Engine Products", "rev": 1017 }
          ]
        },
        "non_gaap": {
          "is": { "ebitda": 572 },
          "segments": [
            { "type": "operating", "name": "Engine Products", "ebitda": 328 }
          ]
        }
      },
      "Q2": {
        "gaap": { "is": { "rev": 2053, "gp": 688, "oi": 514, "ni": 407, "tax": 62 },
          "segments": [ { "type": "operating", "name": "Engine Products", "rev": 1075 } ]
        },
        "non_gaap": { "is": { "ebitda": 600 }, "segments": [ { "type": "operating", "name": "Engine Products", "ebitda": 344 } ] }
      },
      "Q3": { ... },
      "Q4": { ... }
    }
  },

  // ═══ 假设 + 投影（Agent 填）════
  "assumptions": {
    "lines": [
      // ── yoy / ebitda depth / 1:1 ──
      {
        "name": "L1 Engine Products",
        "module": "yoy",
        "one_to_one": true,
        "segment": "Engine Products",

        "yoy": {                           // 投影年 only
          "FY2026E": { "bull": 0.12, "base": 0.10, "bear": 0.05 },
          "FY2027E": { "bull": 0.12, "base": 0.10, "bear": 0.05 },
          "FY2028E": { "bull": 0.10, "base": 0.08, "bear": 0.05 },
          "FY2029E": { "bull": 0.10, "base": 0.08, "bear": 0.05 },
          "FY2030E": { "bull": 0.10, "base": 0.08, "bear": 0.05 }
        },
        "gm": {                            // 1:1 历史空；投影填
          "FY2026E": 0.34, "FY2027E": 0.34,
          "FY2028E": 0.35, "FY2029E": 0.35, "FY2030E": 0.35
        },
        "sotp": { "method": "ev_ebitda", "multiple": 10 }
      },

      // ── vol_asp / op depth / non-1:1 ──
      {
        "name": "tap-PD",
        "module": "vol_asp",
        "one_to_one": false,
        "segment": "外部品製造事業",
        "unit_scale": 1000,
        "asp_unit": "M¥/個",

        "volume": {
          "FY2025": 70,
          "FY2026E": 78, "FY2027E": 85, "FY2028E": 90, "FY2029E": 94, "FY2030E": 97
        },
        "tiers": [{
          "name": "tap-PD",
          "asp_base": {
            "FY2025": 30,
            "FY2026E": 32, "FY2027E": 34, "FY2028E": 36, "FY2029E": 37, "FY2030E": 38
          }
        }],
        "history": {
          "FY2023": { "volume": 60, "tap_pd_asp": 28 },
          "FY2024": { "volume": 65, "tap_pd_asp": 29 }
        },

        "gm": {                            // non-1:1 历史必填
          "FY2023": 0.475, "FY2024": 0.496, "FY2025": 0.525,
          "FY2026E": 0.534, "FY2027E": 0.547, "FY2028E": 0.55, "FY2029E": 0.55, "FY2030E": 0.55
        },
        "opm": {                           // OP depth
          "FY2026E": 0.272, "FY2027E": 0.28
        },
        "q_data": {                        // non-1:1 历史必填
          "FY2025": {
            "Q1": { "rev": 1, "volume": 20, "asp": 30 },
            "Q2": { "rev": 1, "volume": 22, "asp": 30 },
            "Q3": { "rev": 2, "volume": 18, "asp": 32 },
            "Q4": { "rev": 2, "volume": 19, "asp": 34 }
          }
        },
        "sotp": { "method": "pe", "multiple": 35 }
      }
    ],

    "seg_mapping": {
      "Engine Products": {
        "ebitda": {
          "FY2023": 947, "FY2024": 1040, "FY2025": 1438,
          "FY2026E": 1650
        },
        "margin": {
          "FY2023": 0.29, "FY2024": 0.28, "FY2025": 0.333,
          "FY2026E": 0.35
        }
      }
    },

    "global": {
      "tax_rate": { "FY2023": 0.22, "FY2024": 0.22, "FY2025": 0.22, "FY2026E": 0.22 },
      "opm": { "FY2023": 0.207, "FY2024": 0.303, "FY2025": 0.25, "FY2026E": 0.24 },
      "nm": { "FY2023": 0.10, "FY2024": 0.10, "FY2025": 0.10, "FY2026E": 0.10 }
    }
  },

  // ═══ 市场数据 ═══
  "market": {
    "price": 270.41, "mcap_m": 108193, "shares_m": 400.1,
    "pe_ttm": 62.9, "pe_fwd": 44.9, "pb": 19.6,
    "ev_ebitda": 43.2, "ev_revenue": 12.8,
    "beta": 1.19, "hi52": 290.63, "lo52": 169.45,
    "target_price_mean": 305.98,
    "_source": { "price": "yfinance" }
  },

  // ═══ 弹性 KPI ═══
  "kpi": {
    "fleet_hours": 45000000,
    "engine_spares_rev": 520
  }
}
```

## 顶层键总览

| key | 内容 | 来源 |
|-----|------|------|
| `identity` | 公司基本信息 | actuals-resolved |
| `meta` | 模型配置（depth/proj_years/Q 等） | driver-map |
| `actuals` | 历史披露：GAAP + non-GAAP、Y + Q、三表 + 段 | SEC + IR |
| `assumptions` | 所有假设：line 级 driver/margin、段映射、全局 | Agent |
| `market` | 股价/估值 | yfinance |
| `kpi` | 弹性指标 | Agent |
