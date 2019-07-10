# -*-encoding: utf-8 -*-
import moderngl
import os

def source(uri, consts={}):
    """
    Reads and replaces constants (in all caps) in a text file.

    Parameters
    ----------
    uri : str
        URI of the file to read.
    consts : dict
        Dictionary containing the values to replace.

    Returns
    -------

    str
        File contents with replacements.

    """
    with open(uri, 'r') as fp:
        content = fp.read()

    # feed constant values
    for key, value in consts.items():
        content = content.replace(f"%%{key}%%".upper(), str(value))
    return content

def testGL():
    """
    Tries to initialize a compute shader.

    Returns
    -------

    bool
        Initialisation success.

    """
    f = source(os.path.dirname(__file__)+'/dummy.glsl', {"X":50})
    try:
        context = moderngl.create_standalone_context(require=430)
        context.compute_shader(f)
    except:
        return False
    else:
        return True
