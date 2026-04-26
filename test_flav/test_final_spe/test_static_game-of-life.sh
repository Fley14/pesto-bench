python3 /home/marteau/pesto-bench/tools/finetune.py \
/home/marteau/pesto-bench/pluto_bench/game-of-life/life.c \
--log-file /home/marteau/test_flav/results/res_2026-04-24-19-00-24/game-of-life-static.log  \
--env=/home/marteau/omp64.env \
--compiler-bin="gcc" \
-I /home/marteau/pesto-bench/include/ \
--compiler-extra-flags="-lm -L/home/marteau/pesto-bench/lib -lbenchmark -DBENCHMARK_TIME" \
--pluto="/home/marteau/pluto/polycc" \
--pluto-flags="--tile --parallel --diamond-tile --nounroll --prevector" \
 --pluto-custom-vec-pragma="#pragma GCC ivdep" \
--force-omp-schedule "static" \
--perf-nrun 20 \
--param T0 "[2,4096,pow2]" \
--param T1 "[2,2048,pow2]" \
--param T2 "[2,2048,pow2]" \
--timeout 2 \
--output-dump-flags="-DBENCHMARK_DUMP_ARRAYS" \