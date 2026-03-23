import os
import glob
import pandas as pd
from Bio import SeqIO
import argparse

def load_deg_list(deg_file):
    """
    读取差异表达基因列表文件，返回一个集合(Set)以加快查找速度。
    支持简单的文本文件（每行一个基因ID）或单列CSV。
    """
    deg_set = set()
    if not deg_file:
        return deg_set

    print(f"📖 正在读取差异表达基因列表: {deg_file}")
    try:
        # 尝试作为文本文件逐行读取
        with open(deg_file, 'r', encoding='utf-8') as f:
            for line in f:
                # 去除空白符、引号等杂质
                gene = line.strip().strip('"').strip("'")
                if gene:
                    deg_set.add(gene)
        print(f"✅ 成功加载 {len(deg_set)} 个差异基因 ID。")
    except Exception as e:
        print(f"⚠️ 读取 DEG 文件失败: {e}")
        print("   将继续执行，但 DEGs 列将全部显示为 NO。")
    
    return deg_set

def extract_bgc_info_long(input_dir, output_file, deg_file=None):
    """
    遍历 antiSMASH 输出目录，提取 BGC 信息，并与 DEGs 列表进行比对。
    """
    all_rows = [] 
    
    # 1. 加载差异基因列表（如果有）
    deg_set = load_deg_list(deg_file)
    
    # 2. 寻找目录下所有的 .region*.gbk 文件
    search_path = os.path.join(input_dir, "*.region*.gbk")
    gbk_files = glob.glob(search_path)
    
    if not gbk_files:
        print(f"❌ 错误：在目录 {input_dir} 中没有找到任何 .gbk 文件。")
        return

    print(f"🚀 找到 {len(gbk_files)} 个 BGC 文件，开始解析并比对基因...")
    
    for gbk_file in sorted(gbk_files):
        # 获取文件名作为 BGC_ID
        bgc_id = os.path.basename(gbk_file).replace(".gbk", "")
        
        try:
            record = SeqIO.read(gbk_file, "genbank")
        except Exception as e:
            print(f"⚠️ 读取文件 {bgc_id} 出错: {e}")
            continue
        
        cluster_type = "Unknown"
        
        # 3. 遍历特征
        # 先获取 Cluster 类型 (通常在 region 或 protocluster 中)
        for feature in record.features:
            if feature.type in ["region", "protocluster"]:
                if "product" in feature.qualifiers:
                    cluster_type = ",".join(feature.qualifiers["product"])
        
        # 再次遍历提取 CDS 基因并比对 DEGs
        for feature in record.features:
            if feature.type == "CDS":
                gene_id = "Unnamed_Gene"
                if "locus_tag" in feature.qualifiers:
                    gene_id = feature.qualifiers["locus_tag"][0]
                elif "gene" in feature.qualifiers:
                    gene_id = feature.qualifiers["gene"][0]
                
                # --- 核心修改逻辑：判断是否为 DEGs ---
                is_deg = "NO"
                # 判断 gene_id 是否在 deg_set 集合中
                if gene_id in deg_set:
                    is_deg = "YES"
                
                all_rows.append({
                    "BGC_ID": bgc_id,
                    "BGC_Type": cluster_type,
                    "Genes": gene_id,
                    "DEGs": is_deg  # 新增列
                })

    # 4. 导出结果
    df = pd.DataFrame(all_rows)
    
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if output_file.endswith('.xlsx'):
        df.to_excel(output_file, index=False)
    else:
        df.to_csv(output_file, index=False, sep='\t' if output_file.endswith('.txt') else ',')
    
    print("-" * 30)
    print(f"✅ 处理完成！")
    # 统计有多少个 YES
    yes_count = df[df['DEGs'] == 'YES'].shape[0] if 'DEGs' in df.columns else 0
    print(f"📊 数据已展开，共生成 {len(df)} 行记录。")
    print(f"🔍 其中匹配到差异基因 (YES) 的记录数: {yes_count}")
    print(f"💾 保存路径: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将 antiSMASH 结果提取并展开，同时标记差异表达基因(DEGs)")
    
    parser.add_argument("-i", "--input", required=True, help="antiSMASH 结果文件夹路径")
    parser.add_argument("-o", "--output", required=True, help="输出文件路径 (.xlsx, .csv, 或 .txt)")
    # 新增的可选参数
    parser.add_argument("-d", "--degs", required=False, help="差异表达基因列表文件 (txt或csv，每行一个基因ID)，不提供则该列全为NO")

    args = parser.parse_args()
    
    if os.path.isdir(args.input):
        extract_bgc_info_long(args.input, args.output, args.degs)
    else:
        print(f"❌ 错误：找不到输入目录 {args.input}")