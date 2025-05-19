#!/usr/bin/env bash

# Para Matplotlib cache
export MPLCONFIGDIR=/tmp

# Configuración del cluster
MASTER="local[*]"
DEPLOY_MODE="client"
MEM_EXEC="2g"
CORES_EXEC="2"
MEM_DRIVER="1g"

BASE_HDFS="hdfs://namenode:8020/user/aggm000edu"
PLOTS="/tmp/plots"

# 1) Preprocesado
spark-submit \
  --master $MASTER \
  --deploy-mode $DEPLOY_MODE \
  --conf spark.executor.memory=$MEM_EXEC \
  --conf spark.executor.cores=$CORES_EXEC \
  --conf spark.driver.memory=$MEM_DRIVER \
  process_data.py \
    --input  $BASE_HDFS/half_celestial.csv \
    --output $BASE_HDFS/half_celestial_clean \
    --calc-corr --plot-dir $PLOTS

# 2) Experimentos con distintos hiperparámetros

# Random Forest: variar numTrees
for trees in 10 50 100; do
  MODEL_PATH="$BASE_HDFS/models/rf_t${trees}"
  spark-submit \
    --master $MASTER \
    --deploy-mode $DEPLOY_MODE \
    --conf spark.executor.memory=$MEM_EXEC \
    --conf spark.executor.cores=$CORES_EXEC \
    --conf spark.driver.memory=$MEM_DRIVER \
    train_model.py \
      --data      $BASE_HDFS/half_celestial_clean \
      --model-out $MODEL_PATH \
      --algo rf --numTrees $trees --plot-dir $PLOTS

  spark-submit \
    --master $MASTER \
    --deploy-mode $DEPLOY_MODE \
    --conf spark.executor.memory=$MEM_EXEC \
    --conf spark.executor.cores=$CORES_EXEC \
    --conf spark.driver.memory=$MEM_DRIVER \
    evaluate_model.py \
      --data $BASE_HDFS/half_celestial_clean \
      --model $MODEL_PATH \
      --algo rf \
      --plot-dir $PLOTS

  echo "-------- RF numTrees=$trees completado --------"
done

# Logistic Regression: variar maxIter y regParam
for iter in 5 20; do
  for reg in 0.0 0.1; do
    MODEL_PATH="$BASE_HDFS/models/lr_i${iter}_r${reg}"
    spark-submit \
      --master $MASTER \
      --deploy-mode $DEPLOY_MODE \
      --conf spark.executor.memory=$MEM_EXEC \
      --conf spark.executor.cores=$CORES_EXEC \
      --conf spark.driver.memory=$MEM_DRIVER \
      train_model.py \
        --data      $BASE_HDFS/half_celestial_clean \
        --model-out $MODEL_PATH \
        --algo lr --maxIter $iter --regParam $reg --plot-dir $PLOTS

    spark-submit \
      --master $MASTER \
      --deploy-mode $DEPLOY_MODE \
      --conf spark.executor.memory=$MEM_EXEC \
      --conf spark.executor.cores=$CORES_EXEC \
      --conf spark.driver.memory=$MEM_DRIVER \
      evaluate_model.py \
        --data $BASE_HDFS/half_celestial_clean \
        --model $MODEL_PATH \
        --algo lr \
        --plot-dir $PLOTS

    echo "---- LR maxIter=$iter regParam=$reg completado ----"
  done
done

# SVM: variar maxIter y regParam
for iter in 5 20; do
  for reg in 0.0 0.1; do
    MODEL_PATH="$BASE_HDFS/models/svm_i${iter}_r${reg}"
    spark-submit \
      --master $MASTER \
      --deploy-mode $DEPLOY_MODE \
      --conf spark.executor.memory=$MEM_EXEC \
      --conf spark.executor.cores=$CORES_EXEC \
      --conf spark.driver.memory=$MEM_DRIVER \
      train_model.py \
        --data      $BASE_HDFS/half_celestial_clean \
        --model-out $MODEL_PATH \
        --algo svm --maxIter $iter --regParam $reg --plot-dir $PLOTS

    spark-submit \
      --master $MASTER \
      --deploy-mode $DEPLOY_MODE \
      --conf spark.executor.memory=$MEM_EXEC \
      --conf spark.executor.cores=$CORES_EXEC \
      --conf spark.driver.memory=$MEM_DRIVER \
      evaluate_model.py \
        --data $BASE_HDFS/half_celestial_clean \
        --model $MODEL_PATH \
        --algo svm \
        --plot-dir $PLOTS

    echo "---- SVM maxIter=$iter regParam=$reg completado ----"
  done
done
