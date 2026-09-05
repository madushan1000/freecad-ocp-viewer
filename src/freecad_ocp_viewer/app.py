import traceback
import sys
import runpy
import builtins
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, Signal, QThread, QMetaObject, Qt, Q_ARG, Slot, QDir, QMetaMethod
from PySide6.QtWidgets import QApplication

import FreeCADGui
import FreeCAD
from Part import Shape as PartShape

from .show import get_brep

class ReloadWorker(QObject):
    send_shape = Signal(object)
    done_seding = Signal()

    @Slot(str)
    def init_worker(self, main_file: str):
        self.main_file = Path(main_file).resolve()
        self.project_root = self.main_file.parent
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.fileChanged.connect(self.handle_file_change)
        builtins.show_object = self.show_object
        self.load_file()

    def show_object(self, object, label = None):
        brep = get_brep(object)
        bhash = '_' + str(abs(hash(brep.getvalue())))
        label = bhash if label == None else label
        breps = [{"hash": bhash, "label": label, "brep": brep}]
        self.send_shape.emit(breps)

    def handle_file_change(self, path):
        if path not in self.file_watcher.files() and Path(path).resolve().exists():
            self.file_watcher.addPath(path)
            return
        self.load_file()

    def load_file(self):
        #print(self.file_watcher.files())
        self.clear_local_modules()
        self.file_watcher.addPath(str(self.main_file))
        old_modules = self.get_module_attrs(sys.modules)
        sys.path.insert(0, str(self.project_root))
        try:
            runpy.run_path(str(self.main_file), run_name="__main__",)# init_globals={"show_object": self.show_object})
            self.done_seding.emit()
        except Exception:
            traceback.print_exc()
        sys.path.pop(0)
        new_modules = self.get_module_attrs(sys.modules)
        self.unwatch_removed_modules(old_modules - new_modules)
        self.watch_new_modules(new_modules - old_modules)

    def get_module_attrs(self, modules):
        module_pairs = set()
        for module_name, module in modules.items(): 
            module_file = getattr(module, "__file__", None)
            if  module_file != None:
                module_pairs.add((module_name, module_file))
        return module_pairs

    def watch_new_modules(self, modules):
        for _, module_file in modules:
            module_file = Path(module_file)
            if module_file.is_relative_to(self.project_root)and not module_file.is_relative_to(self.project_root.joinpath(".venv")):
                self.file_watcher.addPath(str(module_file))

    def unwatch_removed_modules(self, modules):
        for _, module_file in modules:
            module_file = Path(module_file)
            if module_file.is_relative_to(self.project_root):
                self.file_watcher.removePath(str(module_file))

    def clear_local_modules(self):
        for module_name, module in sys.modules.copy().items():
            orig_module_file = getattr(module, "__file__", None)
            if orig_module_file != None: 
                module_file = Path(orig_module_file)
                if module_file.is_relative_to(self.project_root) and not module_file.is_relative_to(self.project_root.joinpath(".venv")):
                    del sys.modules[module_name]


class FreeCADOcpViewer(QApplication):
    def __init__(self, main_file, argv):
        super().__init__(argv)

        QDir.addSearchPath('qss', FreeCAD.ConfigGet('AppHomePath') + '/share/Gui/Stylesheets')
        FreeCADGui.showMainWindow()

        self.project_name = Path().cwd().name
        self.part_names = set()
        self.worker_thread = QThread()
        self.reload_worker = ReloadWorker()
        self.reload_worker.moveToThread(self.worker_thread)
        self.worker_thread.start()
        self.worker_thread.finished.connect(self.reload_worker.deleteLater)
        FreeCADGui.getMainWindow().mainWindowClosed.connect(self.worker_thread.quit)
        QMetaObject.invokeMethod(
            self.reload_worker, 
            "init_worker", 
            Qt.ConnectionType.QueuedConnection, Q_ARG(str, str(main_file)))
        self.reload_worker.send_shape.connect(self.create_shape)
        self.reload_worker.done_seding.connect(self.handle_cleanup)

    def create_shape(self, breps):
        doc = self.ensure_document()
        for item in breps:
            self.ensure_part(doc, item)
            doc.recompute()

    
    def ensure_part(self, doc, item):
        self.part_names.add(item['hash'])
        parts = doc.findObjects('Part::Feature', Name = item['hash'])
        if len(parts) > 0:
            parts[0].Label = item['label']
            return
        parts = doc.findObjects('Part::Feature', Label = item['label'])
        if len(parts) > 0:
            for part in parts:
                if part.Label == item['label']:
                    doc.removeObject(part.Name)

        part_shape = PartShape()
        obj = doc.addObject("Part::Feature", item['hash'])
        obj.Label = item['label']
        obj.addProperty('App::PropertyString', 'ManagedBy')
        obj.ManagedBy = "FreeCADOcpViewer"
        part_shape.importBrepFromString(item['brep'].getvalue().decode('utf-8'))
        obj.Shape = part_shape
        return  part_shape

    def ensure_document(self):
        doc = FreeCAD.listDocuments().get(self.project_name)
        if doc == None:
            doc = FreeCAD.newDocument(self.project_name)
        return doc

    def handle_cleanup(self):
        doc = self.ensure_document()
        parts = doc.findObjects("Part::Feature")
        for part in parts:
            if getattr(part, "ManagedBy", None) == "FreeCADOcpViewer" and part.Name not in self.part_names :
                doc.removeObject(part.Name)
        self.part_names.clear()
        doc.recompute()

