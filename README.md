# 🧬 antiSMASH 8.0.4 安装与数据库配置完整流程（Mac + Linux + HPC）

本项目记录在 Mac（ARM 架构）及服务器环境中安装 **antiSMASH 8.0.4** 并手动配置数据库的完整流程，适用于次级代谢产物生物合成基因簇（BGC）分析。

---

# ⚠️ 重要说明

* antiSMASH **v8.0.4 已不支持 RiPP 预测**
* 如需 RiPP（核糖体合成肽）预测：

👉 推荐使用 **antiSMASH v7.1.0**

---

# 💻 一、Mac（ARM）安装 x86 环境

```bash
/usr/sbin/softwareupdate --install-rosetta --agree-to-license
arch -x86_64 /bin/zsh
uname -m   # 确认为 x86_64
```

---

# 📦 二、创建 antiSMASH 环境

```bash
conda config --set channel_priority flexible
CONDA_SUBDIR=osx-64 mamba create -n antismash8 antismash=8.0.4
```

---

# 🧹 三、环境清理（重要）

```bash
conda activate base

# 删除环境
mamba remove --name antismash8 --all
mamba env list

# 删除残留文件
rm -rf ~/miniforge3/envs/antismash7
rm -rf /data/run01/*/miniforge3/envs/antismash7

# 清理缓存
mamba clean --all

# 删除旧配置
rm -f ~/.antismashrc
```

---

# ⚙️ 四、配置 Conda 通道

```bash
conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge
conda config --set channel_priority strict
```

---

# 🚀 五、安装 antiSMASH 及依赖

```bash
mamba create -n antismash8 antismash=8.0.4
mamba install rodeo glimmerhmm meme -c bioconda -c conda-forge
mamba install bioconda::antismash
```

---

# 🔓 六、激活环境

```bash
conda activate antismash8
```

---

# 📚 七、数据库下载与配置

## 📥 数据来源

* ClusterBlast / MIBiG / MITE 等数据库
* Pfam：EBI 官方 FTP

---

## 🔧 配置步骤（核心）

### ClusterCompare（MIBiG）

```bash
wget https://dl.secondarymetabolites.org/releases/clustercompare/cc_mibig_4.0.tar.xz
tar -xJf cc_mibig_4.0.tar.xz
mkdir -p clustercompare
mv 4.0 clustercompare/mibig
```

---

### MITE

```bash
wget https://dl.secondarymetabolites.org/releases/mite/mite_1.3.tar.xz
tar -xJf mite_1.3.tar.xz
mkdir -p mite
mv 1.3 mite/1.3
```

---

### NRPS / PKS 模块

```bash
mkdir -p nrps_pks/svm/2.0
wget https://dl.secondarymetabolites.org/releases/nrps_svm/2.0/models.tar.xz
```

---

### TransATor

```bash
hmmpress transATor.hmm
```

---

### CompaRiPPson

```bash
mkdir -p comparippson/asdb/4.0 comparippson/mibig/4.0
```

---

# 📂 数据库结构示意

```bash
manually_antismash8.0.4_database/
├── clusterblast
├── clustercompare
├── comparippson
├── mite
├── nrps_pks
├── pfam
├── resfam
└── tigrfam
```

---

# ✅ 八、数据库完整性检查

```bash
antismash --databases ./manually_antismash8.0.4_database --check-prereqs
```

---

# 🖥️ 九、服务器运行（SLURM）

## 📄 运行脚本：`run_antismash8.sh`

```bash
#!/bin/bash
#SBATCH -p amd_512
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 32

## 集群服务器激活环境
module load miniforge/24.11
source activate /public3/home/scg4618/mambaforge3/envs/antismash8


## 普通电脑激活环境
mamba activate antismash8
export PYTHONUNBUFFERED=1

# 真菌
antismash \
  --taxon fungi \
  --databases ./manually_antismash8.0.4_database \
  --output-dir output_dir \
  --genefinding-gff3 genome.gff3 \
  --cpus 32 \
  --fullhmmer \
  --clusterhmmer \
  --asf \
  --cc-mibig \
  --cb-general \
  --cb-subclusters \
  --cb-knownclusters \
  --pfam2go \
  --rre \
  --smcog-trees \
  --tfbs \
  --tigrfam \
  genome.fa
# 细菌
antismash \
  --taxon bacteria \
  --databases ./manually_antismash8.0.4_database \
  --output-dir Burkholderia_gladioli.antismash8.output \
  --genefinding-gff3 genomic.gff \
  --cpus 32 \
  --fullhmmer \
  --clusterhmmer \
  --asf \
  --cc-mibig \
  --cb-general \
  --cb-subclusters \
  --cb-knownclusters \
  --pfam2go \
  --rre \
  --smcog-trees \
  --tfbs \
  --tigrfam \
  Burkholderia_gladioli_ASM1669870v1_genomic.fa

```
---

## 🚀 提交任务

```bash
sbatch run_antismash8.sh
```

---

## 📊 作业管理

```bash
squeue        # 查看任务
scancel JOBID # 终止任务
```

---

# 📈 十、结果分析（结合转录组）

## 1️⃣ BGC 基因统计

```bash
pip install pandas
python count_antismash_genes.py \
    -i input_dir \
    -d DEGs_list.txt \
    -o result.xlsx
```

---

## 2️⃣ BGC 汇总分析

```bash
python summarize_bgc_stats.py \
  -i result.xlsx \
  -o Final_BGC_Stats.xlsx
```

---

## 3️⃣ 可视化

```bash
python plo_bgc_summary_dot.py \
    -i BGC_Type_Averages.xlsx \
    -o plot.png
```

---

## 4️⃣ DEG vs DEM 相关性分析

```bash
python pearson_analysis_T.py \
    -d DEGs_expression.csv \
    -m DEMs_abundance.csv \
    -o results_corr.csv
```

---

## 5️⃣ 网络图绘制

```bash
python plot_network.py \
    -i correlation_data.txt \
    -o network.png
```

---

# 🧪 十一、扩展工具（推荐）

## 🔹 GECCO（快速 BGC 预测）

```bash
conda create -n gecco_env -c bioconda gecco -y
```

---

## 🔹 TrRiPP（Transformer）

```bash
conda create -n trripp_env python=3.8 -y
conda activate trripp_env
pip install torch transformers biopython pandas
```

---

## 🔹 BGC-MAC（最新深度学习方法）

```bash
conda create -n bgcmac_env python=3.9 -y
conda activate bgcmac_env
pip install torch esm biopython
```

---

# 🧠 总结

本流程实现：

✔ antiSMASH 8.0.4 完整安装
✔ 手动数据库配置
✔ HPC 批量运行
✔ 与转录组/代谢组联合分析

---

# 📂 antiSMASH 8.0.4 数据库结构说明

在完成所有数据库下载与配置后，`antiSMASH 8.0.4` 的数据库目录应具有如下标准结构（非常重要，用于排错与复现）：

---

## 📁 标准数据库目录结构

```bash
./
├── as-js
│   └── 0.16
│       └── antismash.js
├── clusterblast
│   ├── clusters.txt
│   └── proteins.fasta
├── clustercompare
│   └── mibig
│       ├── data.json
│       └── proteins.fasta
├── comparippson
│   ├── asdb
│   │   └── 4.0
│   │       ├── cores.fa
│   │       └── metadata.json
│   └── mibig
│       └── 4.0
│           ├── cores.fa
│           └── metadata.json
├── knownclusterblast
│   ├── clusters.txt
│   └── proteins.fasta
├── mite
│   └── 1.3
│       ├── metadata.json
│       └── mite.fasta
├── nrps_pks
│   ├── stachelhaus
│   │   └── signatures.tsv
│   ├── svm
│   │   └── 2.0
│   │       ├── bacterial_1class.mdl
│   │       ├── checksums.json
│   │       ├── NRPS1_LARGE_CLUSTER
│   │       ├── NRPS1_SMALL_CLUSTER
│   │       ├── NRPS2_LARGE_CLUSTER
│   │       ├── NRPS2_SINGLE_CLUSTER
│   │       ├── NRPS2_SMALL_CLUSTER
│   │       ├── NRPS2_THREE_CLUSTER
│   │       └── NRPS2_THREE_CLUSTER_FUNGAL
│   └── transATor
│       └── 2023.02.23
│           ├── transATor.hmm
│           ├── transATor.hmm.h3f
│           ├── transATor.hmm.h3i
│           ├── transATor.hmm.h3m
│           └── transATor.hmm.h3p
├── pfam
│   └── 35.0
│       ├── Pfam-A.hmm
│       ├── Pfam-A.hmm.h3f
│       ├── Pfam-A.hmm.h3i
│       ├── Pfam-A.hmm.h3m
│       └── Pfam-A.hmm.h3p
├── resfam
│   ├── Resfams.hmm
│   ├── Resfams.hmm.h3f
│   ├── Resfams.hmm.h3i
│   ├── Resfams.hmm.h3m
│   └── Resfams.hmm.h3p
└── tigrfam
    ├── TIGRFam.hmm
    ├── TIGRFam.hmm.h3f
    ├── TIGRFam.hmm.h3i
    ├── TIGRFam.hmm.h3m
    └── TIGRFam.hmm.h3p
```

---

## 📊 统计信息

* 📁 共 **31 个目录**
* 📄 共 **115 个文件**

---

## 📍 实际路径示例（Mac）

```bash
cd /Users/liangdong/Desktop/antismash/manually_antismash8.0.4_database
tree ./
```

---

## ✅ 如何验证数据库是否正确

使用 `antiSMASH` 自带检测命令：

```bash
antismash --databases ./manually_antismash8.0.4_database --check-prereqs
```

---

## ⚠️ 常见错误

### ❌ 1. 目录层级错误

例如：

```bash
clustercompare/4.0   ❌
clustercompare/mibig/4.0   ✅
```

---

### ❌ 2. HMM 文件未压缩

必须包含：

```bash
.h3f / .h3i / .h3m / .h3p
```

否则运行会报错

---

### ❌ 3. 文件缺失

典型缺失：

* `proteins.fasta`
* `clusters.txt`
* `metadata.json`

---

## 🧠 建议

* 📦 建议将该数据库单独压缩保存（避免重复下载）
* 📂 可在服务器统一路径管理（如 `/data/db/antismash/`）
* 🔁 不同版本 antiSMASH 数据库不可混用

---

## 🚀 提示

该数据库结构是 **antiSMASH 能否正常运行的核心关键之一**，
建议在运行分析前务必完成检查。

---

# 📬 说明

如有问题欢迎提交 Issue 或交流改进。

---
