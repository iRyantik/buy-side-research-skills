# Step 3: 深挖竞争格局

> **Skill**: `/mechanism-insight` | **Layer**: foundation | **时间**: ~30 分钟 × 3 次调用

---

## 🗣 问 1 — 固晶设备

> "深挖固晶设备竞争格局，MRSI vs Besi vs ASMPT vs 猎奇智能，每家精度、客户、CPO 准备情况"

### 为什么要拆开问

固晶和耦合是两个不同的竞争格局，混在一起会模糊关键差异。固晶的核心变量是精度（±1μm 俱乐部），耦合的核心变量是算法+客户锁入。

---

## 🤖 答 1 — 关键摘录

**竞争对位**：

| | MRSI (Mycronic) | Besi | ASMPT | 猎奇智能 |
|---|---|---|---|---|
| 精度段 | ±1-3μm | ±1μm | ±3-5μm | ±5-7μm |
| 1.6T 准备好了？ | ✅ 量产 | ✅ 量产 | ⚠️ 在研 | ❌ 精度不够 |
| CPO 路线 | 固晶+耦合打包 | hybrid bonding | AMICRA NANO | 无 |

**核心 insight**：1.6T 要求 ±3μm 精度——这个门槛直接筛掉了猎奇。精度升级就是代际壁垒。

---

## 🗣 问 2 — 耦合设备

> "深挖耦合设备竞争格局，ficonTEC vs 镭神技术 vs MRSI-A-L vs 猎奇智能"

### 🤖 答 2 — 关键摘录

| | ficonTEC | 镭神技术 | MRSI-A-L |
|---|---|---|---|
| 精度天花板 | **±0.3μm** | ±0.5μm | 亚微米 |
| CPO 量产验证 | ✅ 博通 Bailly 独家 | ❌ | ⚠️ 在研 |
| 客户锁入 | 极高（博通/英伟达独家） | 中 | 中高 |

**核心 insight**：耦合壁垒是算法+工艺数据库+客户光路设计绑定=**导入后极难替换**。

---

## 🗣 追问 3 — CPO 技术路线分歧

> "为什么 Besi 的客户是 TSMC 这些，而不是 Coherent 这些光模块厂？"

### 🤖 答 3

> 因为 hybrid bonding 是晶圆级工艺，在芯片还没切割的时候做。这步发生在 TSMC 的 fab 里——不是光模块厂的封测车间。Besi 的 D2W（Die-to-Wafer）hybrid bonding 机台卖给了 TSMC COUPE 产线。
> 而 ficonTEC/MRSI 做的是传统 die bond（芯片已切割，放到基板上），仍发生在封测段。两条路线竞争关系。

**这是整个研究最重要的 insight**：CPO 不是一条路，是两条路在竞争。Besi 的客户不是光模块厂而是 foundry，ficonTEC 仍绑着光模块厂的封测线。

---

## 📝 研究员笔记

**最关键的一步**。做完机制深挖后，对谁会在 CPO 时代受益的理解从"Besi 最大"变成了"有两套逻辑、ficonTEC/Besi/双受益、模块 Burn-in 受损"。**这个框架就是后面 candidate-screener 分场景排序的底层。**

---

## 下一步

> "搞定。现在帮我做 L/S 排序。不仅要看当前，还要分场景——Pluggable 继续主导 vs CPO 过渡 vs CPO 成为主流，每个场景下多/空方向可能不同。用 candidate-screener 做。"

---

📄 **完整产出**: [2026-06-01-mechanism-insight-coupling.md](https://github.com/iRyantik/buy-side-research-skills/blob/main/examples/optical-module-equipment/artifacts/2026-06-01-mechanism-insight-coupling.md)
