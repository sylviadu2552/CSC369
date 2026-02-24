import dask.dataframe as dd

# -----------------------------------------------------
# Load dataset
# -----------------------------------------------------
print("Loading original dataset...")
users = dd.read_parquet("users.parquet")

# Convert datetime column
users["datetime"] = dd.to_datetime(users["datetime"])


# -----------------------------------------------------
# 1. Time filter (largest reduction step)
# -----------------------------------------------------
print("Filtering by time...")

users = users[
    (users["datetime"] >= "2024-01-01") &
    (users["datetime"] < "2025-01-01")
]


# -----------------------------------------------------
# 2. Remove micro trades (reduce noise)
# -----------------------------------------------------
print("Removing tiny trades...")

users = users[abs(users["token_amount"]) > 1]


# -----------------------------------------------------
# 3. Keep only active markets
# -----------------------------------------------------
print("Finding active markets...")

market_counts = users.groupby("market_id").size().compute()
active_markets = market_counts[market_counts > 5000].index

users = users[users["market_id"].isin(active_markets)]


# -----------------------------------------------------
# 4. Keep only active users
# -----------------------------------------------------
print("Finding active users...")

user_counts = users.groupby("user").size().compute()
active_users = user_counts[user_counts > 20].index

users = users[users["user"].isin(active_users)]


# -----------------------------------------------------
# 5. Save filtered dataset
# -----------------------------------------------------
print("Writing filtered parquet (this may take a while)...")

users.to_parquet(
    "users_filtered.parquet",
    write_index=False
)

print("✅ Done. New dataset saved as users_filtered.parquet")