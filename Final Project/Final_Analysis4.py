import dask.dataframe as dd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

import statsmodels.api as sm
from scipy import stats


# --------------------------------------------------
# Settings
# --------------------------------------------------
DATA_PATH = "/Users/sylviadu/Documents/CS 369/users_filtered.parquet"
SAMPLE_FRACTION = 0.01  

# --------------------------------------------------
# Load dataset
# --------------------------------------------------
print("Loading filtered dataset with Dask...")
users = dd.read_parquet(DATA_PATH)

print("Precomputing columns...")
users["is_maker"] = (users["role"] == "maker").astype(int)
users["low_prob_trade"] = (users["price"] < 0.1).astype(int)
users["profit_proxy"] = users["token_amount"] * users["price"]
users["datetime"] = dd.to_datetime(users["datetime"])


# --------------------------------------------------
# Aggregate user-level statistics
# --------------------------------------------------
print("Aggregating user metrics...")

user_stats = users.groupby("user").agg(
    net_usd=("usd_amount", "sum"),
    maker_ratio=("is_maker", "mean"),
    total_trades=("usd_amount", "count"),
    low_prob_fraction=("low_prob_trade", "mean"),
    profit_proxy_std=("profit_proxy", "std"),
).compute()

user_stats = user_stats.fillna(0)
print(user_stats.head())


# --------------------------------------------------
# Clustering users
# --------------------------------------------------
print("Clustering users...")

X_cluster = user_stats[
    ["maker_ratio", "low_prob_fraction", "total_trades"]
].fillna(0)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_cluster)

kmeans = KMeans(n_clusters=4, random_state=42)
user_stats["cluster"] = kmeans.fit_predict(X_scaled)

print(user_stats.head())


# --------------------------------------------------
# Rolling 7-day metrics per user
# --------------------------------------------------
print("Computing 7-day rolling net USD per user...")

users_pd = users.compute()
users_pd["date"] = users_pd["datetime"].dt.date

users_daily = (
    users_pd.groupby(["date", "user"])
    .agg(
        net_usd=("usd_amount", "sum"),
        total_trades=("usd_amount", "count"),
    )
    .reset_index()
)

users_daily["date"] = pd.to_datetime(users_daily["date"])
users_daily = users_daily.sort_values(["user", "date"])

users_daily["net_usd_7day"] = users_daily.groupby("user")["net_usd"].transform(
    lambda x: x.rolling(7, min_periods=1).sum()
)


# --------------------------------------------------
# Statistical tests
# --------------------------------------------------
print("Running statistical tests...")

# ANOVA across clusters
groups = [
    user_stats[user_stats["cluster"] == i]["net_usd"]
    for i in range(4)
]
f_stat, p_val = stats.f_oneway(*groups)
print(f"ANOVA across clusters: F={f_stat:.3f}, p={p_val:.3e}")

# Spearman correlation
corr, p_corr = stats.spearmanr(
    user_stats["maker_ratio"],
    user_stats["net_usd"],
)
print(
    f"Spearman correlation (maker_ratio vs net_usd): "
    f"rho={corr:.3f}, p={p_corr:.3e}"
)

# Welch t-test: high vs low risk users
median_risk = user_stats["low_prob_fraction"].median()

high_risk = user_stats[
    user_stats["low_prob_fraction"] > median_risk
]["net_usd"]

low_risk = user_stats[
    user_stats["low_prob_fraction"] <= median_risk
]["net_usd"]

t_stat, p_t = stats.ttest_ind(high_risk, low_risk, equal_var=False)
print(f"T-test high vs low risk: t={t_stat:.3f}, p={p_t:.3e}")


# --------------------------------------------------
# Robust linear regression
# --------------------------------------------------
print("Running robust linear regression...")

y_log = np.log1p(user_stats["net_usd"])

X_lm = pd.get_dummies(
    user_stats[["maker_ratio", "low_prob_fraction", "cluster"]],
    columns=["cluster"],
    drop_first=False,
)

X_lm["maker_lowprob_interaction"] = (
    X_lm["maker_ratio"] * X_lm["low_prob_fraction"]
)

X_lm = sm.add_constant(X_lm)
X_lm = X_lm.astype(float)

model_robust = sm.RLM(
    y_log,
    X_lm,
    M=sm.robust.norms.HuberT(),
).fit()

print(model_robust.summary())

user_stats["pred_net_usd"] = np.expm1(model_robust.fittedvalues)


# --------------------------------------------------
# Visualizations
# --------------------------------------------------
sns.set(style="whitegrid", context="talk")

# Net USD vs maker ratio
plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=user_stats,
    x="maker_ratio",
    y="net_usd",
    hue="cluster",
    palette="tab10",
    alpha=0.6,
)
plt.title("Net USD vs Maker Ratio by Cluster")
plt.xlabel("Maker Ratio")
plt.ylabel("Net USD")
plt.yscale("log")
plt.show()

# Net USD vs low probability fraction
plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=user_stats,
    x="low_prob_fraction",
    y="net_usd",
    alpha=0.6,
)
sns.regplot(
    data=user_stats,
    x="low_prob_fraction",
    y="net_usd",
    scatter=False,
    color="red",
    line_kws={"lw": 2},
)
plt.title("Net USD vs Low Probability Fraction")
plt.xlabel("Low Probability Fraction")
plt.ylabel("Net USD")
plt.yscale("log")
plt.show()

# Rolling performance of top user
top_user = users_daily.groupby("user")["net_usd"].sum().idxmax()
top_user_df = users_daily[users_daily["user"] == top_user]

plt.figure(figsize=(12, 6))
plt.plot(
    top_user_df["date"],
    top_user_df["net_usd_7day"],
    marker="o",
)
plt.title(f"7-Day Rolling Net USD for Top User {top_user}")
plt.xlabel("Date")
plt.ylabel("Net USD (7-day rolling)")
plt.xticks(rotation=45)
plt.show()

# Predicted vs actual
plt.figure(figsize=(10, 6))
sns.scatterplot(
    x=user_stats["net_usd"],
    y=user_stats["pred_net_usd"],
    alpha=0.5,
)
plt.plot(
    [0, user_stats["net_usd"].max()],
    [0, user_stats["net_usd"].max()],
    color="red",
    linestyle="--",
)
plt.xlabel("Actual Net USD")
plt.ylabel("Predicted Net USD")
plt.title("Robust Linear Model: Actual vs Predicted Net USD")
plt.xscale("log")
plt.yscale("log")
plt.show()


# --------------------------------------------------
# Export results
# --------------------------------------------------
user_stats.to_csv("user_stats_summary.csv")
print("User stats saved to user_stats_summary.csv")