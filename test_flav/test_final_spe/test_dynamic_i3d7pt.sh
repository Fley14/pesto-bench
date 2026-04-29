python3 /home/marteau/pesto-bench/tools/finetune.py \
/home/marteau/pesto-bench/pluto_bench/3d7pt/3d7pt.c \
--log-file /home/marteau/test_flav/results/res_2026-04-24-19-00-24/3d7pt-dynamic.log  \
--env=/home/marteau/omp64.env \
--compiler-bin="gcc" \
-I /home/marteau/pesto-bench/include/ \
--compiler-extra-flags="-lm -L/home/marteau/pesto-bench/lib -lbenchmark -DBENCHMARK_TIME" \
--pluto="/home/marteau/pluto/polycc" \
--pluto-flags="--tile --parallel --diamond-tile --nounroll --prevector" \
 --pluto-custom-vec-pragma="#pragma GCC ivdep" \
--force-omp-schedule "dynamic" \
--perf-nrun 20 \
--param T0 "[2,256,pow2]" \
--param T1 "[2,256,pow2]" \
--param T2 "[2,256,pow2]" \
--param T3 "[2,256,pow2]" \
--timeout 3 \
--output-dump-flags="-DBENCHMARK_DUMP_ARRAYS" \