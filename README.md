# Joint Space Visualizer (3D Slicer Module)

## 概要

このリポジトリは「3D Slicer」向けのスクリプトモジュール Joint Space Visualizer を提供します。
2つのモデル（例: 下顎骨と上顎骨）間の最短距離を計算し、Sourceモデルに“Distance”スカラーとして付与、Viridis カラーマップで可視化します。

## 構成

- モジュール本体: `JointSpaceVisualizer/JointSpaceVisualizer.py`
- UIファイル: `JointSpaceVisualizer/Resources/UI/JointSpaceVisualizer.ui`

スタンドアロン実行用スクリプトや仮想環境、重複したモジュールは削除済みです。

## 導入（追加モジュールパスの設定）

1. 3D Slicer を起動
2. Edit > Application Settings > Modules を開く
3. Additional Module Paths に、このリポジトリ内の `JointSpaceVisualizer` フォルダを追加
   - 正: `/path/to/JointSpaceVisualizer`
   - 注意: 親ディレクトリではなく、`.py` が直下にあるフォルダを指定してください
4. Slicer を再起動

もしくは、Slicer起動時に引数で指定: `--additional-module-paths /path/to/JointSpaceVisualizer`

## 使い方（Slicer内）

- モジュール: “Joint Space Visualizer”
- 入力: Source（距離を付与するモデル）, Target（参照モデル）
- 操作: モデルを選択し「Apply」を押下 → Sourceモデルの表示に“Distance”スカラーが追加され、Viridisで着色されます。

## 依存関係について

距離計算に `trimesh` を使用しています。Slicer の Python で未導入の場合は、Slicer の Python インタラクタから以下を実行してください。

```python
slicer.util.pip_install('trimesh rtree scipy')
```

注: メッシュ変換は VTK ネイティブ実装に変更済みのため、`pyvista` は不要です。

## ライセンス / 謝辞

研究・教育目的での利用を想定しています。3D Slicer コミュニティおよび関連OSSに感謝します。
