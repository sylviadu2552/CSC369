# users_EDA.py
# Dask-based exploratory data analysis (EDA) for cleaned users.parquet (~32GB)

import dask.dataframe as dd
import matplotlib.pyplot as plt

# --------------------------
# Load the dataset
# --------------------------
df_users = dd.read_parquet('users.parquet')

print("Columns in dataset:", df_users.columns)
print("Number of rows (lazy evaluation):", len(df_users))

# --------------------------
# Data sanity checks
# --------------------------

# Check for missing values per column
missing_values = df_users.isna().sum().compute()
print("\nMissing values per column:\n", missing_values)

# Inspect price range
min_price = df_users['price'].min().compute()
max_price = df_users['price'].max().compute()
print(f"\nPrice range: {min_price:.2f} to {max_price:.2f}")

# Inspect token amount range
min_tokens = df_users['token_amount'].min().compute()
max_tokens = df_users['token_amount'].max().compute()
print(f"Token amount range: {min_tokens} to {max_tokens}")

# Distribution of roles
role_distribution = df_users['role'].value_counts().compute()
print("\nRole distribution:\n", role_distribution)

# Trades per user statistics
user_trade_counts = df_users.groupby('user')['token_amount'].count().compute()
print("\nTrades per user statistics:\n", user_trade_counts.describe())

# --------------------------
# User net positions per market
# --------------------------
user_net_positions = df_users.groupby(['user', 'market_id'])['token_amount'].sum().compute()

# Positive positions
user_long_positions = user_net_positions[user_net_positions > 0]
# Negative positions
user_short_positions = user_net_positions[user_net_positions < 0]

print("\nNet positions summary:")
print("Positive positions (long):", user_long_positions.describe())
print("Negative positions (short):", user_short_positions.describe())

# --------------------------
# Time coverage
# --------------------------
earliest_time = df_users['datetime'].min().compute()
latest_time = df_users['datetime'].max().compute()
print(f"\nTime coverage: {earliest_time} to {latest_time}")

# --------------------------
# Exploratory plots (sampled for memory efficiency)
# --------------------------
sample_fraction = 0.01  # 1% sample
df_sample = df_users.sample(frac=sample_fraction).compute()

# a) Price distribution
plt.figure(figsize=(8,5))
df_sample['price'].hist(bins=50)
plt.xlabel('YES token probability')
plt.ylabel('Count')
plt.title('Price Distribution (1% Sample)')
plt.show()

# b) Trades per user histogram (sample)
plt.figure(figsize=(8,5))

sample_trade_counts = df_sample.groupby('user')['token_amount'].count()
sample_trade_counts.clip(upper=200).hist(bins=50)

plt.yscale('log')  

plt.xlabel('Trades per user (clipped at 200)')
plt.ylabel('Count (log scale)')
plt.title('User Trade Activity')
plt.show()

# c) Net positions histogram (sample)
plt.figure(figsize=(8,5))

sample_net_positions = df_sample.groupby('user')['token_amount'].sum()
sample_net_positions.clip(-1000, 1000).hist(bins=50)

plt.yscale('log')

plt.xlabel('Net YES tokens (clipped)')
plt.ylabel('Count (log scale)')
plt.title('User Net Positions')
plt.show()

# d) Role distribution pie chart
plt.figure(figsize=(6,6))

sample_role_counts = df_sample['role'].astype(str).value_counts()

plt.pie(sample_role_counts,
        labels=sample_role_counts.index,
        autopct='%1.1f%%')

plt.title('Maker vs Taker')
plt.show()

# --------------------------
# Top 10 most active users
# --------------------------
top_10_users = user_trade_counts.nlargest(10)
print("\nTop 10 most active users:\n", top_10_users)
