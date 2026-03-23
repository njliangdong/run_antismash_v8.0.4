import pandas as pd
from scipy.stats import pearsonr
import argparse
import sys

def run_pearson_analysis_transposed(deg_file, dem_file, output_file, r_threshold=0.7, p_threshold=0.05):
    """
    加载转置格式（实体x样本）数据，执行 Pearson 相关性分析并保存结果。
    """
    try:
        # 读取数据：第一列作为索引（实体ID），然后执行转置 (.T)
        # 确保数据变为：行=样本，列=实体
        df_deg_T = pd.read_csv(deg_file, index_col=0).T 
        df_dem_T = pd.read_csv(dem_file, index_col=0).T
    except Exception as e:
        print(f"Error reading or transposing file: {e}")
        sys.exit(1)

    # 检查样本（行）是否一致 (转置后样本在行)
    if not df_deg_T.index.equals(df_dem_T.index):
        print("Error: Sample IDs (columns in your input file) do not match or are not in the same order!")
        print("Please check the column names of your DEG and DEM files.")
        sys.exit(1)
        
    num_samples = df_deg_T.shape[0]
    if num_samples < 8:
        print(f"\nWarning: Only {num_samples} samples found. For reliable statistical power, N >= 8 is recommended.\n")

    print(f"Loaded {num_samples} samples, {df_deg_T.shape[1]} DEGs, and {df_dem_T.shape[1]} DEMs.")
    print(f"Thresholds: |r| > {r_threshold}, p < {p_threshold}")

    correlation_results = []

    # 遍历所有 DEG 和 DEM 对 (现在实体ID在列名)
    for deg_id in df_deg_T.columns:
        for dem_id in df_dem_T.columns:
            x = df_deg_T[deg_id]
            y = df_dem_T[dem_id]
            
            try:
                # x 和 y 都是样本 x 1 的 Series
                r, p = pearsonr(x, y)
            except ValueError:
                # 当数据集中所有样本的值都相同时，计算失败，跳过
                continue 
            
            # 筛选显著相关的对
            if abs(r) >= r_threshold and p < p_threshold:
                correlation_results.append({
                    'DEG_ID': deg_id,
                    'DEM_ID': dem_id,
                    'Pearson_r': r,
                    'P_value': p,
                    'Relationship': 'Positive' if r > 0 else 'Negative'
                })

    results_df = pd.DataFrame(correlation_results)
    
    results_df['abs_r'] = results_df['Pearson_r'].abs()
    results_df = results_df.sort_values(by='abs_r', ascending=False).drop(columns=['abs_r'])

    results_df.to_csv(output_file, index=False)
    print(f"\nAnalysis complete. Found {len(results_df)} significant correlations.")
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    # 使用 argparse 配置命令行参数
    parser = argparse.ArgumentParser(description="DEG-DEM Pearson Correlation Analysis (Transposed Format)")
    parser.add_argument('-d', '--deg_file', required=True, help="Path to the DEG expression data file (CSV/TSV).")
    parser.add_argument('-m', '--dem_file', required=True, help="Path to the DEM abundance data file (CSV/TSV).")
    parser.add_argument('-o', '--output_file', required=True, help="Path for the output correlation results file (CSV).")
    parser.add_argument('--r_thresh', type=float, default=0.7, help="Minimum absolute Pearson correlation coefficient threshold (default: 0.7).")
    parser.add_argument('--p_thresh', type=float, default=0.05, help="Maximum P-value threshold (default: 0.05).")
    
    args = parser.parse_args()
    
    run_pearson_analysis_transposed(args.deg_file, args.dem_file, args.output_file, args.r_thresh, args.p_thresh)
