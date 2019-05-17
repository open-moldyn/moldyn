#version 430

#define X %%X%%

layout (local_size_x=X, local_size_y=1, local_size_z=1) in;

layout (std430, binding=0) buffer in_0
{
    vec2 inxs[];
};

void main() {

}