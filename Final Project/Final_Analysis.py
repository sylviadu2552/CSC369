import dask.dataframe as dd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

import statsmodels.api as sm
from scipy import stats
from matplotlib.colors import LogNorm


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

DATA_PATH = "/Users/sylviadu/Documents/CS 369/users_filtered.parquet"
RANDOM_STATE = 42

sns.set(style="whitegrid", context="talk")


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

print("Loading dataset...")

users = dd.read_parquet(DATA_PATH)

users["is_maker"] = (users["role"] == "maker").astype(int)
users["low_prob_trade"] = (users["price"] < 0.1).astype(int)

users["trade_value"] = users["token_amount"] * users["price"]

users["datetime"] = dd.to_datetime(users["datetime"])


# --------------------------------------------------
# USER LEVEL AGGREGATION
# --------------------------------------------------

print("Aggregating user statistics...")

user_stats = users.groupby("user").agg(

    net_usd=("usd_amount","sum"),
    maker_ratio=("is_maker","mean"),
    total_trades=("usd_amount","count"),
    low_prob_fraction=("low_prob_trade","mean"),
    trade_value_std=("trade_value","std")

).compute()

user_stats = user_stats.fillna(0)

print(user_stats.head())


# --------------------------------------------------
# CLUSTERING USERS
# --------------------------------------------------

print("Running KMeans clustering...")

cluster_features = user_stats[
    ["maker_ratio","low_prob_fraction","total_trades"]
]

scaler = StandardScaler()

X_scaled = scaler.fit_transform(cluster_features)

kmeans = KMeans(n_clusters=4, random_state=RANDOM_STATE)

user_stats["cluster"] = kmeans.fit_predict(X_scaled)

# --------------------------------------------------
# ELBOW METHOD FOR OPTIMAL K
# --------------------------------------------------

print("Running Elbow Method...")

cluster_features = user_stats[
    ["maker_ratio","low_prob_fraction","total_trades"]
]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(cluster_features)

inertia = []
k_values = range(1,11)

for k in k_values:
    km = KMeans(n_clusters=k, random_state=RANDOM_STATE)
    km.fit(X_scaled)
    inertia.append(km.inertia_)

plt.figure(figsize=(8,6))
plt.plot(k_values, inertia, marker="o")

plt.xlabel("Number of Clusters (k)")
plt.ylabel("Inertia (Within Cluster SSE)")
plt.title("Elbow Method for Optimal Number of Clusters")

plt.xticks(k_values)
plt.show()


# --------------------------------------------------
# CLUSTER SUMMARY
# --------------------------------------------------

cluster_summary = user_stats.groupby("cluster").agg(

    users=("net_usd","count"),
    avg_net_usd=("net_usd","mean"),
    median_net_usd=("net_usd","median"),
    avg_maker_ratio=("maker_ratio","mean"),
    avg_low_prob=("low_prob_fraction","mean"),
    avg_trades=("total_trades","mean")

)

print("\nCluster Summary")
print(cluster_summary)


# --------------------------------------------------
# STATISTICAL TESTS
# --------------------------------------------------

print("\nRunning statistical tests...")

groups = [

    user_stats[user_stats["cluster"] == i]["net_usd"]

    for i in range(4)

]

f_stat, p_val = stats.f_oneway(*groups)

print(f"ANOVA: F={f_stat:.2f}, p={p_val:.3e}")


# Effect size

ss_between = sum(

    len(g) * (g.mean() - user_stats["net_usd"].mean())**2

    for g in groups

)

ss_total = ((user_stats["net_usd"] - user_stats["net_usd"].mean())**2).sum()

eta_sq = ss_between / ss_total

print(f"ANOVA effect size (eta²): {eta_sq:.3f}")


# Spearman correlation

corr, p_corr = stats.spearmanr(

    user_stats["maker_ratio"],
    user_stats["net_usd"]

)

print(f"Spearman correlation: rho={corr:.3f}, p={p_corr:.3e}")


# Welch t-test

median_risk = user_stats["low_prob_fraction"].median()

high_risk = user_stats[user_stats["low_prob_fraction"] > median_risk]["net_usd"]

low_risk = user_stats[user_stats["low_prob_fraction"] <= median_risk]["net_usd"]

t_stat, p_t = stats.ttest_ind(high_risk, low_risk, equal_var=False)

print(f"Welch t-test: t={t_stat:.2f}, p={p_t:.3e}")


# --------------------------------------------------
# ROBUST REGRESSION
# --------------------------------------------------

print("\nRunning robust regression...")

y_log = np.log1p(user_stats["net_usd"])

X = pd.get_dummies(

    user_stats[["maker_ratio","low_prob_fraction","cluster"]],
    columns=["cluster"],
    drop_first=True

)

X["maker_lowprob_interaction"] = (
    X["maker_ratio"] * X["low_prob_fraction"]
)

X = sm.add_constant(X)

model = sm.RLM(
    y_log,
    X.astype(float),
    M=sm.robust.norms.HuberT()
).fit()

print(model.summary())

user_stats["pred_log_net_usd"] = model.fittedvalues


# --------------------------------------------------
# FIGURE 2: CLUSTER PROFITABILITY
# --------------------------------------------------

cluster_palette = sns.color_palette("pastel", n_colors=user_stats["cluster"].nunique())
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

sns.boxplot(
    data=user_stats,
    x="cluster",
    y=np.log1p(user_stats["net_usd"]),
    palette=cluster_palette,
    ax=axes[0]
)
axes[0].set_xlabel("Cluster")
axes[0].set_ylabel("Log(Net USD)")
axes[0].set_title("Profitability by User Cluster")

sns.boxplot(
    data=user_stats,
    x="cluster",
    y=user_stats["maker_ratio"].clip(0,1),
    palette=cluster_palette,
    ax=axes[1]
)
axes[1].set_xlabel("Cluster")
axes[1].set_ylabel("Maker Ratio")
axes[1].set_title("Maker Ratio by User Cluster")
axes[1].set_ylim(0,1)  

plt.tight_layout()
plt.savefig("cluster_analysis_combined_fixed.png", dpi=300)
plt.show()


# --------------------------------------------------
# FIGURE 3: DENSITY (HEXBIN WITH LOG SCALE)
# --------------------------------------------------

plt.figure(figsize=(9,6))

plt.hexbin(
    user_stats["maker_ratio"],
    np.log1p(user_stats["net_usd"]),
    gridsize=40,
    cmap="viridis",
    norm=LogNorm()
)

plt.colorbar(label="User Density (log scale)")

plt.xlabel("Maker Ratio")
plt.ylabel("Log(Net USD)")

plt.title("Density of Profit vs Maker Participation")

plt.show()


# --------------------------------------------------
# FIGURE 4: LORENZ CURVE
# --------------------------------------------------

profits = user_stats["net_usd"].copy()

profits = profits[profits > 0]

profits_sorted = np.sort(profits)

cum_users = np.arange(1,len(profits_sorted)+1) / len(profits_sorted)

cum_profit = np.cumsum(profits_sorted) / profits_sorted.sum()

plt.figure(figsize=(8,6))

plt.plot(cum_users, cum_profit, label="Observed Profit Distribution")

plt.plot([0,1],[0,1], linestyle="--", label="Perfect Equality")

plt.xlabel("Cumulative Share of Users")
plt.ylabel("Cumulative Share of Profits")

plt.title("Profit Concentration Among Traders")

plt.legend()

plt.show()


# --------------------------------------------------
# GINI COEFFICIENT
# --------------------------------------------------

print("\nCalculating Gini coefficient...")

profits = user_stats["net_usd"].values

profits = profits - profits.min()
profits = profits + 1e-9

profits_sorted = np.sort(profits)

n = len(profits)

cumprofits = np.cumsum(profits_sorted)

gini = (n + 1 - 2*np.sum(cumprofits)/cumprofits[-1]) / n

print(f"Gini coefficient: {gini:.3f}")


# --------------------------------------------------
# FIGURE 5: PARETO PROFIT CONCENTRATION
# --------------------------------------------------

profits = user_stats["net_usd"].sort_values(ascending=False)

cum_profit_share = profits.cumsum() / profits.sum()

user_share = np.arange(1,len(profits)+1) / len(profits)

plt.figure(figsize=(8,6))

plt.plot(user_share, cum_profit_share)

plt.xlabel("Share of Users (Highest Profit First)")
plt.ylabel("Cumulative Share of Profit")

plt.title("Pareto Distribution of Trading Profits")

plt.show()


# --------------------------------------------------
# EXPORT RESULTS
# --------------------------------------------------

user_stats.to_csv("user_stats_summary.csv")
cluster_summary.to_csv("cluster_summary.csv")

print("\nResults exported.")

