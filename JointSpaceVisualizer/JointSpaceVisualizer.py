import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import logging
"""
起動時のモジュール読み込み失敗を避けるため、外部/重い依存は遅延インポートします。
trimesh / vtk / numpy_to_vtk は処理内で import します。
"""

#
# JointSpaceVisualizer
#

class JointSpaceVisualizer(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Joint Space Visualizer"
        self.parent.categories = ["Quantification"]
        self.parent.dependencies = []
        self.parent.contributors = ["Gemini (Google)"]
        self.parent.helpText = """
        This module calculates and visualizes the distance between two models (e.g., maxilla and mandible).
        The distance is displayed as a color map on the surface of one of the models.
        """
        self.parent.acknowledgementText = """
        This module was developed by Gemini.
        """

#
# JointSpaceVisualizerWidget
#

class JointSpaceVisualizerWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None
        self._resultNode = None

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        try:
            ui_path = self.resourcePath('UI/JointSpaceVisualizer.ui')
            uiWidget = slicer.util.loadUI(ui_path)
            self.layout.addWidget(uiWidget)
            self.ui = slicer.util.childWidgetVariables(uiWidget)
            uiWidget.setMRMLScene(slicer.mrmlScene)
            # Fallback resolution for nested widgets and ensure they are not None
            if not hasattr(self.ui, 'maxillaSelector') or self.ui.maxillaSelector is None:
                self.ui.maxillaSelector = slicer.util.findChild(uiWidget, 'maxillaSelector')
            if not hasattr(self.ui, 'mandibleSelector') or self.ui.mandibleSelector is None:
                self.ui.mandibleSelector = slicer.util.findChild(uiWidget, 'mandibleSelector')
            if not hasattr(self.ui, 'applyButton') or self.ui.applyButton is None:
                self.ui.applyButton = slicer.util.findChild(uiWidget, 'applyButton')
            # Display controls
            for name in (
                'resultVisibilityCheckBox','resultOpacitySlider',
                'maxillaVisibilityCheckBox','maxillaOpacitySlider',
                'mandibleVisibilityCheckBox','mandibleOpacitySlider',
                'minDistanceValueLabel','saveResultButton'):
                if not hasattr(self.ui, name) or getattr(self.ui, name) is None:
                    setattr(self.ui, name, slicer.util.findChild(uiWidget, name))
        except Exception as e:
            logging.error(f"Failed to load UI: {e}")
            # フォールバック: 最低限のUIを作る（Applyボタンのみ）
            import qt
            self.ui = type('UI', (), {})()
            self.ui.applyButton = qt.QPushButton('Apply')
            self.ui.applyButton.enabled = False
            self.layout.addWidget(self.ui.applyButton)

        self.logic = JointSpaceVisualizerLogic()

        # Ensure selectors allow None and hook scene explicitly
        try:
            if self.ui.maxillaSelector:
                self.ui.maxillaSelector.setMRMLScene(slicer.mrmlScene)
            if self.ui.mandibleSelector:
                self.ui.mandibleSelector.setMRMLScene(slicer.mrmlScene)
        except Exception as e:
            logging.warning(f"Selector setup warning: {e}")

        # Wire up signals
        self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
        if hasattr(self.ui, 'maxillaSelector') and self.ui.maxillaSelector:
            self.ui.maxillaSelector.currentNodeChanged.connect(self.onSelect)
        if hasattr(self.ui, 'mandibleSelector') and self.ui.mandibleSelector:
            self.ui.mandibleSelector.currentNodeChanged.connect(self.onSelect)
        # Optional file load buttons
        if hasattr(self.ui, 'maxillaLoadButton'):
            self.ui.maxillaLoadButton.connect('clicked(bool)', lambda _: self.onLoadModel(self.ui.maxillaSelector))
        if hasattr(self.ui, 'mandibleLoadButton'):
            self.ui.mandibleLoadButton.connect('clicked(bool)', lambda _: self.onLoadModel(self.ui.mandibleSelector))

        # Decimation options
        if hasattr(self.ui, 'enableDecimationCheckBox'):
            self.ui.enableDecimationCheckBox.connect('toggled(bool)', self.onEnableDecimation)
            # Set initial state of slider based on checkbox
            self.onEnableDecimation(self.ui.enableDecimationCheckBox.checked)

        # Observe scene changes to refresh state
        self.addObserver(slicer.mrmlScene, slicer.vtkMRMLScene.NodeAddedEvent, self._onSceneChanged)
        self.addObserver(slicer.mrmlScene, slicer.vtkMRMLScene.NodeRemovedEvent, self._onSceneChanged)

        self.onSelect()
        self._wireDisplayControls()
        self._syncDisplayControls()

    def cleanup(self):
        self.removeObservers()

    def onSelect(self):
        try:
            maxilla = self.ui.maxillaSelector.currentNode() if hasattr(self.ui, 'maxillaSelector') and self.ui.maxillaSelector else None
            mandible = self.ui.mandibleSelector.currentNode() if hasattr(self.ui, 'mandibleSelector') and self.ui.mandibleSelector else None
            self.ui.applyButton.enabled = bool(maxilla and mandible)
        except Exception as e:
            logging.warning(f"onSelect failed: {e}")
            self.ui.applyButton.enabled = False

    def onApplyButton(self):
        self.ui.applyButton.enabled = False
        slicer.app.processEvents()
        try:
            enable_decimation = self.ui.enableDecimationCheckBox.checked if hasattr(self.ui, 'enableDecimationCheckBox') else False
            decimation_value = float(self.ui.decimationSlider.value) if hasattr(self.ui, 'decimationSlider') else 0.0
            out = self.logic.process(
                self.ui.mandibleSelector.currentNode(),
                self.ui.maxillaSelector.currentNode(),
                enable_decimation,
                decimation_value / 100.0,
            )
            # Unpack result and min distance
            minDistance = None
            if isinstance(out, tuple):
                self._resultNode, minDistance = out
            else:
                self._resultNode = out
            if hasattr(self.ui, 'minDistanceValueLabel') and self.ui.minDistanceValueLabel:
                try:
                    self.ui.minDistanceValueLabel.text = (f"{float(minDistance):.2f}" if minDistance is not None else "-")
                except Exception:
                    self.ui.minDistanceValueLabel.text = "-"
            self._syncDisplayControls()
        except Exception as e:
            slicer.util.errorDisplay(f"An error occurred during processing: {e}")
            logging.error(f"Processing failed: {e}")
        finally:
            self.ui.applyButton.enabled = True

    def onEnableDecimation(self, checked):
        try:
            if hasattr(self.ui, 'decimationSlider') and self.ui.decimationSlider:
                self.ui.decimationSlider.enabled = bool(checked)
        except Exception as e:
            logging.warning(f"onEnableDecimation failed: {e}")

    def onLoadModel(self, combo: 'qMRMLNodeComboBox'):
        import qt
        import os
        fileTypes = "Model files (*.stl *.ply *.vtk *.vtp);;All files (*)"
        filePath = qt.QFileDialog.getOpenFileName(slicer.util.mainWindow(), 'Load Model', os.path.expanduser('~'), fileTypes)
        if not filePath:
            return
        try:
            node = slicer.util.loadNodeFromFile(filePath, 'ModelFile', {})
            if node:
                combo.setCurrentNodeID(node.GetID())
                self.onSelect()
        except Exception as e:
            slicer.util.errorDisplay(f"Failed to load model: {e}")

    def _onSceneChanged(self, caller, event, callData=None):
        self.onSelect()
        self._syncDisplayControls()

    # --- Display controls ---
    def _wireDisplayControls(self):
        try:
            if hasattr(self.ui, 'resultVisibilityCheckBox') and self.ui.resultVisibilityCheckBox:
                self.ui.resultVisibilityCheckBox.connect('toggled(bool)', self.onResultVisibilityToggled)
            if hasattr(self.ui, 'maxillaVisibilityCheckBox') and self.ui.maxillaVisibilityCheckBox:
                self.ui.maxillaVisibilityCheckBox.connect('toggled(bool)', self.onMaxillaVisibilityToggled)
            if hasattr(self.ui, 'mandibleVisibilityCheckBox') and self.ui.mandibleVisibilityCheckBox:
                self.ui.mandibleVisibilityCheckBox.connect('toggled(bool)', self.onMandibleVisibilityToggled)

            if hasattr(self.ui, 'resultOpacitySlider') and self.ui.resultOpacitySlider:
                self.ui.resultOpacitySlider.connect('valueChanged(double)', self.onResultOpacityChanged)
            if hasattr(self.ui, 'maxillaOpacitySlider') and self.ui.maxillaOpacitySlider:
                self.ui.maxillaOpacitySlider.connect('valueChanged(double)', self.onMaxillaOpacityChanged)
            if hasattr(self.ui, 'mandibleOpacitySlider') and self.ui.mandibleOpacitySlider:
                self.ui.mandibleOpacitySlider.connect('valueChanged(double)', self.onMandibleOpacityChanged)
            if hasattr(self.ui, 'saveResultButton') and self.ui.saveResultButton:
                self.ui.saveResultButton.connect('clicked(bool)', self.onSaveResult)
        except Exception as e:
            logging.warning(f"Display control wiring failed: {e}")

    # Slots for display controls
    def onResultVisibilityToggled(self, checked):
        self._setNodeVisibility(self._getResultNode(), bool(checked))

    def onMaxillaVisibilityToggled(self, checked):
        self._setNodeVisibility(self._getMaxillaNode(), bool(checked))

    def onMandibleVisibilityToggled(self, checked):
        self._setNodeVisibility(self._getMandibleNode(), bool(checked))

    def onResultOpacityChanged(self, v):
        try:
            self._setNodeOpacity(self._getResultNode(), float(v) / 100.0)
        except Exception as e:
            logging.warning(f"Result opacity change failed: {e}")

    def onMaxillaOpacityChanged(self, v):
        try:
            self._setNodeOpacity(self._getMaxillaNode(), float(v) / 100.0)
        except Exception as e:
            logging.warning(f"Maxilla opacity change failed: {e}")

    def onMandibleOpacityChanged(self, v):
        try:
            self._setNodeOpacity(self._getMandibleNode(), float(v) / 100.0)
        except Exception as e:
            logging.warning(f"Mandible opacity change failed: {e}")

    def _getMaxillaNode(self):
        try:
            return self.ui.maxillaSelector.currentNode() if hasattr(self.ui, 'maxillaSelector') and self.ui.maxillaSelector else None
        except Exception:
            return None

    def _getMandibleNode(self):
        try:
            return self.ui.mandibleSelector.currentNode() if hasattr(self.ui, 'mandibleSelector') and self.ui.mandibleSelector else None
        except Exception:
            return None

    def _getResultNode(self):
        if self._resultNode and slicer.mrmlScene.IsNodePresent(self._resultNode):
            return self._resultNode
        # Try to find by naming convention
        mandible = self._getMandibleNode()
        if mandible:
            result_name = f"{mandible.GetName()}_DistanceMap"
            try:
                return slicer.util.getNode(result_name)
            except Exception:
                return None
        return None

    def _setNodeVisibility(self, node, visible):
        if not node:
            return
        node.CreateDefaultDisplayNodes()
        dn = node.GetDisplayNode()
        if dn:
            dn.SetVisibility(1 if visible else 0)

    def _setNodeOpacity(self, node, opacity01):
        if not node:
            return
        node.CreateDefaultDisplayNodes()
        dn = node.GetDisplayNode()
        if dn:
            dn.SetOpacity(max(0.0, min(1.0, opacity01)))

    def _syncDisplayControls(self):
        # Enable controls based on node availability and reflect current state
        pairs = [
            (self._getResultNode(), 'resultVisibilityCheckBox', 'resultOpacitySlider'),
            (self._getMaxillaNode(), 'maxillaVisibilityCheckBox', 'maxillaOpacitySlider'),
            (self._getMandibleNode(), 'mandibleVisibilityCheckBox', 'mandibleOpacitySlider'),
        ]
        for node, chk, sld in pairs:
            checkbox = getattr(self.ui, chk, None)
            slider = getattr(self.ui, sld, None)
            hasNode = node is not None
            if checkbox:
                checkbox.enabled = hasNode
                if hasNode and node.GetDisplayNode():
                    checkbox.checked = bool(node.GetDisplayNode().GetVisibility())
            if slider:
                slider.enabled = hasNode
                if hasNode and node.GetDisplayNode():
                    slider.value = float(node.GetDisplayNode().GetOpacity()) * 100.0
        # Save button state
        if hasattr(self.ui, 'saveResultButton') and self.ui.saveResultButton:
            self.ui.saveResultButton.enabled = self._getResultNode() is not None

    def onSaveResult(self, *_):
        import qt, os
        node = self._getResultNode()
        if not node:
            slicer.util.infoDisplay('No result model to save yet. Please run Apply first.')
            return
        # Suggest a safe default (VTP preserves scalars). STL may drop scalars.
        defaultName = f"{node.GetName()}.vtp"
        filters = "VTP (*.vtp);;VTK (*.vtk);;PLY (*.ply);;STL (*.stl)"
        outPath = qt.QFileDialog.getSaveFileName(slicer.util.mainWindow(), 'Save Result Model', os.path.join(os.path.expanduser('~'), defaultName), filters)
        if not outPath:
            return
        try:
            ok = slicer.util.saveNode(node, outPath)
            if not ok:
                raise RuntimeError('saveNode returned False')
            # Warn if STL chosen (may not preserve scalars)
            if outPath.lower().endswith('.stl'):
                slicer.util.infoDisplay('Saved as STL. Note: STL does not store per-point scalars. Use VTP/VTK/PLY to preserve the Distance data.')
        except Exception as e:
            slicer.util.errorDisplay(f"Failed to save: {e}")

#
# JointSpaceVisualizerLogic
#

class JointSpaceVisualizerLogic(ScriptedLoadableModuleLogic):

    def polydata_to_trimesh(self, polydata):
        """Converts a vtkPolyData object to a trimesh.Trimesh object without PyVista."""
        import vtk
        from vtk.util.numpy_support import vtk_to_numpy
        import numpy as np

        # Ensure triangulated surface (handles polys/quads)
        tri = vtk.vtkTriangleFilter()
        tri.SetInputData(polydata)
        tri.PassLinesOff()
        tri.PassVertsOff()
        tri.Update()
        tri_poly = tri.GetOutput()

        # Points
        vtk_points = tri_poly.GetPoints()
        if vtk_points is None or vtk_points.GetNumberOfPoints() == 0:
            raise ValueError("Input polydata has no points")
        points = vtk_to_numpy(vtk_points.GetData())

        # Faces (vtkCellArray as [3, i0, i1, i2, 3, ...])
        vtk_polys = tri_poly.GetPolys()
        if vtk_polys is None or vtk_polys.GetNumberOfCells() == 0:
            raise ValueError("Input polydata has no polygons")
        faces_flat = vtk_to_numpy(vtk_polys.GetData())
        try:
            faces = faces_flat.reshape((-1, 4))[:, 1:4]
        except Exception:
            # Fallback: parse sequentially (robust to irregular cell sizes)
            faces = []
            i = 0
            n = faces_flat.size
            while i < n:
                cnt = int(faces_flat[i]); i += 1
                ids = faces_flat[i:i+cnt]; i += cnt
                if cnt == 3:
                    faces.append(ids)
                elif cnt > 3:
                    # fan triangulation
                    for k in range(1, cnt-1):
                        faces.append([ids[0], ids[k], ids[k+1]])
            faces = np.asarray(faces, dtype=np.int64)

        import trimesh
        return trimesh.Trimesh(vertices=points, faces=faces, process=False)

    def process(self, sourceNode, targetNode, enable_decimation=False, decimation_value=0.0):
        """
        Run the actual algorithm
        """
        # 遅延インポート（VTKのみ使用）
        import vtk

        if not sourceNode or not targetNode:
            logging.error("Input models are not valid.")
            return False

        logging.info(f"Source model: {sourceNode.GetName()}")
        logging.info(f"Target model: {targetNode.GetName()}")

        # 1. Get polydata from nodes
        logging.info("Preparing polydata...")
        source_polydata = sourceNode.GetPolyData()
        target_polydata = targetNode.GetPolyData()

        # Apply decimation if enabled
        if enable_decimation and decimation_value > 0.0:
            logging.info(f"Applying decimation to source model (target reduction: {decimation_value:.2f})...")
            decimate = vtk.vtkQuadricDecimation()
            decimate.SetInputData(source_polydata)
            decimate.SetTargetReduction(decimation_value)
            decimate.Update()
            source_polydata = decimate.GetOutput()

            logging.info(f"Applying decimation to target model (target reduction: {decimation_value:.2f})...")
            decimate = vtk.vtkQuadricDecimation()
            decimate.SetInputData(target_polydata)
            decimate.SetTargetReduction(decimation_value)
            decimate.Update()
            target_polydata = decimate.GetOutput()

        # Log mesh sizes
        try:
            sp = source_polydata.GetNumberOfPoints()
            tp = target_polydata.GetNumberOfPoints()
            sc = source_polydata.GetNumberOfCells()
            tc = target_polydata.GetNumberOfCells()
            logging.info(f"Source points/cells: {sp}/{sc}, Target points/cells: {tp}/{tc}")
        except Exception:
            pass

        # 2. Calculate distances using VTK (robust and memory-friendly)
        logging.info("Calculating distances with vtkDistancePolyDataFilter...")
        distFilter = vtk.vtkDistancePolyDataFilter()
        distFilter.SetInputData(0, source_polydata)
        distFilter.SetInputData(1, target_polydata)
        distFilter.SignedDistanceOff()  # unsigned distance
        distFilter.Update()

        result_polydata = distFilter.GetOutput()

        # 3. Create a new model node for the result
        logging.info("Creating result model...")
        result_name = f"{sourceNode.GetName()}_DistanceMap"
        # Check if a node with the same name exists and remove it
        old_node = None
        try:
            old_node = slicer.util.getNode(result_name)
        except Exception:
            old_node = None
        if old_node is not None:
            slicer.mrmlScene.RemoveNode(old_node)
        
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        sourceNodeID = shNode.GetItemByDataNode(sourceNode)
        parentItemID = shNode.GetItemParent(sourceNodeID)

        resultNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", result_name)
        resultNode.SetAndObservePolyData(result_polydata)
        shNode.SetItemParent(shNode.GetItemByDataNode(resultNode), parentItemID)

        # 4. Add color information (already added by the filter as 'Distance')
        logging.info("Distance scalars added by filter. Updating display...")

        # 5. Update the display to show the colors (custom R->Y->G->B, 0..5mm)
        logging.info("Updating display properties and color mapping (0-5mm, RYGB)...")
        resultNode.CreateDefaultDisplayNodes()
        displayNode = resultNode.GetDisplayNode()
        if displayNode:
            displayNode.SetScalarVisibility(True)
            displayNode.SetActiveScalarName("Distance")
            # Fix scalar range to 0-5mm
            try:
                displayNode.SetAutoScalarRange(0)
            except Exception:
                pass
            try:
                displayNode.SetScalarRange(0.0, 5.0)
            except Exception:
                pass

            # Create or reuse a procedural color node with 0..5 mapping
            # Updated thresholds: <=1.0mm stays RED, >=4.0mm stays BLUE
            try:
                colorNode = slicer.util.getNode('JSV_RYGB_0to5')
            except Exception:
                colorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLProceduralColorNode", "JSV_RYGB_0to5")
            ctf = colorNode.GetColorTransferFunction()
            ctf.RemoveAllPoints()
            # Keep red flat from 0 to 1.0 mm
            ctf.AddRGBPoint(0.0, 1.0, 0.0, 0.0)    # red
            ctf.AddRGBPoint(1.0, 1.0, 0.0, 0.0)    # red (flat until 1.0)
            # Transition through yellow and green between 1.0 and 4.0 mm
            ctf.AddRGBPoint(1.6, 1.0, 1.0, 0.0)    # yellow at 1.6 mm
            ctf.AddRGBPoint(3.25, 0.0, 1.0, 0.0)   # green
            # Clamp to blue from 4.0 mm upwards
            ctf.AddRGBPoint(4.0, 0.0, 0.0, 1.0)    # blue
            ctf.AddRGBPoint(5.0, 0.0, 0.0, 1.0)    # blue
            displayNode.SetAndObserveColorNodeID(colorNode.GetID())

        # Compute min distance (mm) from result scalars
        try:
            from vtk.util.numpy_support import vtk_to_numpy
            arr = result_polydata.GetPointData().GetArray('Distance')
            minDistance = float(vtk_to_numpy(arr).min()) if arr is not None else None
        except Exception:
            minDistance = None

        logging.info("Processing finished.")
        return resultNode, minDistance
