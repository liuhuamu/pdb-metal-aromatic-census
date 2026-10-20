# PDB 金属-芳香环相互作用高通量筛选管线

> **2026-10-15 全流程运行完成**，最终结果：
> - L1：92,487 个含芳香配体的结构 / 37,877 个芳香配体 comp ID
> - L2：37,337 个候选结构（芳香配体 ∧ 金属离子）
> - L3：下载 37,336 cif + 33,491 pdb（~140 GB）；**57,578 个金属-芳香环接触入库，
>   来自 7,953 个结构**；29,384 个结构被排除（24,676 无 ≤6 Å 接触、3,724 分辨率差等）
> - 归档：47 个（分桶×金属）文件夹，output/structures/
> - 分类：face-on 223 / edge-on 12,348 / mid 1,031 / chelated 43,976（血红素+叶绿素类）
>
> 设计文档见 `../docs/pipeline_design.md`；API 查询模板已于 2026-10-15 对
> RCSB 生产环境实测验证。**重要**：entry 级化学搜索会把 Phe/Tyr/Trp 等聚合物
> 残基也计入（苯环虚高至 255,847），因此 L1 必须使用
> `return_type="non_polymer_entity"`——苯环真实命中 52,638 个结构
> （55,521 个配体实体对）。

## 安装

```bash
pip install -r requirements.txt     # requests, numpy, pandas, matplotlib, networkx, gemmi
```

Python ≥ 3.9。无需 rdkit（环感知直接使用每个 entry 自带的 `chem_comp_bond` 芳香性标注）。

## 运行（按顺序）

```bash
python step1_aromatic.py    # L1: 9 个芳香环 SMILES 子结构搜索（在线，~10 min）
python step2_metals.py      # L2: 每金属一次分子式查询 + 本地交集（在线，~30 min）
python step3_download.py    # L3a: 下载候选结构 cif + pdb 双格式（16 线程，可断点续传）
python step4_geometry.py    # L3b: 几何分析 -> data/results.sqlite（可断点续传）
python step5_organize.py    # L4: 命中结构按 分桶/金属 归档 + index.csv
python step6_stats.py       # L5: 统计表 + 分布直方图
```

试运行（小样本验证流程）：

```bash
python step4_geometry.py --limit 50      # 只分析前 50 个候选
python step5_organize.py --dry-run       # 只显示将生成的文件夹布局
```

断点续传：step3 自动跳过已下载文件；step4 自动跳过已入库的 entry（`--force` 强制重算，
`--only 1AI0,3GKY` 指定重算条目）。

## 输出布局

```
data/
  aromatic_entries.json     L1: 每环型命中的 PDB ID
  aromatic_ligands.json     L1: 每环型命中的配体 comp ID
  candidates.json           L2: {pdb_id: [金属元素列表]}
  metals/<Element>.json     L2: 每金属候选明细
  download_errors.json      L3a: 下载失败记录
  results.sqlite            L3b: hits / excluded 两张表（核心数据库）
cache/
  cif/<ID>.cif              全部候选结构（mmCIF）
  pdb/<ID>.pdb              全部候选结构（PDB 格式；超大结构可能缺失）
output/
  structures/               ★ 最终结构库（分桶 → 金属 → 几何类别）
    A_d10_metpi/            d10 离子（Zn/Cd/Hg/Cu/Ag/Au）— metal-π 经典
      Zn/face-on|edge-on|mid/   每类别子文件夹：命中结构 cif+pdb + index.csv
    B_alkali_cationpi/      碱(土)金属（K/Na/Mg/Ca/...）— cation-π 经典
    C_transition/           其他过渡金属（Fe/Mn/Co/Ni/...）
    D_noble/                贵金属（Pt/Pd/Ir/...）
    chelated/               血红素类"金属内嵌大环"（配位，非 metal-π；不分类别）
    summary.csv  README.txt
  class_stats_by_metal.csv  每金属 face-on/edge-on/mid 接触数、占比、结构数
  counts_by_bucket.csv      桶 × 几何类别计数
  counts_by_metal.csv       金属 × 几何类别计数
  top_ligands.csv           每金属最常见芳香配体
figures/
  dist_hist_A/B/C/D.png     各桶 d_centroid / d_plane / offset 分布
  dist_hist_chelated.png
```

`hits` 表关键字段：`pdb_id, metal_comp_id/element/charge/bucket/embedded,
ligand_comp_id, ring_type, d_centroid, d_plane, offset, theta_deg, min_dist,
geometry_class(face-on/edge-on/mid/chelated), coordination, resolution, ...`

## 已确认的科学标准（2026-10-15）

| 决策 | 取值 |
|---|---|
| 血红素类金属内嵌大环 | 单独 `chelated` 桶（金属-环原子距离 ≤2.8 Å 判据） |
| face-on | offset ≤1.5 Å 且 d_plane ∈ [2.5, 4.5] Å |
| edge-on | offset >2.5 Å（如 6HWZ：4.28/2.41/3.54 Å） |
| 命中阈值 | 金属-环质心距离 ≤6.0 Å |
| 分辨率 | ≤3.0 Å（缺失分辨率记入 excluded） |
| 对称性 | v1 仅不对称单元，不做 assembly 扩展 |
| 金属占有率 | ≥0.5 |
| NMR | 取 model 1 |
| 下载格式 | cif + pdb 双格式 |

## 注意事项 / 已知局限

- **本代码未在开发环境实际运行过**（开发机 shell 故障），但所有 API JSON 模板都经过
  实测验证；首次请用 `--limit` 小样本试跑。
- step2 的金属分子式查询返回 entry 列表（实测 AND 组合下可用）；若个别金属返回空，
  请检查 RCSB 服务状态或改用 rcsbsearchapi 包。
- 金属氧化态来自 `config.py` 的静态映射（常见 comp），罕见 comp 记为 NULL，
  可按需扩展 `METAL_COMPS`。
- 超大结构（>约 100 万原子）无 PDB 格式文件，pdb 缺失会记录在
  `data/download_errors.json`，cif 始终可用。
- 晶体对称相关的金属-配体接触（跨对称操作）v1 未覆盖——统计时注意此 caveat，
  v2 可用 gemmi 生成 assembly 后重算。
- molybdate 等含氧金属酸根不以"自由离子"形式检测（多原子残基），如需统计请扩展
  `METAL_COMPS` 与检测逻辑。
- RCSB Search API 请适度使用：代码内置 0.4 s 分页间隔与 429/5xx 退避重试。

## 规模预估

| 步骤 | 预计耗时（单工作站） |
|---|---|
| step1 + step2（在线查询） | ~40 min |
| step3 下载（~5-10 万结构 × 2 格式，30-80 GB） | 4-8 h（16 线程） |
| step4 几何分析 | 3-6 h |
| step5 + step6 | 分钟级 |
