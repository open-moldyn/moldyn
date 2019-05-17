// %%VARIABLE%% will be replaced with consts by python code

#version 430


#define BUFFER_SIZE %%BUFFER_SIZE%%
#define RCUT %%RCUT%%
#define EPSILON %%EPSILON%%
#define SIGMA %%SIGMA%%
#define SHIFTX %%SHIFTX%%
#define SHIFTY %%SHIFTY%%
#define LENGTHX %%LENGTHX%%
#define LENGTHY %%LENGTHY%%
#define V_PERIODIC %%V_PERIODIC%%
#define H_PERIODIC %%H_PERIODIC%%


layout (local_size_x=BUFFER_SIZE, local_size_y=1, local_size_z=1) in;

layout (std430, binding=0) buffer in_0
{
    vec2 inxs[];
};

layout (std430, binding=1) buffer in_1
{
    vec2 inxs2[];
};

layout (std430, binding=2) buffer out_0
{
    vec2 outfs[];
};


layout (std430, binding=3) buffer out_1
{
    float outes[];
};

layout (std430, binding=4) buffer out_2
{
    float outms[];
};

layout (std430, binding=5) buffer in_params
{
    uint inparams[];
};

float force(float dist) {
	const float p=pow(SIGMA/dist,6);
	return (-4.0*EPSILON*(6.0*p-12.0*p*p))/(dist*dist);
}

float energy(float dist) {
	const float p=pow(SIGMA/dist,6);
	return EPSILON*(4.0*(p*p-p)+127.0/4096.0);
}

void main()
{
	const int x = int(gl_GlobalInvocationID.x);
	const vec2 pos = inxs[x];

	uint itermax = min(BUFFER_SIZE,inparams[3]);

	if(x < inparams[2]) {

		vec2 f = vec2(0.0, 0.0);
		float e = 0.0;
		float m = 0.0;

		for (int i=0;i<itermax;i++) {
			if (inparams[0]!=inparams[1] || i!=x) {
				vec2 distxy = pos - inxs2[i];

				#if V_PERIODIC
					if (distxy.x<(-SHIFTX)) {
						distxy.x += LENGTHX;
					}
					if (distxy.x>SHIFTX) {
						distxy.x -= LENGTHX;
					}
				#endif

				#if H_PERIODIC
					if (distxy.y<(-SHIFTY)) {
						distxy.y += LENGTHY;
					}
					if (distxy.y>SHIFTY) {
						distxy.y -= LENGTHY;
					}
				#endif

				float dist = length(distxy);
				if (dist<RCUT) {
					f += force(dist)*distxy;
					e += energy(dist);
					m += 1.0;
				}
			}
		}

		outfs[x] = f;
		outes[x] = e;
		outms[x] = m;
	}
}