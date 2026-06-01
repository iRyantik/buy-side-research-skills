# Step 1: 建立物理直觉

> **Skill**: `teach-in` | **Layer**: foundation | **时间**: ~30 分钟 | **产出**: [完整 artifact](https://github.com/iRyantik/buy-side-research-skills/blob/main/examples/optical-module-equipment/artifacts/2026-06-01-teach-in.md)

---

## 🗣 问 1

> "光模块设备行业我不了解。光模块是做什么的？制造链条上有哪些设备？用 teach-in 教我。"

### 为什么要这样问

不要先问"这个行业值不值得投"——如果连光模块是什么都不知道，后面的判断没有根基。teach-in 是 foundation 层的第一个 skill，专门用于"零基础建立物理直觉"。关键是把问题拆成两层：产品本身是什么 + 怎么造出来的（设备链）。

---

## 🤖 答 1

AI 自动把光模块设备 teach-in 拆成了 6 层：

**Layer 1: 光模块是什么**
> 光模块 = 服务器里把电信号转成光信号的"翻译器"。没有它，数据中心里的 GPU 之间没法用光纤通信。一个 800G 光模块每秒能传 800Gbps。

**Layer 2: 内部长什么样**
> 拿一个 800G 模块拆开：PCB 板 → 光芯片(DSP+laser) → 金线键合 → 光纤耦合(Lens/Fiber Array) → 外壳。

**Layer 3: 关键材料**（InP/GaAs/Si/SiPh/LiNbO₃ 五种材料平台 + 供应链）

**Layer 5: 设备链条**
```
固晶机(贴芯片) → 键合机(金线) → 耦合机(对光纤) → 老化柜(Burn-in) → 终测
```

**Layer 6: 谁做什么**
> 中际旭创/Coherent/新易盛 = 模块厂（买设备、做模块）
> MRSI/Besi/ASMPT = 设备厂（造设备、卖给模块厂）

---

## 🗣 问 2

> "图片没下载好。这个 teach-in 还是太简单了，我对耦合、固晶这些东西完全没概念。能不能配图？"

### 🤖

下载了 11 张产品实物图（800G 模块、晶圆芯片、引线键合 SEM 图、Keysight 测试机、AEHR Burn-in 系统、Broadcom CPO 交换机等），嵌入到各 Layer。

---

## 🗣 问 3（关键转向）

> "光学耦合这一步，光纤是做到光模块里面的吗？"

### 🤖 答

> 对。耦合就是把比头发丝还细的单模光纤（芯径 9μm）对准芯片上的光口，精度要求 ±0.3μm。这是整条链最难的一站——不是因为硬件精度高，而是需要六轴实时闭环反馈（X/Y/Z + 俯仰/偏摆/旋转），还需要针对每客户的光路设计调算法。

---

## 📝 研究员笔记

**最重要的收获**：看完 teach-in 后改变了研究方向。原本想研究"光模块行业"，发现模块厂壁垒不高（中际旭创毛利率 25%，设备厂 MRSI 毛利率 55%）。**利润在设备端，不在模块端。** 所以后续研究全部聚焦设备。

**AI 好在哪里**：
- 自动拆成 6 层，从物理→产业
- 实时响应追问（耦合原理、材料、CPO 定义）
- 主动下载产品实物图配文

**AI 局限**：
- Layer 6 的"谁做什么"表漏了 ficonTEC/镭神技术等耦合设备商——后来在 mechanism-insight 里补上的
- 前几次下载的图片有些是 WebP 格式，有些 URL 不对——需要人工纠正

**你觉得无聊但 AI 替你做了的**：31 张示意图计划、图片下载、格式排版、source 标注。

---

## 下一步

> "用 industry-landscape 看光模块设备行业"

📄 **完整产出**: [2026-06-01-teach-in.md](https://github.com/iRyantik/buy-side-research-skills/blob/main/examples/optical-module-equipment/artifacts/2026-06-01-teach-in.md)（~11,000 字，含图片）
