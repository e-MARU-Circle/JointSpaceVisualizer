import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import logging
"""
起動時のモジュール読み込み失敗を避けるため、外部/重い依存は遅延インポートします。
trimesh/pyvista/vtk/numpy_to_vtk は処理内で import します。
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

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        try:
            ui_path = self.resourcePath('UI/JointSpaceVisualizer.ui')
            uiWidget = slicer.util.loadUI(ui_path)
            self.layout.addWidget(uiWidget)
            self.ui = slicer.util.childWidgetVariables(uiWidget)
            uiWidget.setMRMLScene(slicer.mrmlScene)
        except Exception as e:
            logging.error(f"Failed to load UI: {e}")
            # フォールバック: 最低限のUIを作る（Applyボタンのみ）
            import qt
            self.ui = type('UI', (), {})()
            self.ui.applyButton = qt.QPushButton('Apply')
            self.ui.applyButton.enabled = False
            self.layout.addWidget(self.ui.applyButton)

        self.logic = JointSpaceVisualizerLogic()

        self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
        self.ui.maxillaSelector.currentNodeChanged.connect(self.onSelect)
        self.ui.mandibleSelector.currentNodeChanged.connect(self.onSelect)

        self.onSelect()

    def cleanup(self):
        self.removeObservers()

    def onSelect(self):
        self.ui.applyButton.enabled = self.ui.maxillaSelector.currentNode() and self.ui.mandibleSelector.currentNode()

    def onApplyButton(self):
        self.ui.applyButton.enabled = False
        slicer.app.processEvents()
        try:
            self.logic.process(self.ui.mandibleSelector.currentNode(),
                                 self.ui.maxillaSelector.currentNode())
        except Exception as e:
            slicer.util.errorDisplay(f"An error occurred during processing: {e}")
            logging.error(f"Processing failed: {e}")
        finally:
            self.ui.applyButton.enabled = True

#
# JointSpaceVisualizerLogic
#

class JointSpaceVisualizerLogic(ScriptedLoadableModuleLogic):

    def polydata_to_trimesh(self, polydata):
        """Converts a vtkPolyData object to a trimesh.Trimesh object."""
        import pyvista as pv
        pv_mesh = pv.wrap(polydata)
        # PyVista faces are in a flat array like [3, p0, p1, p2, 3, p3, p4, p5, ...]
        # We need to reshape it for trimesh
        faces = pv_mesh.faces.reshape((-1, 4))[:, 1:4]
        import trimesh
        return trimesh.Trimesh(vertices=pv_mesh.points, faces=faces)

    def process(self, sourceNode, targetNode):
        """
        Run the actual algorithm
        """
        # 遅延インポート
        import vtk
        from vtk.util.numpy_support import numpy_to_vtk
        import trimesh

        if not sourceNode or not targetNode:
            logging.error("Input models are not valid.")
            return False

        logging.info(f"Source model: {sourceNode.GetName()}")
        logging.info(f"Target model: {targetNode.GetName()}")

        # 1. Convert MRML nodes to trimesh objects
        logging.info("Converting Slicer models to trimesh objects...")
        source_polydata = sourceNode.GetPolyData()
        target_polydata = targetNode.GetPolyData()

        source_trimesh = self.polydata_to_trimesh(source_polydata)
        target_trimesh = self.polydata_to_trimesh(target_polydata)

        # 2. Calculate distances
        logging.info("Calculating closest point distances...")
        closest_points, distances, triangle_id = trimesh.proximity.closest_point(
            target_trimesh, source_trimesh.vertices)

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
        resultNode.SetAndObservePolyData(source_polydata)
        shNode.SetItemParent(shNode.GetItemByDataNode(resultNode), parentItemID)

        # 4. Add color information (scalars) to the new node
        logging.info("Adding distance data to the result model...")
        vtk_distances = numpy_to_vtk(num_array=distances, deep=True, array_type=vtk.VTK_DOUBLE)
        vtk_distances.SetName("Distance")
        resultNode.GetPolyData().GetPointData().SetScalars(vtk_distances)

        # 5. Update the display to show the colors
        logging.info("Updating display properties...")
        resultNode.CreateDefaultDisplayNodes()
        displayNode = resultNode.GetDisplayNode()
        if displayNode:
            displayNode.SetScalarVisibility(True)
            displayNode.SetActiveScalarName("Distance")
            # Use a default Slicer color map
            try:
                colorNode = slicer.util.getNode('Viridis')  # Slicer 5+
            except Exception:
                try:
                    colorNode = slicer.util.getNode('vtkMRMLColorTableNodeFileViridis.txt')
                except Exception:
                    colorNode = None
            if colorNode is not None:
                displayNode.SetAndObserveColorNodeID(colorNode.GetID())
            else:
                logging.warning("Could not find 'Viridis' color node.")

        logging.info("Processing finished.")
        return True
