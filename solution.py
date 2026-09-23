import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

train_signals = pd.read_csv('train_signals.csv')
train_trans = pd.read_parquet('train_transactions.parquet')
test_signals = pd.read_csv('test_signals.csv')
test_trans = pd.read_parquet('test_transactions.parquet')

def engineer_features(signals_df, trans_df):
    signals = signals_df.copy()
    trans = trans_df.copy()

    signals['signal_sanasi'] = pd.to_datetime(signals['signal_sanasi'])
    trans['tranzaksiya_vaqti'] = pd.to_datetime(trans['tranzaksiya_vaqti'])
    trans['kirim_chiqim'] = trans['kirim_chiqim'].astype(str)
    trans['tranzaksiya_turi'] = trans['tranzaksiya_turi'].astype(str)

    base_stats = trans.groupby('signal_id').agg(
        txn_count=('miqdor_indeksi', 'count'),
        amount_sum=('miqdor_indeksi', 'sum'),
        amount_mean=('miqdor_indeksi', 'mean'),
        amount_std=('miqdor_indeksi', 'std'),
        amount_max=('miqdor_indeksi', 'max'),
        amount_min=('miqdor_indeksi', 'min'),
        last_txn_time=('tranzaksiya_vaqti', 'max'),
        first_txn_time=('tranzaksiya_vaqti', 'min')
    ).reset_index()

    dir_piv = trans.pivot_table(
        index='signal_id',
        columns='kirim_chiqim',
        values='miqdor_indeksi',
        aggfunc=['count', 'sum'],
        fill_value=0
    )
    dir_piv.columns = [f"{col[1]}_{col[0]}" for col in dir_piv.columns]
    dir_piv = dir_piv.reset_index()

    type_piv = trans.pivot_table(
        index='signal_id',
        columns='tranzaksiya_turi',
        values='miqdor_indeksi',
        aggfunc=['count', 'sum'],
        fill_value=0
    )
    type_piv.columns = [f"{col[1]}_{col[0]}" for col in type_piv.columns]
    type_piv = type_piv.reset_index()

    merged = base_stats.merge(dir_piv, on='signal_id', how='left').merge(type_piv, on='signal_id', how='left')
    output = signals.merge(merged, on='signal_id', how='left')

    output['days_to_last_txn'] = (output['signal_sanasi'] - output['last_txn_time']).dt.total_seconds() / 86400.0
    output['days_to_first_txn'] = (output['signal_sanasi'] - output['first_txn_time']).dt.total_seconds() / 86400.0
    output['txn_span_days'] = (output['last_txn_time'] - output['first_txn_time']).dt.total_seconds() / 86400.0

    if 'chiqim_sum' in output.columns and 'kirim_sum' in output.columns:
        output['chiqim_kirim_sum_ratio'] = output['chiqim_sum'] / (output['kirim_sum'] + 1e-5)
    if 'chiqim_count' in output.columns and 'kirim_count' in output.columns:
        output['chiqim_kirim_cnt_ratio'] = output['chiqim_count'] / (output['kirim_count'] + 1e-5)

    output['signal_month'] = output['signal_sanasi'].dt.month
    output['signal_day'] = output['signal_sanasi'].dt.day
    output['signal_dow'] = output['signal_sanasi'].dt.dayofweek

    cols_to_drop = ['last_txn_time', 'first_txn_time']
    output = output.drop(columns=[c for c in cols_to_drop if c in output.columns])

    return output

train_df = engineer_features(train_signals, train_trans)
test_df = engineer_features(test_signals, test_trans)

exclude_cols = ['signal_id', 'signal_sanasi', 'eskalatsiya']
feature_cols = [c for c in train_df.columns if c not in exclude_cols]

for col in feature_cols:
    if col not in test_df.columns:
        test_df[col] = 0

X = train_df[feature_cols].fillna(0)
y = train_df['eskalatsiya']
X_test = test_df[feature_cols].fillna(0)

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
oof_preds = np.zeros(len(X))
test_preds = np.zeros(len(X_test))

lgb_params = {
    'objective': 'binary',
    'metric': 'auc',
    'boosting_type': 'gbdt',
    'learning_rate': 0.03,
    'num_leaves': 31,
    'max_depth': 6,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 1,
    'n_estimators': 1500,
    'random_state': 42,
    'verbose': -1
}

for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
    X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
    X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]

    model = lgb.LGBMClassifier(**lgb_params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
    )

    oof_preds[val_idx] = model.predict_proba(X_val)[:, 1]
    test_preds += model.predict_proba(X_test)[:, 1] / skf.n_splits

cv_auc = roc_auc_score(y, oof_preds)
print(f"5-Fold CV ROC-AUC: {cv_auc:.5f}")

submission = pd.DataFrame({
    'signal_id': test_df['signal_id'],
    'ehtimollik': np.clip(test_preds, 0.0, 1.0)
})

submission.to_csv('team_6927C48E.csv', index=False)
print("Saved team_6927C48E.csv successfully.")
