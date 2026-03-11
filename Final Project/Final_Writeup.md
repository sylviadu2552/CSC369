# Final Project Whitepaper: User Trading Analysis

## Introduction

This study analyzes user trading behavior on Polymarket, a cryptocurrency-based prediction market where participants buy and sell “yes/no” tokens on the outcomes of future events. Every token is priced between $0 and $1, representing the market’s estimated probability of that outcome. For example, if YES shares for a market trade at $0.65, the market assigns roughly a 65% chance of the event occurring. A user might buy 50 YES tokens at $0.65 each on a given market and if the event occurs, each token pays $1, otherwise the tokens are worthless. Users can act as makers, setting prices and providing liquidity, or as takers, accepting existing prices.

The dataset covers all trades made during 2024. The primary goal of this project is to understand how trading style, activity level, and risk-taking behavior influence profitability and overall market outcomes.

I hypothesize that a small fraction of highly active users drives most of the trading volume, and that users who frequently act as market makers while avoiding extremely low-probability trades earn higher profits. This project also investigates whether distinct clusters of users exhibit consistent behavioral patterns.


## Data & Methodology

To ensure meaningful analysis, the raw dataset of user trades was carefully filtered to remove noise and focus on relevant activity:

1. **Time Filtering**  
   Only trades occurring between January 1, 2024, and December 31, 2024, were retained. This limits the analysis to a consistent, recent time period and eliminates outdated data that could bias results.

2. **Removal of Micro Trades**  
   Trades involving negligible token amounts (≤1) were excluded. These small trades often represent noise, automated testing, or outliers that do not reflect meaningful user behavior.

3. **Focus on Active Markets**  
   Markets with fewer than 5,000 trades were excluded. By concentrating on liquid, high-volume markets, the analysis captures environments where trading behavior is most significant.

4. **Focus on Active Users**  
   Users with fewer than 20 trades over the year were excluded to remove occasional or inactive participants. This ensures statistical relevance and reduces sparsity in the dataset.

5. **Feature Engineering**
   Several derived metrics were computed to capture meaningful aspects of user behavior:
   - `maker_ratio`: fraction of trades in which the user acted as a market maker.  
   - `low_prob_fraction`: fraction of trades with price < 0.1 (representing high-risk or low-probability trades).  
   - `profit_proxy_std`: standard deviation of the profit proxy (`token_amount * price`) as a measure of trading volatility.  
   - `7-day rolling net USD`: capturing short-term temporal patterns in profit accumulation.

The resulting filtered dataset provides a cleaner, more representative view of trading behavior across both users and markets. Because the dataset contains trade-level information but not full market settlement outcomes, a proxy for profitability was used. Net USD reflects the cumulative cash flow from executed trades. While this does not represent final realized profit after market resolution, it provides a consistent measure of trading performance and capital flow across users.

## Analytical Approach

1. **Descriptive Metrics**  
   The distributions of key trading metrics are highly skewed, supporting the hypothesis that a small fraction of users drive most market activity. Summary statistics for all users were computed, including total net USD, maker ratio, total trades, low-probability trade fraction, and profit volatility.

   Due to the large size of the dataset, visualizations were generated from a 1% random sample to maintain memory efficiency while still capturing overall patterns.

   **Figure 1: User Trading Activity (1% Sample, Three Histograms Combined)**  
   ![Figure 1: Combined histograms of price distribution, trades per user, and net token positions](https://i.imgur.com/1yb8HI6.png) 

   - **Price Distribution:** Most trades occur at very low probabilities (near $0), with a small fraction at higher prices. This indicates that impactful trades are concentrated among a few higher-probability positions.  
   - **Trades per User:** The majority of users make relatively few trades, while a small subset of highly active users dominates overall trading volume.  
   - **Net Token Positions:** Most users hold near-neutral positions, but extreme positions exist in both directions, reflecting the presence of super-active, high-impact traders.    

2. **Clustering**  
Users were grouped using KMeans clustering based on three key behavioral metrics: `maker_ratio`, `low_prob_fraction`, and total trades. The variables were standardized prior to clustering to ensure differences in scale did not dominate the algorithm. The optimal number of clusters was evaluated using the elbow method, which examines the within-cluster sum of squares as the number of clusters increases. The elbow occurred at k = 4, indicating that four clusters provided a good balance between model complexity and explanatory power. This analysis revealed four distinct clusters, summarized in Table 1:

      | Cluster |   Users | Avg Net USD | Median Net USD | Avg Maker Ratio | Avg Low Prob | Avg Trades |
      | ------- | ------: | ----------: | -------------: | --------------: | -----------: | ---------: |
      | 0       | 129,457 |       9,238 |            201 |           0.129 |        0.944 |        101 |
      | 1       | 111,476 |       9,683 |          2,234 |           0.039 |        0.077 |         68 |
      | 2       |  44,974 |      86,325 |          7,341 |           0.696 |        0.279 |        418 |
      | 3       |      22 |  18,751,660 |      4,377,093 |           0.823 |        0.730 |    382,846 |


   **Table 1:** Summary statistics by cluster.

   An **ANOVA** indicates that `net_usd` differs significantly across clusters (F = 11,334, p < 0.001), suggesting that user behavior strongly drives profitability.  However, due to the heavy-tailed distribution, the results should be interpreted with caution. 

   **Figure 2: User Profitability and Maker Activity by Cluster**  
   ![Figure 2: Net USD and Maker Ratio by Cluster](https://i.imgur.com/BnmOBWT.png)  

   This figure shows **two aspects of user behavior across clusters**:  

   - Left plot: Log-transformed net USD per user, highlighting differences in profitability.  
   - Right plot: Maker ratio per user, showing differences in liquidity provision activity.  

   Clusters 0 and 1 contain the majority of users with lower profitability and lower maker ratios. Cluster 2 includes more active and profitable users with higher maker ratios. Cluster 3 is a very small group with extreme net USD and high maker ratios, with potential to be institutional-level traders or even automated strategies. Together, these plots illustrate that user behavior and profitability are highly unevenly distributed across clusters.


3. **Profit vs. Maker Participation**
User behavior in trading can significantly influence profitability. One key behavioral metric is the **maker ratio**, which represents the fraction of trades a user executes as a market maker rather than a taker. Market makers often provide liquidity and may benefit from transaction fees or price advantages, which can translate into higher net earnings.  

   To visualize the relationship between trading behavior and profitability, a **hexbin of `maker_ratio` versus log-transformed net USD (`log1p(net_usd)`)** was plotted:

   **Figure 3: Profit vs Maker Participation**  
   ![Figure 3: Density Plot of Profit vs Maker Participation](https://i.imgur.com/sYaPyoM.png)

   The plot reveals several important patterns:
      - **Concentration at low maker ratios:** The densest hexagons appear at the left side of the plot (low `maker_ratio`), indicating that most users execute relatively few maker trades. These users generally correspond to lower `log(net_usd)` values, confirming that the majority achieve modest profits.
      - **Wider profit dispersion at higher maker ratios:** As `maker_ratio` increases (moving right along the x-axis), the range of `log(net_usd)` expands noticeably and low profits remain common, but the upper profit boundary rises, suggesting that higher maker activity opens the door to greater gains.
      - **High-profit outliers skew toward high maker ratios** While extreme profits occur across the spectrum, the most exceptional outliers concentrate in the upper-right region, where users combine high maker ratios with massive profits. This pattern suggests that market-making behavior is overrepresented among top earners.

   These visual patterns support our hypothesis that trading behavior influences profitability. Users who engage more as market makers have a clearer path to higher profits, highlighting that strategy choices, not just trading volume, affect success.


4. **Statistical Relationships**  
Several statistical analyses were conducted to evaluate the relationships between trading behavior and profitability, focusing on cluster membership, maker activity, and risk engagement.

   #### Spearman Correlation: Maker Ratio and Profitability
   Spearman’s rank correlation was calculated to evaluate the monotonic relationship between `maker_ratio` and `net_usd`.  

   - **Results:** ρ = 0.472, p < 0.001  
   - **Interpretation:** A moderately strong positive correlation indicates that higher maker activity is associated with higher profits. This pattern is consistent with **Figure 3: Density of Profit vs Maker Participation**, suggesting that strategy choices, such as acting as a market maker more frequently, are linked to improved financial performance.

   #### Welch’s t-test: High vs. Low Risk Engagement
   Users were divided based on the median `low_prob_fraction` (fraction of extremely low-probability trades), and a Welch t-test was used to compare mean profits between high- and low-risk engagement groups.  

   - **Results:** t = -7.94, p < 0.001  
   - **Interpretation:** Users with higher engagement in low-probability trades exhibit significantly lower profits compared to those with lower engagement. This supports the notion that excessive involvement in risky trades negatively impacts profitability. 

   #### Summary
   The analyses supports our hypothesis that trading behavior is a significant determinant of profitability:
   - As seen earlier, cluster membership captures behavioral patterns that correspond to differences in earnings.  
   - Maker activity is positively associated with profits.  
   - Controlled risk-taking, avoiding excessive low-probability trades, contributes to stronger financial performance.  


5. **Regression Modeling**  
   To quantify the combined effects of trading behavior and risk engagement on profitability, a robust linear model (RLM) with Huber weighting was fit to the log-transformed `net_usd`. The predictors included:

      - **Maker activity (`maker_ratio`)**  
      - **Risk engagement (`low_prob_fraction`)**  
      - **Cluster membership (`cluster_1`, `cluster_2`, `cluster_3`, with cluster 0 as reference)**  
      - **Interaction term (`maker_ratio * low_prob_fraction`)**  

   The robust regression approach was chosen to account for the heavy-tailed and skewed nature of the profit distribution, which includes extreme outliers.

   #### Key Findings
   | Predictor | Coefficient | Interpretation |
   |-----------|------------|----------------|
   | **Const** | 7.7558 | Baseline log-profit for users in cluster 0 with zero maker activity and zero low-probability trade fraction. |
   | **maker_ratio** | 3.0515 | Positive and highly significant: higher maker activity is strongly associated with increased profitability. This supports the pattern observed in **Figure 3**, where users with higher maker ratios cluster at higher log-profits. |
   | **low_prob_fraction** | -3.6870 | Negative and highly significant: engaging in low-probability trades reduces expected profits. This aligns with the Welch t-test results showing lower profits among high-risk users. |
   | **cluster_1** | 0.4675 | Users in cluster 1 earn slightly higher profits relative to cluster 0, controlling for behavior metrics. |
   | **cluster_2** | -0.8152 | After controlling for maker activity and risk engagement, users in cluster 2 earn lower profits relative to cluster 0. Although cluster 2 shows higher median profits in the raw summary statistics (Table 1), this difference diminishes once trading behavior is accounted for, suggesting that maker activity and risk-taking explain much of the variation between these groups. |
   | **cluster_3** | 5.1147 | Extremely high profits dominate cluster 3, confirming the presence of outliers with disproportionately large earnings. |
   | **maker_lowprob_interaction** | 3.4662 | Significant positive interaction: users who combine high maker activity with higher low-probability trade fractions see an amplified effect on profitability, suggesting that the combined influence of behavior and risk-taking is more nuanced than individual effects alone. |

   #### Interpretation
   The robust regression confirms and extends the patterns observed in earlier analyses:

   1. **Behavior drives profitability:** Maker activity has a strong positive influence on earnings, reinforcing the hypothesis that strategy choice affects success.  
   2. **Risk management is crucial:** Engagement in low-probability trades negatively impacts profitability, indicating that indiscriminate risk-taking is detrimental.  
   3. **Cluster effects highlight heterogeneity:** Cluster 3 contains extreme outliers with massive profits, while clusters 1 and 2 represent more typical traders with moderate earnings. Although cluster 2 shows relatively strong profits in the raw summary statistics (Table 1), the regression results indicate that much of this difference is explained by trading behavior such as maker activity and risk engagement. This suggests that behavioral strategy accounts for much of the variation between clusters.  
   4. **Interactions matter:** The significant interaction term suggests that the effect of maker activity on profits is modified by risk-taking behavior. High-maker users who strategically engage in low-probability trades can see disproportionate gains, highlighting the complexity of trading success.



6. **Profit Concentration**
To assess the distribution of profits across users, both a Lorenz curve and a Pareto plot were examined. These tools illustrate the extent to which earnings are concentrated among a small fraction of traders.

   #### Lorenz Curve
   The Lorenz curve plots the cumulative share of users against the cumulative share of profits:

   **Figure 4: Profit Concentration Among Traders**  
   ![Figure 4: Profit Concentration Among Traders](https://i.imgur.com/g2eMbT4.png)  

   The curve being far below the 45° line shows that profits are extremely concentrated among a small fraction of users. Most users generate only a small portion of total profits, while a very small group captures the majority of earnings. The calculated Gini coefficient of **0.934** indicates extremely unequal profit distribution among users. Most profits are concentrated in a very small fraction of the user base, consistent with the Lorenz curve. This also aligns with cluster-level findings, where cluster 3 contains a tiny group of users responsible for the majority of profits.

   #### Pareto Plot
   The Pareto plot highlights the concentration of profits by ranking users from highest to lowest earnings:

   **Figure 5: Pareto Distribution of Trading Profits**  
   ![Figure 5: Pareto Distribution of Trading Profit](https://i.imgur.com/841h19m.png)  

   The Pareto curve shows that profitability is highly concentrated among a small portion of users. Less than 10% of users account for roughly 80% of total profit, indicating that a small minority of traders generate the majority of gains. This pattern suggests a strongly unequal distribution of trading outcomes.

   Overall, the Lorenz and Pareto analyses provide clear visual and quantitative evidence of profit inequality, supporting the conclusion that user behavior and strategic choices play a pivotal role in profitability.



## Conclusion

The analysis of 2024 trading activity shows that profits on Polymarket are very uneven across users. Most participants made relatively small amounts of net USD, while a small group of traders captured a large share of the total profits. Plots of the profit distribution also show a heavy concentration of low-profit users with a few extreme outliers. Because of this, the extreme values can make it harder to clearly see general behavioral patterns in the raw data.

Despite this heavy skew, statistical analyses reveal consistent and meaningful relationships between trading behavior and profitability. Maker-oriented trading behavior is positively associated with profitability, whereas frequent engagement in extremely low-probability trades tends to reduce earnings. Robust regression results further confirm these relationships and indicate that higher maker activity can partially mitigate the negative effects of risky trading. Clustering analysis also identified distinct behavioral groups of traders, although differences between clusters remain subtle for the majority of users due to the highly unequal distribution of profits.

Overall, the results support the hypothesis that a small subset of highly active and strategically oriented traders drives a disproportionate share of market profits. The findings suggest that trading success is more strongly associated with behavioral strategy—particularly liquidity provision and controlled risk-taking—than with trading activity alone.

However, because this analysis is observational, several potential confounding variables may influence the results. Factors such as trader experience, capital availability, market selection, and the use of automated trading strategies may affect both trading behavior and profitability. As a result, the relationships identified in this study should be interpreted as associations rather than strictly causal effects. Results may also not generalize to other markets or time periods. 

## Next Steps / Extensions

Several avenues exist for extending this project to gain deeper insights into user trading behavior:

1. **Predictive Modeling**  
   Incorporating models such as Random Forests or time-series forecasting could improve predictions of trading outcomes and provide a more rigorous assessment of the predictability of different user strategies.

2. **Market-Specific Analysis**  
   Examining individual markets may reveal whether the advantages of maker activity or the effects of risky trading vary across liquidity conditions, providing a finer-grained understanding of market dynamics.

3. **Longitudinal Study of Users**  
   Tracking users over time could uncover whether trading strategies evolve or whether participants shift between behavioral clusters, offering insights into learning, adaptation, and experience effects in trading behavior.

By pursuing these next steps, the analysis can be made more precise, interpretable, and informative, ultimately providing a clearer picture of the behavioral and strategic factors that drive trading success in prediction markets.