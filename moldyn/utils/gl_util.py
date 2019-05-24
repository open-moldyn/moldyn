import moderngl

def source(uri, consts={}):
    """
    Reads and replaces constants in a text file.

    Parameters
    ----------
    uri : str
        URI of the file to read.
    consts : dict
        Dictionary containing the values to replace.

    Returns
    -------

    str
        File contents with replacements

    """
    with open(uri, 'r') as fp:
        content = fp.read()

    # feed constant values
    for key, value in consts.items():
        content = content.replace(f"%%{key}%%", str(value))
    return content

def testMaxSizes():
    """
    Finds the maximum layout size for openGL compute shaders.

    Returns
    -------

    int
        Maximum layout size

    """
    context = moderngl.create_standalone_context(require=430)

    buffer_size = 1024 # garanti par la spec
    try:
        while True:
            context.compute_shader(source('./dummy.glsl', {"X":buffer_size}))
            buffer_size*=2
    except:
        pass

    return buffer_size//2

if __name__=="__main__":
    print("Taille maximale :",testMaxSizes())
