# users_EDA.py
# Dask-based exploratory data analysis (EDA) for cleaned users.parquet (~32GB)

import dask.dataframe as dd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# --------------------------
# Load the dataset
# --------------------------
df_users = dd.read_parquet('users_filtered.parquet')

print("Columns in dataset:", df_users.columns)
print("Number of rows (lazy evaluation):", len(df_users))

# --------------------------
# Data sanity checks
# --------------------------
missing_values = df_users.isna().sum().compute()
print("\nMissing values per column:\n", missing_values)

min_price = df_users['price'].min().compute()
max_price = df_users['price'].max().compute()
print(f"\nPrice range: {min_price:.2f} to {max_price:.2f}")

min_tokens = df_users['token_amount'].min().compute()
max_tokens = df_users['token_amount'].max().compute()
print(f"Token amount range: {min_tokens} to {max_tokens}")

# --------------------------
# User-level aggregates
# --------------------------
user_net_tokens = df_users.groupby('user')['token_amount'].sum().compute()
user_trade_counts = df_users.groupby('user')['token_amount'].count().compute()

# --------------------------
# Sample for plotting (memory efficient)
# --------------------------
sample_fraction = 0.01
df_sample = df_users.sample(frac=sample_fraction).compute()

# User-level aggregates on sample
sample_trade_counts = df_sample.groupby('user')['token_amount'].count()
sample_net_positions = df_sample.groupby('user')['token_amount'].sum()

# --------------------------
# Combined EDA plots
# --------------------------
sns.set(style="whitegrid", context="talk")
fig, axes = plt.subplots(1, 3, figsize=(20, 5))

# 1) Price distribution
sns.histplot(df_sample['price'], bins=50, ax=axes[0], color='skyblue')
axes[0].set_title('Price Distribution')
axes[0].set_xlabel('YES token probability')
axes[0].set_ylabel('Count')

# 2) Trades per user (clipped)
sns.histplot(sample_trade_counts.clip(upper=200), bins=50, ax=axes[1], color='salmon')
axes[1].set_title('Trades per User (Clipped at 200)')
axes[1].set_xlabel('Total Trades')
axes[1].set_ylabel('Count (log scale)')
axes[1].set_yscale('log')

# 3) Net token positions (clipped)
sns.histplot(sample_net_positions.clip(-1000, 1000), bins=50, ax=axes[2], color='limegreen')
axes[2].set_title('Net Token Positions per User')
axes[2].set_xlabel('Net YES tokens')
axes[2].set_ylabel('Count (log scale)')
axes[2].set_yscale('log')

plt.tight_layout()
plt.show()

# --------------------------
# Role distribution pie chart
# --------------------------
role_counts = df_sample['role'].astype(str).value_counts()
plt.figure(figsize=(6,6))
plt.pie(role_counts, labels=role_counts.index, autopct='%1.1f%%', startangle=140, colors=['#66b3ff','#ff9999'])
plt.title('Maker vs Taker Roles')
plt.show()

# --------------------------
# Top 10 most active users
# --------------------------
top_10_users = user_trade_counts.nlargest(10)
print("\nTop 10 most active users:\n", top_10_users)
