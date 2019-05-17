import moderngl

def source(uri, consts):
    ''' read gl code '''
    with open(uri, 'r') as fp:
        content = fp.read()

    # feed constant values
    for key, value in consts.items():
        content = content.replace(f"%%{key}%%", str(value))
    return content

def testMaxSizes(data_size=8):
    context = moderngl.create_standalone_context(require=430)

    buffer_size = 512
    try:
        while True:
            context.compute_shader(source('./dummy.glsl', {"X":buffer_size}))
            context.buffer(reserve=data_size*buffer_size)
            buffer_size*=2
    except:
        pass

    return buffer_size//2

if __name__=="__main__":
    print("Taille maximale :",testMaxSizes())
