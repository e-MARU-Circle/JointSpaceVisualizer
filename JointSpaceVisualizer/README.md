# Joint Space Visualizer (3D Slicer Module)

## Overview

Joint Space Visualizer is a 3D Slicer scripted module to compute the closest surface distance between two models (e.g., Mandible and Maxilla) using VTK's `vtkDistancePolyDataFilter`, and visualize it as a color map.

- Distance scalar: stored as point data array "Distance" (mm)
- Color map: fixed 0–5 mm
  - 0–1.0 mm: Red (flat)
  - 1.0–2.5 mm: Red → Yellow
  - 2.5–3.25 mm: Yellow → Green
  - 3.25–4.0 mm: Green → Blue
  - 4.0–5.0 mm: Blue (flat)
- Min distance: displayed in the UI after Apply

## Features

- Load… buttons to import STL/PLY/VTP from disk
- Decimation Options (VTK `vtkQuadricDecimation`) to reduce mesh size
- Display controls: per-node Show/Opacity (Result, Target, Source)
- Fixed scale readout and min distance value (reproducible)

## Layout

- Module: `JointSpaceVisualizer/JointSpaceVisualizer.py`
- UI: `JointSpaceVisualizer/Resources/UI/JointSpaceVisualizer.ui`

## Installation (Additional Module Paths)

1. Open 3D Slicer
2. Edit > Application Settings > Modules
3. Add this repository root as Additional Module Path
   - Example: `/path/to/JointSpaceVisualizer`
4. Restart Slicer

Command-line example: `--additional-module-paths /path/to/JointSpaceVisualizer`

## Usage

1. Pick or Load… Target (Maxilla) and Source (Mandible)
2. Optionally enable Decimation and set reduction
3. Click Apply
4. Adjust Display (Show/Opacity) for Result/Target/Source
5. Verify Scale (fixed) and Min Distance (mm)

## Python Dependencies

- None required. The module uses VTK built-ins for computation and display.
- Note: Legacy code paths using `trimesh/rtree/scipy` are not used by the current implementation.

## Tips / Troubleshooting

- If processing is slow or runs out of memory, enable Decimation (try 80–95%).
- If visibility seems off, make Result semi-transparent and toggle Target/Source visibility.
- Result node is named `<MandibleName>_DistanceMap`.

