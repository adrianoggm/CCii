# train_model.py
# -*- coding: utf-8 -*-
import argparse
import os
import csv
import matplotlib.pyplot as plt

from pyspark.sql import SparkSession
from pyspark.ml.classification import RandomForestClassifier, LogisticRegression
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator


def main():
    p = argparse.ArgumentParser(description="Entrenamiento P3 - p3_adriano")
    p.add_argument("--data", required=True)
    p.add_argument("--model-out", required=True)
    p.add_argument("--algo", choices=["rf", "lr"], required=True,
                   help="rf: Random Forest, lr: Logistic Regression")
    p.add_argument("--maxIter", type=int, default=10)
    p.add_argument("--regParam", type=float, default=0.0)
    p.add_argument("--numTrees", type=int, default=20)
    p.add_argument("--plot-dir", default="/tmp/plots")
    p.add_argument("--results-csv", default="results.csv", help="Path to save results as CSV")
    args = p.parse_args()

    # Identify tag from model path to use in plot filenames
    tag = os.path.basename(args.model_out.rstrip('/'))

    spark = SparkSession.builder.appName(f"p3_adriano_train_{tag}").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # Lectura de datos
    df = spark.read.parquet(args.data)

    # Preparar features
    if "features" in df.columns:
        data2 = df.select("features", "label")
    else:
        assembler = VectorAssembler(
            inputCols=[c for c in df.columns if c != "label"],
            outputCol="features"
        )
        data2 = assembler.transform(df).select("features", "label")

    train, test = data2.randomSplit([0.8, 0.2], seed=33)

    # Selección de modelo
    if args.algo == "rf":
        clf = RandomForestClassifier(labelCol="label", featuresCol="features", numTrees=args.numTrees)
    else:
        clf = LogisticRegression(labelCol="label", featuresCol="features",
                                 maxIter=args.maxIter, regParam=args.regParam)

    model = clf.fit(train)

    os.makedirs(args.plot_dir, exist_ok=True)
    preds = model.transform(test)

    # Curva ROC y AUC (solo para RF y LR)
    bce = BinaryClassificationEvaluator(rawPredictionCol="rawPrediction", metricName="areaUnderROC")
    auc = bce.evaluate(preds)
    print(f"AUC ({args.algo}): {auc:.4f}")

    from pyspark.mllib.evaluation import BinaryClassificationMetrics
    scoreAndLabels = preds.rdd.map(lambda r: (float(r.probability[1]), float(r.label)))
    metrics = BinaryClassificationMetrics(scoreAndLabels)
    try:
        java_roc = metrics._java_model.roc()
        roc_list = java_roc.collect()
        xs = [float(pair._1()) for pair in roc_list]
        ys = [float(pair._2()) for pair in roc_list]
        plt.figure()
        plt.plot(xs, ys)
        plt.xlabel("FPR")
        plt.ylabel("TPR")
        plt.title(f"ROC {tag}")
        roc_path = os.path.join(
            args.plot_dir,
            f"roc_{args.algo}_t{args.numTrees}_i{args.maxIter}_r{args.regParam}_{tag}.png"
        )
        plt.savefig(roc_path, bbox_inches='tight')
        print(f"ROC curve saved in {roc_path}")
    except Exception as e:
        print(f"No se pudo generar la curva ROC: {e}")

    # Accuracy
    mce = MulticlassClassificationEvaluator(metricName="accuracy")
    acc = mce.evaluate(preds)
    print(f"Accuracy ({args.algo}): {acc:.4f}")

    # Guardar resultados en CSV
    results_path = args.results_csv
    file_exists = os.path.isfile(results_path)
    with open(results_path, mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        if not file_exists:
            # Escribir encabezados si el archivo no existe
            writer.writerow(["Algorithm", "NumTrees", "MaxIter", "RegParam", "AUC", "Accuracy", "ModelTag"])
        writer.writerow([args.algo, args.numTrees, args.maxIter, args.regParam, auc, acc, tag])

    # Matriz de confusión
    cm_rows = preds.groupBy("label", "prediction").count().collect()
    labels = sorted({row['label'] for row in cm_rows})
    mat = [[0] * len(labels) for _ in labels]
    for row in cm_rows:
        i = labels.index(row['label'])
        j = labels.index(row['prediction'])
        mat[i][j] = row['count']

    plt.figure()
    plt.imshow(mat, interpolation='nearest', cmap='Blues')
    plt.title(f"Confusion matrix {tag}")
    plt.colorbar()
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.xticks(range(len(labels)), labels)
    plt.yticks(range(len(labels)), labels)
    conf_path = os.path.join(
        args.plot_dir,
        f"confusion_{args.algo}_t{args.numTrees}_i{args.maxIter}_r{args.regParam}_{tag}.png"
    )
    plt.savefig(conf_path, bbox_inches='tight')
    print(f"Matriz de confusión guardada en {conf_path}")

    # Guardar modelo
    model.write().overwrite().save(args.model_out)
    spark.stop()


if __name__ == "__main__":
    main()