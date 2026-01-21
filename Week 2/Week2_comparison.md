# Week 2: Comparison of Implementation Strategies
## Pandas
Pandas was rather pretty easy to write I suppose since I'm the most familiar with Pandas and there's already built in functions, but i was still slower than DuckDB and Polars for large datasets like this one. As my memory couldn't hold, I had to chunk the data which adds extra complexity since each chunk has to be processed separately. You also have to manually merge the results across chunks. This one also ran the slowest for all three time frames by quite a comparable amount of time. 
## Polars (Streaming + Parquet)
Polars was the fastest for the one hour time frame and through using the streaming method, it enabled optimizations by reading only the needed columns and parallelizing tasks, preventing memory crashes. Polars also provided by streaming and eager method, contrary to Pandas which only follows the eager method. However, Pandas was slightly slower than DuckDB when the filtered time window is larger. Also, the API seems to change frequently between versions, making it the hardest to write. 
## DuckDB (SQL + Parquet)
DuckDB was faster for the three and six hour time frame, and SQL made filtering and aggregation simple. It was also fast and memory-efficient and there's automatic query optimization. A con to DuckDB would probably be you have to know SQL syntax and it's less "Python" than Pandas or Polars. 

## Favorite Approach
My favorite approach was DuckDB. It was consistently fast across all time windows and handled the larger timestamp ranges more efficiently than the other tools. Additionally, I’m already familiar with SQL from last quarter, so DuckDB felt the most natural and easy to write.