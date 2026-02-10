# Research Proposal: Exploring Polymarket Data

## 1. Question
I’m really interested in prediction markets and how people make decisions when real money is involved. For this project, I want to explore **either market-level trends (`quant.parquet`) or user-level behavior (`users.parquet`)** in Polymarket:  

- **Market-level:** How do prices and trading volumes evolve over time? Can spikes or drops reveal inefficiencies or trends?  
- **User-level:** How do individual traders behave? Are some consistently better predictors, or do most follow the crowd?  

Basically, I want to see how markets and individual behavior interact.

---

## 2. Why this question is worth answering
I’ve always been fascinated by strategy and prediction, so this dataset is super appealing to me.  
On a broader scale, understanding market dynamics or user behavior is important as it sheds light on various quant and financial aspects, and I do ideally want to go more into the quant/econ side of stats and data analysis.

---

## 3. Hypothesis
- **Market-level:** I suspect that sudden spikes or drops in trading volume or price are often followed by partial corrections, reflecting inefficiencies.  
- **User-level:** I expect that while most users follow trends, a small subset consistently makes better predictions than the crowd.  

These ideas come from observing patterns in financial markets and prior research on prediction markets and just general common consensus on market behavior. 
---

## 4. Dataset
- **Primary dataset:** Polymarket `quant.parquet` (market-level) or `users.parquet` (user-level)  
- **Size:** 21GB (`quant.parquet`) / 23GB (`users.parquet`)  
- **Contents:**  
  - `quant.parquet`: Cleaned, normalized market trades with prices, USD amounts, timestamps, market IDs, and maker/taker roles.  
  - `users.parquet`: User-level trades, split by maker/taker, with signed buy/sell directions, USD amounts, timestamps, and market IDs.  

Both datasets are huge, fully processed, and ready for analysis. I don't know quite yet which perspective I want to focus on, I guess it depends on which question excites me more.

Link: https://huggingface.co/datasets/SII-WANGZJ/Polymarket_data/tree/main (I will say though, I'm not too sure how safe downloading this data would be...)