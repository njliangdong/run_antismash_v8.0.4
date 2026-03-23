import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import argparse
import sys
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Spring布局强化版：标签居中且连线对比增强")
    parser.add_argument("-i", "--input", required=True, help="输入文件路径")
    parser.add_argument("-o", "--output", default="network_final_centered.png", help="输出图片文件名")
    parser.add_argument("-s", "--sep", default="\t", help="分隔符，默认为制表符")
    args = parser.parse_args()

    # 全局字体加粗配置
    plt.rcParams['font.weight'] = 'bold'
    plt.rcParams['axes.labelweight'] = 'bold'

    # 1. 读取数据
    try:
        df = pd.read_csv(args.input, sep=args.sep)
    except Exception as e:
        print(f"读取失败: {e}")
        sys.exit(1)

    # 计算全局权重范围，用于后续连线归一化
    all_weights = df['Pearson_r'].abs()
    min_w, max_w = all_weights.min(), all_weights.max()

    # 2. 构建图
    G = nx.Graph()
    for _, row in df.iterrows():
        G.add_edge(row['DEG_ID'], row['DEM_ID'], 
                   weight=abs(row['Pearson_r']), 
                   rel=row['Relationship'])
    
    genes = [n for n in G.nodes() if n in df['DEG_ID'].values]
    metabolites = [n for n in G.nodes() if n in df['DEM_ID'].values]

    # 3. 分连通分量布局
    components = list(nx.connected_components(G))
    num_components = len(components)
    
    # 动态画布大小：根据组件数量扩展
    fig_dimension = max(24, int(np.sqrt(num_components) * 12))
    fig, ax = plt.subplots(figsize=(fig_dimension, fig_dimension))
    
    all_pos = {}
    grid_size = int(np.ceil(np.sqrt(num_components)))
    
    # 组件间距步长
    step = 8.0 

    for i, nodes in enumerate(components):
        subgraph = G.subgraph(nodes)
        n_nodes = len(nodes)
        
        # --- 布局优化：强化斥力，为居中标签留空间 ---
        # 增加 k 值让节点散得更开
        local_k = 5.5 / np.sqrt(n_nodes) if n_nodes > 1 else 3.5
        local_scale = 1.0 + (np.sqrt(n_nodes) / 2.0) 
        
        pos_sub = nx.spring_layout(subgraph, 
                                   k=local_k, 
                                   scale=local_scale, 
                                   iterations=200, 
                                   seed=42)
        
        row_idx = i // grid_size
        col_idx = i % grid_size
        offset = np.array([col_idx * step, -row_idx * step])
        
        for node in pos_sub:
            all_pos[node] = pos_sub[node] + offset

    # 4. 绘图 (严格控制顺序)
    
    # A. 连线：显著的粗细差异
    for u, v, d in G.edges(data=True):
        color = 'red' if d['rel'] == 'Positive' else 'green'
        # 归一化算法：将相关系数映射到 1.5 到 9.0 的宽度
        norm = (d['weight'] - min_w) / (max_w - min_w) if max_w != min_w else 0.5
        width = 1.5 + (norm ** 2) * 7.5 
        ax.plot([all_pos[u][0], all_pos[v][0]], 
                [all_pos[u][1], all_pos[v][1]], 
                color=color, lw=width, alpha=0.25)

    # B. 基因节点 (稍微增大尺寸以包裹文字)
    nx.draw_networkx_nodes(G, all_pos, nodelist=genes, 
                           node_color='lightgrey', node_size=3200, 
                           edgecolors='black', linewidths=2.5, ax=ax, alpha=0.9)

    # C. 代谢物节点
    for m in metabolites:
        edge_data = list(G.edges(m, data=True))[0][2]
        m_color = 'red' if edge_data['rel'] == 'Positive' else 'green'
        nx.draw_networkx_nodes(G, all_pos, nodelist=[m], 
                               node_color=m_color, node_size=1200, 
                               edgecolors='white', linewidths=1.5, ax=ax, alpha=0.9)

    # 5. 标签处理：绝对正中心对齐
    for node, (x, y) in all_pos.items():
        is_gene = node in genes
        f_size = 13 if is_gene else 10
        
        # va='center' 和 ha='center' 确保文字在节点图形正中心
        ax.text(x, y, node, 
                fontsize=f_size, 
                fontweight='bold', 
                ha='center', 
                va='center',
                # 使用带透明度的 bbox 确保文字在复杂背景下依然清晰
                bbox=dict(facecolor='white', alpha=0.4, edgecolor='none', pad=0),
                zorder=10) # 确保文字处于最顶层

    # 6. 保存输出
    ax.set_title("DEG-DEM Network: Centered Labels & Weighted Edges", 
                 fontsize=40, fontweight='bold', pad=80)
    plt.axis('off')
    
    plt.savefig(args.output, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"成功完成！")
    print(f"1. 标签位置：已调整至节点图形正中心。")
    print(f"2. 节点间距：已通过强化斥力系数大幅拉开，防止重叠。")
    print(f"3. 连线对比：已根据 Pearson_r 绝对值完成显著粗细化。")

if __name__ == "__main__":
    main()