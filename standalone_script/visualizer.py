import trimesh
import numpy as np
import pyvista as pv
import matplotlib
from matplotlib.colors import Normalize
import os
import argparse

def visualize_distance(mesh_a_path, mesh_b_path, output_ply_path=None, show_viewer=True):
    """
    メッシュAの各頂点からメッシュBの最も近い点までの距離を計算し、
    その距離に基づいてメッシュAを色付けして可視化します。

    Args:
        mesh_a_path (str): 最初のSTLファイルのパス（例: 下顎骨）
        mesh_b_path (str): 2番目のSTLファイルのパス（例: 上顎骨）
        output_ply_path (str, optional): 指定された場合、色付けされたメッシュをPLYファイルとして保存します。
        show_viewer (bool): Trueの場合、インタラクティブなビューアーを起動します。
    """
    print("メッシュを読み込んでいます...")
    try:
        mesh_a = trimesh.load(mesh_a_path)
        mesh_b = trimesh.load(mesh_b_path)
    except Exception as e:
        print(f"メッシュの読み込み中にエラーが発生しました: {e}")
        return

    print("最近傍点間の距離を計算しています...")
    closest_points, distances, triangle_id = trimesh.proximity.closest_point(mesh_b, mesh_a.vertices)

    print("カラーマップを適用しています...")
    try:
        cmap = matplotlib.colormaps.get_cmap('viridis_r')
    except AttributeError:
        # Matplotlib 3.7以前のフォールバック
        cmap = matplotlib.cm.get_cmap('viridis_r')
    norm = Normalize(vmin=np.min(distances), vmax=np.max(distances))
    colors = (cmap(norm(distances))[:, :3] * 255).astype(np.uint8)

    colored_mesh_a = mesh_a.copy()
    colored_mesh_a.visual.vertex_colors = colors

    if output_ply_path:
        output_dir = os.path.dirname(output_ply_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        print(f"色付けされたメッシュを {output_ply_path} に保存しています...")
        colored_mesh_a.export(output_ply_path)

    if show_viewer:
        print("ビューアーを起動します...")
        plotter = pv.Plotter(window_size=[1024, 768])
        plotter.add_text("Joint Space Visualization", font_size=15)
        pv_mesh_a = pv.wrap(colored_mesh_a)
        pv_mesh_b = pv.wrap(mesh_b)
        plotter.add_mesh(pv_mesh_a, scalars=distances, cmap='viridis_r', scalar_bar_args={'title': 'Distance (mm)'})
        plotter.add_mesh(pv_mesh_b, color='white', opacity=0.4, style='surface')
        print("ビューアーウィンドウを閉じて終了します。")
        plotter.show()
    else:
        print("ビューアーは無効です。処理を完了しました。")

def create_and_visualize_dummy_data(show_viewer=True):
    """2つの単純な形状を作成し、距離を可視化します。"""
    print("テスト用のダミーデータ（球と箱）を作成しています...")
    sphere = trimesh.creation.icosphere(subdivisions=4, radius=0.8)
    sphere.apply_translation([0, 0, 1.5])
    box = trimesh.creation.box(extents=[3, 3, 0.5])

    temp_dir = "temp_data"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    sphere_path = os.path.join(temp_dir, "temp_sphere.stl")
    box_path = os.path.join(temp_dir, "temp_box.stl")
    sphere.export(sphere_path)
    box.export(box_path)

    print("\n--- ダミーデータで可視化を実行します ---")
    visualize_distance(sphere_path, box_path, os.path.join("output", "colored_sphere.ply"), show_viewer=show_viewer)

    print("一時ファイルをクリーンアップしています...")
    os.remove(sphere_path)
    os.remove(box_path)
    os.rmdir(temp_dir)
    print("クリーンアップ完了。")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='2つのメッシュ間の距離を計算し、色付けして可視化します。',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('mesh_a', nargs='?', default=None, 
                        help='距離を測定するベースとなるSTLファイル（例: 下顎骨）')
    parser.add_argument('mesh_b', nargs='?', default=None, 
                        help='距離のターゲットとなるSTLファイル（例: 上顎骨）')
    parser.add_argument('-o', '--output', type=str, default=None, 
                        help="""
色付けしたモデルの出力先PLYファイルパス。
指定しない場合、入力ファイル名に基づいて自動生成されます。
""" ) 
    parser.add_argument('--no-viewer', action='store_true', 
                        help='インタラクティブなビューアーを起動しません。')
    parser.add_argument('--sample', action='store_true', 
                        help='引数を無視し、サンプルデータ（球と箱）で実行します。')

    args = parser.parse_args()

    show_viewer = not args.no_viewer

    if args.sample:
        create_and_visualize_dummy_data(show_viewer=show_viewer)
    elif args.mesh_a and args.mesh_b:
        if not os.path.exists(args.mesh_a):
            print(f"エラー: 入力ファイルが見つかりません: {args.mesh_a}")
        elif not os.path.exists(args.mesh_b):
            print(f"エラー: 入力ファイルが見つかりません: {args.mesh_b}")
        else:
            output_path = args.output
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(args.mesh_a))[0]
                output_path = os.path.join("output", f"colored_{base_name}.ply")
                print(f"出力パスが指定されていません。デフォルトのパスを使用します: {output_path}")
            
            visualize_distance(args.mesh_a, args.mesh_b, output_path, show_viewer=show_viewer)
    else:
        print("処理を開始できません。入力ファイルを指定するか、--sampleオプションを使用してください。")
        parser.print_help()
