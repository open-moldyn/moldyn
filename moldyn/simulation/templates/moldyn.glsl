// %%VARIABLE%% will be replaced with consts by python code

#version 430


#define LAYOUT_SIZE %%LAYOUT_SIZE%%
#define NPART %%NPART%%
#define N_A %%N_A%%

#define RCUT_A %%RCUT_A%%
#define RCUT_B %%RCUT_B%%
#define RCUT_AB %%RCUT_AB%%

#define EPSILON_A %%EPSILON_A%%
#define EPSILON_B %%EPSILON_B%%
#define EPSILON_AB %%EPSILON_AB%%

#define SIGMA_A %%SIGMA_A%%
#define SIGMA_B %%SIGMA_B%%
#define SIGMA_AB %%SIGMA_AB%%

#define LENGTH_X %%LENGTH_X%%
#define LENGTH_Y %%LENGTH_Y%%
#define SHIFT_X LENGTH_X/2 // générique et logique
#define SHIFT_Y LENGTH_Y/2

#define X_PERIODIC %%X_PERIODIC%%
#define Y_PERIODIC %%Y_PERIODIC%%


layout (local_size_x=LAYOUT_SIZE, local_size_y=1, local_size_z=1) in;

layout (std430, binding=0) buffer in_0
{
    vec2 inxs[];
};

layout (std430, binding=1) buffer out_0
{
    vec2 outfs[];
};

layout (std430, binding=2) buffer out_1
{
    float outes[];
};

layout (std430, binding=3) buffer out_2
{
    float outms[];
};

layout (std430, binding=4) buffer in_params
{
    uint inparams[];
};

float force(float dist, float p, float epsilon) {
	return (-4.0*epsilon*(6.0*p-12.0*p*p))/(dist*dist);
}

float energy(float dist, float p, float epsilon) {
	return epsilon*(4.0*(p*p-p)+127.0/4096.0);
}

void iterate(vec2 pos, uint a, uint b, float epsilon, float sigma, float rcut) {
	// a et b les bornes, pos la position de l'atome associé à l'instance
	const uint x = gl_GlobalInvocationID.x;

	for (uint i=a;i<b;i++) {
		if (i!=x) {
			vec2 distxy = pos - inxs[i];

			// Conditions périodiques de bord
			/* On trouvera des tutos sur le net qui disent de vectoriser les tests suivants à la main
             * mais le compilateur est malin et le fait tout seul.
             */
			#if X_PERIODIC
				if (distxy.x<(-SHIFT_X)) {
					distxy.x+=LENGTH_X;
				}
				if (distxy.x>SHIFT_X) {
					distxy.x-=LENGTH_X;
				}
			#endif

			#if Y_PERIODIC
				if (distxy.y<(-SHIFT_Y)) {
					distxy.y+=LENGTH_Y;
				}
				if (distxy.y>SHIFT_Y) {
					distxy.y-=LENGTH_Y;
				}
			#endif


			/* Ce test accélère d'environ 15%, puisqu'on saute les étapes de multipication+somme du calcul de distance
			 * pour voir si on est dans la sphère
			 */
			if(abs(distxy.x)<rcut && abs(distxy.y)<rcut) {

				float dist = length(distxy);

				if (dist<rcut) {
					const float p=pow(sigma/dist, 6);

					outfs[x] += force(dist, p, epsilon)*distxy;
					outes[x] += energy(dist, p, epsilon);
					outms[x] += 1.0;
				}
			}
		}
	}
}

void main()
{
	const uint x = gl_GlobalInvocationID.x;
	const vec2 pos = inxs[x];

	outfs[x] = vec2(0.0);
	outes[x] = 0.0;
	outms[x] = 0.0;

	if(x < NPART) { // On vérifie qu'on est bien associé à un atome

		if(x < N_A) { // si on est de l'espèce A
			iterate(pos, 0, N_A, EPSILON_A, SIGMA_A, RCUT_A); // on s'occupe d'abord des forces avec les autres A
			iterate(pos, N_A, NPART, EPSILON_AB, SIGMA_AB, RCUT_AB); // on finit par les forces avec les B
		} else { // si on est de l'espèce B, même chose
			iterate(pos, 0, N_A, EPSILON_AB, SIGMA_AB, RCUT_AB);
			iterate(pos, N_A, NPART, EPSILON_B, SIGMA_B, RCUT_B);
		}

	}
}