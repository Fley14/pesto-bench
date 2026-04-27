#include <omp.h>
#include <math.h>
#define ceild(n,d)  (((n)<0) ? -((-(n))/(d)) : ((n)+(d)-1)/(d))
#define floord(n,d) (((n)<0) ? -((-(n)+(d)-1)/(d)) : (n)/(d))
#define max(x,y)    ((x) > (y)? (x) : (y))
#define min(x,y)    ((x) < (y)? (x) : (y))

/*
 * Calculating the price of American Put Option
 * Adapted from Pochoir test bench
 *
 * Irshad Pananilath: irshad@csa.iisc.ernet.in
 */

#include <stdio.h>
#include <sys/time.h>

#define max(x, y) ((x) > (y) ? (x) : (y))
#define min(x, y) ((x) < (y) ? (x) : (y))

/* apop_pochoir -S 100 -E 95 -r 10 -V 30 -T 1 -s 2000000 -t 10000 */

/* #define DEFAULT_S 100.00 */
/* #define DEFAULT_E 100.00 */
/* #define DEFAULT_r   0.10 */
/* #define DEFAULT_V   0.25 */
/* #define DEFAULT_T   1.00 */
/*  */
/* #define DEFAULT_s 100 */
/* #define DEFAULT_t 100 */

#define DEFAULT_S 100.00
#define DEFAULT_E 95.00
#define DEFAULT_r 0.10
#define DEFAULT_V 0.30
#define DEFAULT_T 1.00

#define DEFAULT_s 101000000
#define DEFAULT_t 100000

#define NUM_FP_OPS 6
#define BENCHMARK_NUM_FP_OPS (NUM_FP_OPS) * (DEFAULT_s) * (DEFAULT_t)

#include <benchmark.h>

void print_usage(char *prog) {
	printf("Usage: %s [ options ]\n\n", prog);

	printf("Options:\n");

	printf("\t-S value : spot price ( default: %0.2lf )\n", DEFAULT_S);
	printf("\t-E value : exercise price ( default: %0.2lf )\n", DEFAULT_E);
	printf("\t-r value : interest rate ( default: %0.2lf )\n", DEFAULT_r * 100);
	printf("\t-V value : volatility ( default: %0.2lf )\n", DEFAULT_V * 100);
	printf("\t-T value : time to mature in years ( default: %0.2lf )\n\n",
		   DEFAULT_T);

	printf("\t-s value : steps in space dimension ( default: %d )\n",
		   DEFAULT_s);
	printf("\t-t value : steps in time dimension ( default: %d )\n\n",
		   DEFAULT_t);

	printf("\t-i               : Run iterative stencil\n\n");

	printf("\t-h               : print this help screen\n\n");
}

void init_array(param_t nt, param_t ns, data_t *E, data_t *dS,
				data_t BENCHMARK_2D(C, 3, DEFAULT_s, 3, ns),
				data_t BENCHMARK_2D(F, 2, DEFAULT_s, 2, ns)) {
	data_t S, r, V, T;
	iter_t i, t, x;

	S = DEFAULT_S;
	*E = DEFAULT_E;
	r = DEFAULT_r;
	V = DEFAULT_V;
	T = DEFAULT_T;

	*dS = 2.0 * S / ns;

	/* computeCoeffs( r, V, T, ns, nt ); */

	// initialize
	double V2 = V * V;
	double dt = T / nt;
	double r1 = 1.0 / (1.0 + r * dt);
	double r2 = dt / (1.0 + r * dt);

	for (x = 0; x <= ns; ++x) {
		C[0][x] = r2 * 0.5 * x * (-r + V2 * x);
		C[1][x] = r1 * (1 - V2 * x * x * dt);
		C[2][x] = r2 * 0.5 * x * (r + V2 * x);
	}

	for (i = 0; i <= ns; ++i) {
		F[0][i] = max(0.0, *E - i * *dS);
	}

	F[1][0] = *E;

	for (t = 0; t < nt; ++t) {
		F[0][ns] = 0;
		F[1][ns] = 0;
	}
}

void dump_arrays(param_t nt, param_t ns, data_t E, data_t dS,
				 data_t BENCHMARK_2D(C, 3, DEFAULT_s, 3, ns),
				 data_t BENCHMARK_2D(F, 2, DEFAULT_s, 2, ns)) {
	BENCHMARK_DUMP_START();
#ifdef BENCHMARK_DUMP_CHKSUM
	BENCHMARK_DUMP_BEGIN("parameters");
	fprintf(BENCHMARK_DUMP_FILE, "nt: %ld\n", nt);
	fprintf(BENCHMARK_DUMP_FILE, "ns: %ld\n", ns);
	fprintf(BENCHMARK_DUMP_FILE, "E: %e\n", E);
	fprintf(BENCHMARK_DUMP_FILE, "dS: %e\n", dS);
	BENCHMARK_DUMP_END("parameters");
#endif
#ifdef BENCHMARK_DUMP_ARRAYS
	BENCHMARK_DUMP_BEGIN("C");
	for (iter_t i = 0; i <= ns; ++i) {
		fprintf(BENCHMARK_DUMP_FILE, "%e %e %e\n", C[0][i], C[1][i], C[2][i]);
		if (i % 100 == 99) {
			fprintf(BENCHMARK_DUMP_FILE, "\n");
		}
	}
	BENCHMARK_DUMP_END("C");
	BENCHMARK_DUMP_BEGIN("F");
	for (iter_t i = 0; i <= ns; ++i) {
		fprintf(BENCHMARK_DUMP_FILE, "%e ", F[nt % 2][i]);
		if (i % 100 == 99) {
			fprintf(BENCHMARK_DUMP_FILE, "\n");
		}
	}
	fprintf(BENCHMARK_DUMP_FILE, "\n");
	BENCHMARK_DUMP_END("F");
	data_t price1 = F[nt % 2][(ns >> 1)];
	BENCHMARK_DUMP_BEGIN("result");
	fprintf(BENCHMARK_DUMP_FILE, "option price = %e\n", price1);
	BENCHMARK_DUMP_END("result");
#endif /* BENCHMARK_DUMP_ARRAYS */
	BENCHMARK_DUMP_STOP();
}

void kernel_apop(param_t nt, param_t ns, data_t E, data_t dS,
				 data_t BENCHMARK_2D(C, 3, DEFAULT_s, 3, ns),
				 data_t BENCHMARK_2D(F, 2, DEFAULT_s, 2, ns)) {
	iter_t t, i;
  int t1, t2, t3, t4;
 int lb, ub, lbp, ubp, lb2, ub2;
 register int lbv, ubv;
if ((ns >= 2) && (nt >= 1)) {
  for (t1=ceild(-7*ns-226,128);t1<=floord(9*nt-16,128);t1++) {
    lbp=max(max(ceild(-t1-8,7),ceild(t1-7,9)),ceild(16*t1-nt+2,16));
    ubp=min(min(min(floord(16*t1+ns+14,16),floord(-8*t1+nt-1,56)),floord(8*t1+ns+6,72)),floord(nt+ns-2,128));
#pragma omp parallel for private(lbv,ubv,t3,t4) schedule(static)
    for (t2=lbp;t2<=ubp;t2++) {
      for (t3=max(max(max(0,8*t1+56*t2),16*t1-16*t2+1),128*t2-ns+1);t3<=min(min(min(nt-1,128*t2+126),8*t1+56*t2+71),16*t1-16*t2+ns+14);t3++) {
        lbv=max(max(128*t2,t3+1),-16*t1+16*t2+2*t3-15);
        ubv=min(min(128*t2+127,-16*t1+16*t2+2*t3),t3+ns-1);

#pragma GCC ivdep
        for (t4=lbv;t4<=ubv;t4++) {
          F[(t3 + 1) % 2][(-t3+t4)] = max(C[0][(-t3+t4)] * F[t3 % 2][(-t3+t4) - 1] + C[1][(-t3+t4)] * F[t3 % 2][(-t3+t4)] + C[2][(-t3+t4)] * F[t3 % 2][(-t3+t4) + 1], E - (-t3+t4) * dS);;
        }
      }
    }
  }
}
}

int main(int argc, char *argv[]) {
	param_t ns = DEFAULT_s;
	param_t nt = DEFAULT_t;
	data_t E, dS;

	ns = ns + (ns & 1);

	BENCHMARK_2D_ARRAY_DECL(C, data_t, 3, DEFAULT_s, 3, ns);
	BENCHMARK_2D_ARRAY_DECL(F, data_t, 2, DEFAULT_s, 2, ns);

#ifdef DEBUG
	printf("\nStencil-based DP for the price of American put option ( Run "
		   "with "
		   "option -h for help ).\n\n");
	printf("Parameters:\n\n");

	printf("\t spot price = %0.2lf\n", S);
	printf("\t exercise price = %0.2lf\n", E);
	printf("\t interest rate = %0.2lf\%\n", r * 100);
	printf("\t volatility = %0.2lf\%\n", V * 100);
	printf("\t time to mature ( in years ) = %0.2lf\n\n", T);

	printf("\t steps in space dimension = %d\n", ns);
	printf("\t steps in time dimension = %d\n\n", nt);
#endif

	init_array(nt, ns, &E, &dS, C, F);

	/* start timer */
	benchmark_measure_start();

	/* serial execution */
	kernel_apop(nt, ns, E, dS, C, F);

	/* stop timer */
	benchmark_measure_stop();

	/* print time */
	benchmark_measure_print();

#ifdef BENCHMARK_DUMP
	dump_arrays(nt, ns, E, dS, C, F);
#endif /* BENCHMARK_DUMP */

	BENCHMARK_FREE_ARRAY(F);
	BENCHMARK_FREE_ARRAY(C);

	return 0;
}
