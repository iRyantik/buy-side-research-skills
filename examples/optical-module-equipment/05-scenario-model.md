# Step 5: 场景量化测算

> **Skill**: `/scenario-model` | **Layer**: supporting | **时间**: ~15 分钟

---

## 🗣 问

> "用 scenario-model 算：CPO 渗透 >15% 场景下，Long AEHR 的理论回报。需要 TAM x 份额 x margin x PE 全链路有 source 标注，不能自己拍数。"

### 为什么要这样问

candidate-screener 给了方向（Long AEHR）和定性（"小赌注"），但没给出量化目标。scenario-model 的任务是把 TAM→份额→业绩→市值这条链算出来，并且每个数字能溯源。关键约束："不能自己拍数"——让 AI 知道必须找 source。

---

## 🤖 答 — Phase 1 假设表

| 假设 | 值 | 来源 | Tier | Confidence |
|---|---|---|---|---|
| CPO burn-in TAM 2028 | $1.2B | Frost via 猎奇招股书 | 1 | Medium |
| AEHR share | 60% | mechanism-insight：晶圆 Burn-in 龙头 | 2 | Low |
| Target margin | 25% | 当前 ~22% + scale | 2 | Medium |
| Target PE | 40x | Semi equip peers 2028 forward PE | 1 | Medium |

---

## 🤖 答 — Phase 2 测算

| Step | Value |
|---|---|
| 场景收入 | $720M |
| 场景利润 | $180M |
| 场景市值 | $7.2B |
| 当前市值 | $2.9B |
| **Upside** | **+148%** |

---

## 🗣 追问 1

> "你这个 TAM 是哪里来的？share 60% 的依据是什么？"

### 🤖 回复

> TAM 来源：猎奇智能招股说明书引用弗若斯特沙利文（Frost & Sullivan）"全球光模块封测设备市场 2028E CNY 51.8B"，CPO burn-in test 细分占比 ~17%，换算 $1.2B。
> Share 60% 依据：mechanism-insight 竞争格局显示 AEHR 当前是全球唯一晶圆级 Burn-in 量产供应商。但如果 Teradyne/Keysight 等传统测试巨头进入，share 可能降到 40-50%。

---

## 🗣 追问 2

> "如果这个 share 降到 40%，upside 是多少？"

### 🤖 Sensitivity

| 份额 | Upside |
|---|---|
| 40% | +100% |
| 60% | +148% |
| 75% | +185% |

---

## 📝 研究员笔记

**scenario-model 最有价值的不是那个 +148%**，而是 sensitivity 告诉你：share 从 60%→40%，upside 依然 100%。**这意味着 AEHR 的 thesis 不是赌在"他必须是唯一供应商"上——即使有竞争，回报依然可观。这是 candidate-screener "小赌注"判断的量化支撑。**

**AI 局限**：TAM 用了招股书里的 Frost 数据。研究员后来交叉验证发现 Frost 在 IPO 招股书里通常偏大 20-30%——如果下调 TAM，upside 可能降到 80-100%。这个 bias 需要研究员自己判断。

---

## 总结：5 步走完

```
teach-in → industry-landscape → mechanism-insight → candidate-screener → scenario-model
  (物理直觉)    (行业全景+价值池)    (竞争格局机制)    (分场景L/S排序)      (量化测算)
```

3 个在 foundation、1 个在 deep-work、1 个在 supporting。**关键是：AI 做了数据收集和初稿，研究员做了判断和验证。**

> ⚠️ scenario-model 是本 session 中设计的新 skill，未实际运行过。上面的测算摘录来自对话中的手动推算。安装 v5.0.0 后，`/scenario-model` 可自动执行两 Phase 流程。
