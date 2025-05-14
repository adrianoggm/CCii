# evaluate_model.py
# -*- coding: utf-8 -*-
import argparse
import os
import csv

from pyspark.sql import SparkSession
from pyspark.ml.classification import RandomForestClassificationModel, LogisticRegressionModel
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
import matplotlib.pyplot as plt


def main():
    p = argparse.ArgumentParser(description="Evaluación P3 - p3_adriano")
    p.add_argument("--data", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--algo", choices=["rf", "lr"], required=True)
    p.add_argument("--plot-dir", default="/tmp/plots")
    p.add_argument("--results-csv", default="evaluation_results.csv", help="Path to save evaluation results as CSV")
    args = p.parse_args()

    spark = SparkSession.builder.appName(f"p3_adriano_eval_{args.algo}").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    df = spark.read.parquet(args.data)

    if args.algo == "rf":
        model = RandomForestClassificationModel.load(args.model)
    else:
        model = LogisticRegressionModel.load(args.model)

    preds = model.transform(df)

    # Evaluación
    mce = MulticlassClassificationEvaluator(metricName="accuracy")
    acc = mce.evaluate(preds)
    print(f"Accuracy final ({args.algo}): {acc:.4f}")

    # Guardar resultados en CSV
    results_path = args.results_csv
    file_exists = os.path.isfile(results_path)
    with open(results_path, mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        if not file_exists:
            # Escribir encabezados si el archivo no existe
            writer.writerow(["Algorithm", "ModelPath", "Accuracy"])
        writer.writerow([args.algo, args.model, acc])

    # Matriz de confusión
    os.makedirs(args.plot_dir, exist_ok=True)
    cm_rows = preds.groupBy("label", "prediction").count().collect()
    labels = sorted({row['label'] for row in cm_rows})
    mat = [[0] * len(labels) for _ in labels]
    for row in cm_rows:
        i = labels.index(row['label'])
        j = labels.index(row['prediction'])
        mat[i][j] = row['count']

    plt.figure()
    plt.imshow(mat, interpolation='nearest', cmap='Blues')
    plt.title(f"Confusion matrix {args.algo}")
    plt.colorbar()
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.xticks(range(len(labels)), labels)
    plt.yticks(range(len(labels)), labels)

    # Guardar la matriz de confusión con un nombre único
    model_name = os.path.basename(args.model)
    cm_path = os.path.join(args.plot_dir, f"confusion_eval_{args.algo}_{model_name}.png")
    plt.savefig(cm_path, bbox_inches='tight')
    print(f"Matriz de confusión evaluada guardada en {cm_path}")

    spark.stop()


if __name__ == "__main__":
    main()