import pandas as pd
import argparse
import os
import sys

def summarize_bgc_stats(input_file, output_file, type_summary_file):
    """
    1. 统计每个 BGC 的详细信息。
    2. 根据 BGC_Type 统计平均 DEG_percentage。
    """
    print(f"📂 正在读取输入文件: {input_file}")
    
    # --- 1. 读取原始基因列表数据 ---
    try:
        if input_file.endswith('.xlsx'):
            df = pd.read_excel(input_file)
        else:
            df = pd.read_csv(input_file, sep=None, engine='python')
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        sys.exit(1)

    df.columns = df.columns.str.strip()
    
    if 'BGC_ID' not in df.columns or 'DEGs' not in df.columns:
        print(f"❌ 错误：输入文件缺少必要列 (BGC_ID, DEGs)。")
        sys.exit(1)

    if 'BGC_Type' not in df.columns:
        df['BGC_Type'] = 'Unknown'

    df['DEGs'] = df['DEGs'].astype(str).str.upper().str.strip()

    # --- 2. 生成详细统计表 (Final_BGC_Stats) ---
    summary = df.groupby(['BGC_ID', 'BGC_Type']).agg(
        Total_Genes=('DEGs', 'count'),
        DEG_Count=('DEGs', lambda x: (x == 'YES').sum())
    ).reset_index()

    # 计算百分比数值 (用于后续计算平均值)
    summary['Percentage_Val'] = (summary['DEG_Count'] / summary['Total_Genes'] * 100).round(2)
    # 转换为字符串格式
    summary['DEG_percentage'] = summary['Percentage_Val'].astype(str) + '%'

    # 筛选详细表的5列并保存
    detail_cols = ['BGC_ID', 'BGC_Type', 'Total_Genes', 'DEG_Count', 'DEG_percentage']
    detail_df = summary[detail_cols].sort_values(by=['DEG_Count'], ascending=False)

    try:
        detail_df.to_excel(output_file, index=False)
        print(f"✅ 详细统计表已保存至: {output_file}")
    except Exception as e:
        print(f"❌ 保存详细表失败: {e}")

    # --- 3. 生成 BGC_Type 类型汇总表 (新增功能) ---
    if type_summary_file:
        print(f"📊 正在按 BGC_Type 计算平均值...")
        
        # 计算每个类型的平均百分比
        type_avg = summary.groupby('BGC_Type').agg(
            Average_DEG_percentage=('Percentage_Val', 'mean'),
            BGC_Count=('BGC_ID', 'count') # 顺便统计该类型下有多少个簇
        ).reset_index()

        # 格式化百分比
        type_avg['Average_DEG_percentage'] = type_avg['Average_DEG_percentage'].round(2).astype(str) + '%'
        
        # 排序：按平均百分比降序
        type_avg = type_avg.sort_values(by='Average_DEG_percentage', ascending=False)

        try:
            type_avg.to_excel(type_summary_file, index=False)
            print(f"✅ 类型汇总表已保存至: {type_summary_file}")
        except Exception as e:
            print(f"❌ 保存汇总表失败: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="统计 BGC 差异基因并进行类型平均值分析")
    parser.add_argument("-i", "--input", required=True, help="输入基因列表文件 (.csv/.xlsx)")
    parser.add_argument("-o", "--output", required=True, help="输出详细 Excel 文件路径 (每个BGC一行)")
    parser.add_argument("-s", "--summary", required=True, help="输出类型汇总 Excel 文件路径 (每个BGC_Type一行)")

    args = parser.parse_args()

    # 检查输入
    if os.path.isfile(args.input):
        summarize_bgc_stats(args.input, args.output, args.summary)
    else:
        print(f"❌ 错误：找不到输入文件 {args.input}")