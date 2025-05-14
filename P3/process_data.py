# process_data.py
# -*- coding: utf-8 -*-
import argparse
import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import when, col, isnan, count
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.stat import Correlation
from pyspark.sql.types import NumericType
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description="Preprocesado P3 - p3_adriano")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--calc-corr", action="store_true")
    parser.add_argument("--corr-threshold", type=float, default=0.9)
    parser.add_argument("--plot-dir", default="/tmp/plots")
    args = parser.parse_args()

    spark = SparkSession.builder.appName("p3_adriano_preprocess").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # Lectura CSV con separador ';'
    df = spark.read.csv(args.input, header=True, inferSchema=True, sep=';')

    # 1) Detectar y reportar columnas con valores nulos (NaN/null)
    null_counts = df.select([count(when(isnan(c) | col(c).isNull(), c)).alias(c) for c in df.columns]).collect()[0].asDict()
    cols_with_null = [c for c, v in null_counts.items() if v > 0]
    if cols_with_null:
        print(f"Columnas con valores nulos: {cols_with_null}")

    # 2) Detectar y reportar columnas con valor centinela -999
    num_cols = [f.name for f in df.schema.fields if isinstance(f.dataType, NumericType)]
    sentinel_counts = {}
    for c in num_cols:
        cnt = df.filter(col(c) == -999).count()
        if cnt > 0:
            sentinel_counts[c] = cnt
    if sentinel_counts:
        print(f"Columnas con valor -999: {list(sentinel_counts.keys())}")

    # 3) Eliminar filas con ANY null / NaN
    df = df.na.drop()

    # 4) Eliminar filas con ANY valor centinela -999 en columnas numéricas
    for c in num_cols:
        df = df.filter(col(c) != -999)

    # Inspección
    df.printSchema()
    df.show(5)
    print(f"Filas tras limpieza inicial: {df.count()}, Columnas: {len(df.columns)}")

    # Creamos etiqueta binaria y descartamos 'type'
    df = df.withColumn(
        "label",
        when(col("type") == "galaxy", 0.0).otherwise(1.0).cast("double")
    ).drop("type")

    # (Opcional) Conteo de nulos residuales para verificar
    nulls = df.select([
        count(when(isnan(c) | col(c).isNull(), c)).alias(c)
        for c in df.columns
    ]).collect()[0].asDict()
    print("Conteo de nulos tras etiquetado:", nulls)

    feature_cols = [c for c in df.columns if c != "label"]

    # Cálculo de correlación y eliminación de features altamente correlacionadas
    if args.calc_corr:
        assembler = VectorAssembler(inputCols=feature_cols, outputCol="vec")
        vec_df = assembler.transform(df).select("vec")
        corr_mat = Correlation.corr(vec_df, "vec").head()[0].toArray()

        os.makedirs(args.plot_dir, exist_ok=True)
        plt.figure(figsize=(8, 8))
        plt.imshow(corr_mat, interpolation='nearest', cmap='coolwarm')
        plt.colorbar()
        plt.xticks(range(len(feature_cols)), feature_cols, rotation=90)
        plt.yticks(range(len(feature_cols)), feature_cols)
        plt.title("Matriz de correlación")
        plt.savefig(os.path.join(args.plot_dir, "correlation_matrix.png"), bbox_inches='tight')

        to_drop = set()
        for i in range(len(feature_cols)):
            for j in range(i):
                if abs(corr_mat[i, j]) > args.corr_threshold:
                    to_drop.add(feature_cols[i])

        if to_drop:
            df = df.drop(*to_drop)
            feature_cols = [c for c in feature_cols if c not in to_drop]
        print("Variables eliminadas por correlación:", to_drop)

    # Montaje y escalado de features
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="raw_features")
    df_feat = assembler.transform(df)
    scaler = StandardScaler(
        inputCol="raw_features", outputCol="features",
        withMean=True, withStd=True
    )
    df_scaled = scaler.fit(df_feat).transform(df_feat).select("features", "label")

    # Guardamos en Parquet
    df_scaled.write.mode("overwrite").parquet(args.output)
    print(f"Datos preprocesados guardados en {args.output}")

    spark.stop()


if __name__ == "__main__":
    main()
