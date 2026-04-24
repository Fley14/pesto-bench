python3 /home/marteau/pesto-bench/tools/finetune.py \
/home/marteau/pesto-bench/pluto_bench/heat-1d/heat-1d.c \
--log-file /home/marteau/test_flav/results/res_2026-04-24-15-52-16/heat-1d.log  \
--env=/home/marteau/omp64.env \
--compiler-bin="gcc" \
-I /home/marteau/pesto-bench/include/ \
--compiler-extra-flags="-lm -L/home/marteau/pesto-bench/lib -lbenchmark -DBENCHMARK_TIME" \
--pluto="/home/marteau/pluto/polycc" \
--pluto-flags="--tile --parallel --diamond-tile --nounroll --prevector" \
 --pluto-custom-vec-pragma="#pragma GCC ivdep" \
--force-omp-schedule "static" \
--param T0 "[256,512,pow2]" \
--param T1 "[256,512,pow2]" \
--timeout 2 \
--output-dump-flags="-DBENCHMARK_DUMP_ARRAYS" \