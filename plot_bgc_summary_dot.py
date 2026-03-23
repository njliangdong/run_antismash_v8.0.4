import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os
import sys

# 设置全局字体，尝试解决中文显示问题（如果BGC Type中有中文的话）
# 如果仍然无法显示中文，可能需要手动指定系统存在的英文字体，如 'Arial' 或 'Times New Roman'
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False
except Exception:
    pass

def plot_bgc_distribution(input_file, output_image):
    # 1. 设置绘图风格
    sns.set_theme(style="whitegrid", context="talk") # context="talk" 会让整体字体和元素稍微大一点，适合展示
    
    # 2. 读取数据
    print(f"📂 正在读取数据: {input_file}")
    try:
        if input_file.endswith('.xlsx'):
            df = pd.read_excel(input_file)
        else:
            df = pd.read_csv(input_file, sep=None, engine='python')
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        sys.exit(1)

    # 基本检查
    required_cols = ['BGC_Type', 'BGC_Count', 'Average_DEG_percentage']
    if not all(col in df.columns for col in required_cols):
         print(f"❌ 错误：输入文件缺少必要的列: {required_cols}")
         sys.exit(1)

    # 3. 数据预处理
    # 将百分比字符串 "5.60%" 转换为数值 5.60 用于绘图
    # 先统一转为字符串处理，防止已有部分是数值类型报错
    df['Percentage_Str'] = df['Average_DEG_percentage'].astype(str)
    df['Percentage_Val'] = df['Percentage_Str'].str.replace('%', '', regex=False)
    # 处理可能出现的非数字情况（例如由 '0.00%' 转换来的 '0.00'）
    df['Percentage_Val'] = pd.to_numeric(df['Percentage_Val'], errors='coerce').fillna(0)

    # 按 BGC_Count 排序，让图例的顺序也比较整齐
    df = df.sort_values(by='BGC_Count', ascending=False)

    # 4. 创建画布
    # 【修改点2：图片宽一点】将宽度从12增加到16
    plt.figure(figsize=(16, 8))
    
    # 5. 绘制散点图
    # 【修改点1：散点颜色区分大一点】使用 'tab20' 色盘，专用于多分类高对比显示
    scatter = sns.scatterplot(
        data=df, 
        x='BGC_Count', 
        y='Percentage_Val', 
        hue='BGC_Type', 
        palette='tab20',  # 使用高对比度色盘
        s=250,            # 稍微加大点的大小
        edgecolor='k',    # 点的边框颜色改为黑色，增强对比
        linewidth=0.5,    # 边框宽度
        alpha=0.9         # 透明度
    )

    # 6. 为每个点添加标注 (BGC_Type)
    # 使用 adjust_text 库可以自动避让标签，但为了不引入新依赖，这里用简单的手动偏移
    # 如果标签重叠严重，建议安装 adjust_text 库并使用
    texts = []
    for i in range(df.shape[0]):
        # 只标注 BGC_Count > 1 的点，避免左下角过于拥挤（可选）
        # if df.iloc[i]['BGC_Count'] > 1: 
        plt.text(
            x=df.iloc[i]['BGC_Count'], 
            y=df.iloc[i]['Percentage_Val'], 
            s=df.iloc[i]['BGC_Type'],
            fontdict={'size': 9, 'color': 'black'},
            ha='center', va='bottom' # 文字对齐方式：水平居中，垂直靠底部（即在点上方）
        )

    # 7. 设置图表细节
    plt.title('BGC Type Distribution: Count vs Activity', fontsize=18, pad=20, fontweight='bold')
    plt.xlabel('BGC Count (Number of Clusters)', fontsize=14, labelpad=10)
    plt.ylabel('Average DEG Percentage (%)', fontsize=14, labelpad=10)
    
    # 设置坐标轴起点为 0，避免误导
    plt.ylim(bottom=0)
    plt.xlim(left=0)

    # 调整图例
    # move_legend 是 seaborn 0.11.2 版本后推荐的方法，更稳定
    try:
        sns.move_legend(
            scatter, "upper left",
            bbox_to_anchor=(1.02, 1), # 放在图表右侧外沿
            title='BGC Type',
            frameon=True, # 显示图例边框
            shadow=True   # 图例阴影
        )
    except AttributeError:
        # 旧版 seaborn 的兼容写法
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', title='BGC Type', frameon=True, shadow=True)
    
    # 8. 保存图片
    # 【修改点3：解决图注被裁】关键在于 bbox_inches='tight'
    try:
        # 使用 tight_layout 调整内部元素间距
        plt.tight_layout()
        # 保存时使用 bbox_inches='tight' 确保包含所有外部元素（如图例）
        plt.savefig(output_image, dpi=300, bbox_inches='tight')
        print(f"✅ 图片已成功保存至: {output_image}")
    except Exception as e:
        print(f"❌ 保存图片失败: {e}")
    finally:
        # 关闭画布释放内存
        plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="根据 BGC 类型统计数据绘制分布散点图 (改进版)")
    parser.add_argument("-i", "--input", required=True, help="输入汇总文件路径 (csv/xlsx)")
    parser.add_argument("-o", "--output", required=True, help="输出图片路径 (如 .png, .pdf, .jpg)")

    args = parser.parse_args()

    if os.path.exists(args.input):
        plot_bgc_distribution(args.input, args.output)
    else:
        print(f"❌ 错误：找不到文件 {args.input}")