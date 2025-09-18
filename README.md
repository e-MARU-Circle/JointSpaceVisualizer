# Joint Space Visualizer (3D Slicer Module)

## 概要

Joint Space Visualizer は 3D Slicer 用スクリプトモジュールです。2つのモデル（例: Mandible と Maxilla）間の最短距離を、VTK の `vtkDistancePolyDataFilter` を用いて計算し、結果をカラー表示します。

- 距離スカラー: “Distance” を結果モデルに付与（mm）
- カラーマップ: 0–5 mm 固定
  - 0–1.0 mm: 赤（フラット）
  - 1.0–2.5 mm: 赤→黄
  - 2.5–3.25 mm: 黄→緑
  - 3.25–4.0 mm: 緑→青
  - 4.0–5.0 mm: 青（フラット）
- 最小距離: Apply 実行後に UI 上へ表示

## 主な機能

- Load… ボタンから STL/PLY/VTP を直接読み込み、セレクタへ自動設定
- Decimation Options（`vtkQuadricDecimation`）でポリゴン削減（重いモデル対策）
- Display コントロール（Result/Target/Source の Show/Opacity を個別に設定）
- 固定スケールの表示（再現性を担保）と最小距離の表示

## 構成

- モジュール: `JointSpaceVisualizer/JointSpaceVisualizer.py`
- UI: `JointSpaceVisualizer/Resources/UI/JointSpaceVisualizer.ui`

## 導入（Additional Module Paths）

1. 3D Slicer を起動
2. Edit > Application Settings > Modules を開く
3. Additional Module Paths に、このリポジトリのモジュールフォルダを追加
   - 本リポジトリが単体の場合: リポジトリのルートパスを追加
     - 例: `/path/to/JointSpaceVisualizer`（この直下に `JointSpaceVisualizer.py` と `Resources/` がある構成）
   - 複数プロジェクトを含む親リポジトリにある場合: `.../JointSpaceVisualizer` ディレクトリを追加
4. Slicer を再起動

引数での指定例: `--additional-module-paths /path/to/JointSpaceVisualizer`

## 使い方

1. Maxilla / Mandible の行で、既存モデルを選択するか「Load…」で読み込み
2. （必要に応じて）Decimation を有効化し、削減率を設定
3. Apply を押下
4. Display セクションで Result / Target / Source の Show / Opacity を調整
5. Scale（固定）と Min Distance（mm）を参照

## 必要な Python ライブラリ

- 追加インストールは不要です（VTK 標準機能で計算・表示を行います）
- 補足（任意）: 以前の実装で利用していた `trimesh / rtree / scipy` は本モジュールの現行機能では不要です

## ヒント / トラブルシューティング

- 重いモデルで処理が遅い/フリーズする場合は、Decimation を有効にして削減率を上げてください（80–95% を目安に段階的に調整）
- 結果の距離マップが見えづらい場合は、Result を半透明（例: 30–60%）にし、他モデルの Show を切り替えて確認
- 結果ノード名は「Mandible名 + `_DistanceMap`」です

## ライセンス / 謝辞

研究・教育目的での利用を想定しています。3D Slicer コミュニティおよび関連 OSS に感謝します。
