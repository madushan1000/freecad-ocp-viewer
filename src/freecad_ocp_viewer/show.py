# Most of the code in this file are taken from https://github.com/bernhard-42/vscode-ocp-cad-viewer, https://github.com/CadQuery/cadquery, and https://github.com/CadQuery/CQ-editor
# So this specific file is licensed under Apache-2.0 license

from io import BytesIO
from typing_extensions import TypeIs

import numpy as np
import OCP
from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import (
    BRepAdaptor_Curve,
)
from OCP.GeomAbs import GeomAbs_CurveType
from OCP.gp import (
    gp_Ax1,
    gp_Pln,
    gp_Vec,
)
from OCP.Quantity import Quantity_ColorRGBA 

from OCP.TopLoc import TopLoc_Location

# Bounding Box
from OCP.TopoDS import (
    TopoDS,
    TopoDS_Compound,
    TopoDS_CompSolid,
    TopoDS_Edge,
    TopoDS_Face,
    TopoDS_Shape,
    TopoDS_Shell,
    TopoDS_Solid,
    TopoDS_Vertex,
    TopoDS_Wire,
)


def get_brep(object):
    brep_stream = BytesIO()

    cadquery_object = unwrap_cadquery_object(object)
    if cadquery_object != None:
        return

    build123d_object = unwrap_build123d_object(object)
    if build123d_object != None:
        from build123d import export_brep
        export_brep(build123d_object, brep_stream)
        return brep_stream
    
    raise Exception("unsupported object type", object)

def unwrap_cadquery_object(obj):

    if (
        is_cadquery(obj) 
        or is_cadquery_shape(obj) 
        or is_cadquery_assembly(obj) 
        or is_cadquery_massembly(obj) 
        or is_cadquery_sketch(obj)
        or is_cadquery_empty_workplane(obj)
        or is_vector(obj)
        or is_massembly(obj)):
        return obj
    return None


def unwrap_build123d_object(obj):

    if is_build123d(obj):
        return getattr(obj, getattr(obj, "_obj_name"))

    if (
        is_build123d_part(obj)
        or is_build123d_sketch(obj)
        or is_build123d_line(obj)
        or is_build123d_shape(obj)
        or is_build123d_shell(obj)
        or is_build123d_compound(obj)
        or is_build123d_assembly(obj)
        or is_build123d_shapelist(obj)
        or is_build123d_locationlist(obj)
        or is_build123d_plane(obj)
        or is_build123d_location(obj)
        or is_build123d_axis(obj)):
        return obj
    return None

#From https://github.com/bernhard-42/ocp-tessellate/blob/ebc09d3f7a0797ac62e45c73c6cbe2c4057f2106/ocp_tessellate/ocp_utils.py#L245 Apache 2
def _has(obj, attrs):
    return all([hasattr(obj, a) for a in attrs])

def is_cadquery(obj):
    return _has(obj, ["objects", "ctx", "val"])

def is_cadquery_shape(obj):
    return _has(obj, ["wrapped", "forConstruction"]) and is_topods_shape(obj.wrapped)


def is_cadquery_assembly(obj):
    return _has(obj, ["obj", "loc", "name", "children"])


def is_cadquery_massembly(obj):
    return _has(obj, ["obj", "loc", "name", "children", "mates"])


def is_cadquery_sketch(obj):
    return (
        hasattr(obj, "_faces") and hasattr(obj, "_edges") and hasattr(obj, "_selection")
    )


def is_cadquery_empty_workplane(obj):
    return is_cadquery(obj) and len(obj.objects) == 0

    # (len(obj.objects) == 0 or (len(obj.objects) == 1 and is_vector(obj.objects[0])))


def is_vector(obj):
    return hasattr(obj, "wrapped") and isinstance(obj.wrapped, gp_Vec)


def is_massembly(obj):
    return _has(obj, ["obj", "loc", "name", "children", "mates"])


def is_wrapped(obj):
    return hasattr(obj, "wrapped")


def is_build123d(obj):
    return _has(obj, ["_obj", "_obj_name", "_tag"]) and not isinstance(obj, type)


def is_build123d_part(obj):
    return is_build123d(obj) and obj._obj_name == "part"


def is_build123d_sketch(obj):
    return is_build123d(obj) and obj._obj_name == "sketch"


def is_build123d_line(obj):
    return is_build123d(obj) and obj._obj_name == "line"


def is_build123d_shape(obj):
    return _has(obj, ["wrapped", "children"]) and is_topods_shape(obj.wrapped)


def is_build123d_shell(obj):
    return hasattr(obj, "wrapped") and is_topods_shell(obj.wrapped)


def is_build123d_compound(obj):
    return hasattr(obj, "wrapped") and is_topods_compound(obj.wrapped)


def is_build123d_assembly(obj):
    return (
        (is_build123d_compound(obj) or is_build123d_shape(obj))
        and hasattr(obj, "children")
        and isinstance(obj.children, (list, tuple))
        and len(obj.children) > 0
        # and (
        #     (len(obj.children) == 0 and obj.parent is not None)
        #     or (len(obj.children) > 0 and obj.parent is None)
        # )
    )


def is_build123d_shapelist(obj):
    return (
        isinstance(obj, Iterable)
        and hasattr(obj, "first")
        and hasattr(obj, "last")
        and hasattr(obj, "filter_by")
    )


def is_build123d_locationlist(obj):
    return (
        isinstance(obj, Iterable)
        and hasattr(obj, "locations")
        and hasattr(obj, "__enter__")
        and hasattr(obj, "__exit__")
    )


def is_build123d_plane(obj):
    return is_wrapped(obj) and is_gp_plane(obj.wrapped)


def is_build123d_location(obj):
    return is_wrapped(obj) and is_toploc_location(obj.wrapped)


def is_build123d_axis(obj):
    return is_wrapped(obj) and is_gp_axis(obj.wrapped)


#
# %% Shape identifiers on OCP level
#


def is_topods_shape(topods_shape):
    return isinstance(topods_shape, TopoDS_Shape)


def is_topods_compound(topods_shape):
    return isinstance(topods_shape, TopoDS_Compound)


def is_topods_compsolid(topods_shape):
    return isinstance(topods_shape, TopoDS_CompSolid)


def is_topods_solid(topods_shape):
    return isinstance(topods_shape, TopoDS_Solid)


def is_topods_shell(topods_shape):
    return isinstance(topods_shape, TopoDS_Shell)


def is_topods_face(topods_shape):
    return isinstance(topods_shape, TopoDS_Face)


def is_topods_wire(topods_shape):
    return isinstance(topods_shape, TopoDS_Wire)


def is_topods_edge(topods_shape):
    return isinstance(topods_shape, TopoDS_Edge)


def is_topods_vertex(topods_shape):
    return isinstance(topods_shape, TopoDS_Vertex)


def is_line(topods_shape):
    c = BRepAdaptor_Curve(topods_shape)
    return c.GetType() == GeomAbs_CurveType.GeomAbs_Line


def is_degenerated_edge(edge: TopoDS_Edge) -> bool:
    """
    Detect OCCT artifact edges: flagged degenerated or carrying no 3D curve.
    Both checks are O(1); constructing a BRepAdaptor_Curve on such an edge
    would raise "BRepAdaptor_Curve::No geometry".
    """
    if BRep_Tool.Degenerated_s(edge):
        return True
    loc = TopLoc_Location()
    return BRep_Tool.Curve_s(edge, loc, 0.0, 0.0) is None


def is_degenerated_face(face: TopoDS_Face) -> bool:
    """
    Detect OCCT artifact faces carrying no surface (O(1)). Zero-area faces
    with a valid surface are not caught here on purpose - computing the area
    is expensive, and the mesher drops them for free (no triangulation).
    """
    return BRep_Tool.Surface_s(face) is None


def is_toploc_location(obj) -> TypeIs[TopLoc_Location]:
    return isinstance(obj, TopLoc_Location)


def is_gp_plane(obj) -> TypeIs[gp_Pln]:
    return isinstance(obj, gp_Pln)


def is_gp_axis(obj) -> TypeIs[gp_Ax1]:
    return isinstance(obj, gp_Ax1)


def is_gp_vec(obj) -> TypeIs[gp_Vec]:
    return isinstance(obj, gp_Vec)

