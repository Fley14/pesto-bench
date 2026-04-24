python3 /home/marteau/pesto-bench/tools/finetune.py \
/home/marteau/pesto-bench/pluto_bench/heat-3d/heat-3d.c \
--log-file /home/marteau/test_flav/results/res_base/heat-3d.log  \
--env=/home/marteau/omp64.env \
--compiler-bin="gcc" \
-I /home/marteau/pesto-bench/include/ \
--compiler-extra-flags="-lm -L/home/marteau/pesto-bench/lib -lbenchmark -DBENCHMARK_TIME" \
--pluto="/home/marteau/pluto/polycc" \
--pluto-flags="--tile --parallel --diamond-tile --nounroll --prevector" \
 --pluto-custom-vec-pragma="#pragma GCC ivdep" \
--force-omp-schedule "static" \
--param T0 "{8}" \
--param T1 "{8}" \
--param T2 "{8}" \
--param T3 "{8}" \
--timeout 4 \
--output-dump-flags="-DBENCHMARK_DUMP_ARRAYS" \