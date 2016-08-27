import sys
import getopt
import itertools

from mathutils import Matrix

from bpy import ops, context
from bpy.props import FloatProperty
from io_curve_svg import import_svg
from io_mesh_stl import stl_utils, blender_utils
from bpy_extras.io_utils import axis_conversion

# Note: this script extrudes an svg and converts it to a stl file
# it depends on the blender addons io_curve_svg and io_mesh_stl
# blender units get converted to millimeters
# tested on Blender 2.77

def run(extrude_height=10.0, input_file="input.svg", output_file='output.stl', max_dimension=None):
    # clear the default scene
    ops.object.select_by_type(type='MESH')
    ops.object.delete(use_global=True)

    # load the svg file
    import_svg.load_svg(input_file)
    context.scene.objects.active = context.scene.objects['Curve']
    ops.object.select_by_type(type='CURVE')
    ops.object.convert(target='MESH')

    # if it includes an argument, scale to the appropriate maximum size
    if(max_dimension):
        current_max = max(context.object.dimensions)
        scale_factor = max_dimension/current_max
        context.object.scale *= scale_factor

    # enter edit mode to modify the mesh
    ops.object.editmode_toggle()

    # select the edges
    ops.mesh.select_non_manifold()

    # fill in the surface
    ops.mesh.fill()

    # now that everything is set up, run the extrude function
    ops.mesh.extrude_region_move(
        MESH_OT_extrude_region={"mirror":False},
        TRANSFORM_OT_translate={"value":(0, -0, -extrude_height),
        "constraint_axis":(False, False, True),
        "constraint_orientation":'NORMAL',
        "mirror":False,
        "proportional":'DISABLED',
        "proportional_edit_falloff":'SMOOTH',
        "proportional_size":1,
        "snap":False,
        "snap_target":'CLOSEST',
        "snap_point":(0, 0, 0),
        "snap_align":False,
        "snap_normal":(0, 0, 0),
        "gpencil_strokes":False,
        "texture_space":False,
        "remove_on_cancel":False,
        "release_confirm":False}
    )

    # exit edit mode
    ops.object.editmode_toggle()

    # recenter the object's geometry and place it in the center
    ops.object.origin_set(type='ORIGIN_GEOMETRY')
    context.object.location[0] = 0
    context.object.location[1] = 0
    context.object.location[2] = extrude_height/2

    # call the export function
    export(output_file)


def export(filepath, use_mesh_modifiers=True, batch_mode='OFF'):
    global_matrix = axis_conversion(to_forward='Y',
                                    to_up='Z',
                                    ).to_4x4() * Matrix.Scale(1.0, 4)

    if batch_mode == 'OFF':
        faces = itertools.chain.from_iterable(
                blender_utils.faces_from_mesh(ob, global_matrix, use_mesh_modifiers)
                for ob in context.scene.objects)

        stl_utils.write_stl(faces=faces, filepath=filepath)
    elif batch_mode == 'OBJECT':
        prefix = os.path.splitext(filepath)[0]
        for ob in context.scene.objects:
            faces = blender_utils.faces_from_mesh(ob, global_matrix, use_mesh_modifiers)
            stl_utils.write_stl(faces=faces, filepath=filepath)

def main(argv):
    inputfile = ''
    outputfile = ''
    extrude_height_in_mm = 10.0
    max_size_in_mm = None
    try:
        opts, args = getopt.getopt(argv,"hi:o:s:x:",["ifile=","ofile=","max_size_in_mm=","extrude_height_in_mm"])
    except getopt.GetoptError:
        print('OPT ERROR | usage: blender --python extrude.py -i <inputfile>.svg -o <outputfile>.stl -x <extrude_height_in_mm> -s <max_size_in_mm>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('usage: blender --python extrude.py -i <inputfile>.svg -o <outputfile>.stl -x <extrude_height_in_mm> -s <max_size_in_mm>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-x", "--extrude_height_in_mm"):
            extrude_height_in_mm = float(arg)
        elif opt in ("-s", "--max_size_in_mm"):
            max_size_in_mm = float(arg)
        print('Input file is %s' % inputfile)
        print('Output file is %s' % outputfile)

    if(inputfile != '' and outputfile != ''):
       run(input_file=inputfile, extrude_height=extrude_height_in_mm, max_dimension=max_size_in_mm, output_file=outputfile)

if (__name__ == '__main__'):
    # usage: blender --python extrude.py -- -i inputfile.svg -o outputfile.stl -m 50
    # skip the first four args (blender ignores args after -- )
    main(sys.argv[4:])
    sys.exit()
