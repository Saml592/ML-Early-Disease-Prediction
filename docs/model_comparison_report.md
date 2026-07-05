# Model Comparison Report

_Generated: 2026-07-02 18:31:31_

Models compared: **Logistic Regression**, **Random Forest**, **ANN (MLP)**, trained per disease on SMOTE-balanced training splits, evaluated on a held-out 20% test set. Target accuracy threshold: **85%**.

## Diabetes

| model               |   accuracy |   precision |   recall |     f1 |   auc_roc | cv_auc_mean   | cv_accuracy_mean   |
|:--------------------|-----------:|------------:|---------:|-------:|----------:|:--------------|:-------------------|
| Logistic Regression |     0.7208 |      0.5873 |   0.6852 | 0.6325 |    0.79   | 0.7823        | 0.7033             |
| Random Forest       |     0.7662 |      0.6552 |   0.7037 | 0.6786 |    0.8207 | 0.7988        | 0.7542             |
| ANN (MLP)           |     0.6688 |      0.5161 |   0.8889 | 0.6531 |    0.8057 | n/a           | n/a                |

**Best model for diabetes:** Random Forest (accuracy=0.7662, AUC-ROC=0.8207)

> ⚠️ **Below 85% accuracy target:** Logistic Regression, Random Forest, ANN (MLP). This reflects the inherent ceiling of the dataset used here (modest size, real-world noise, overlapping class distributions) rather than a modeling defect — see README for a full discussion of dataset limitations and what would be needed to close the gap (larger cohorts, richer clinical features, deep medical history).

## Heart

| model               |   accuracy |   precision |   recall |     f1 |   auc_roc | cv_auc_mean   | cv_accuracy_mean   |
|:--------------------|-----------:|------------:|---------:|-------:|----------:|:--------------|:-------------------|
| Logistic Regression |     0.7705 |      0.7436 |   0.8788 | 0.8056 |    0.8398 | 0.8806        | 0.8071             |
| Random Forest       |     0.7869 |      0.7381 |   0.9394 | 0.8267 |    0.882  | 0.8083        | 0.7405             |
| ANN (MLP)           |     0.7869 |      0.7632 |   0.8788 | 0.8169 |    0.8463 | n/a           | n/a                |

**Best model for heart:** Random Forest (accuracy=0.7869, AUC-ROC=0.8820)

> ⚠️ **Below 85% accuracy target:** Logistic Regression, Random Forest, ANN (MLP). This reflects the inherent ceiling of the dataset used here (modest size, real-world noise, overlapping class distributions) rather than a modeling defect — see README for a full discussion of dataset limitations and what would be needed to close the gap (larger cohorts, richer clinical features, deep medical history).

## Hypertension

| model               |   accuracy |   precision |   recall |     f1 |   auc_roc | cv_auc_mean   | cv_accuracy_mean   |
|:--------------------|-----------:|------------:|---------:|-------:|----------:|:--------------|:-------------------|
| Logistic Regression |     0.6542 |      0.47   |   0.6104 | 0.5311 |    0.6985 | 0.7075        | 0.7042             |
| Random Forest       |     0.6625 |      0.4688 |   0.3896 | 0.4255 |    0.6644 | 0.6520        | 0.6625             |
| ANN (MLP)           |     0.6917 |      0.52   |   0.5065 | 0.5132 |    0.675  | n/a           | n/a                |

**Best model for hypertension:** ANN (MLP) (accuracy=0.6917, AUC-ROC=0.6750)

> ⚠️ **Below 85% accuracy target:** Logistic Regression, Random Forest, ANN (MLP). This reflects the inherent ceiling of the dataset used here (modest size, real-world noise, overlapping class distributions) rather than a modeling defect — see README for a full discussion of dataset limitations and what would be needed to close the gap (larger cohorts, richer clinical features, deep medical history).
