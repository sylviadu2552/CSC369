# Response to Feedback

## Feedback Received
> "You do a good job in your intro of establishing the setting and hypothesis. Given Polymarket isn't something everyone will have heard of before, I think it would help to write another sentence or two explaining it. I like some of your EDA, it feels a little misplaced to go so into depth in a writeup like this. Your Figure 5: Net USD vs Maker Ratio by Cluster should be cleaned up to be much more understandable. Same with your Figure 6. Same with your predicted vs actual net USD chart. It also makes me question the value of the trend line you have there given the data that is plotted. Your writeup on your analysis is high quality overall."

## How I Addressed Each Point

### 1. Polymarket Explanation
**Original Issue:** The introduction assumed familiarity with Polymarket, which may not be accurate for all readers.  

**Revision:** Added two sentences explaining Polymarket's mechanics with a concrete example:

> "Every token is priced between $0 and $1, representing the market’s estimated probability of that outcome. For example, if YES shares for a market trade at $0.65, the market assigns roughly a 65% chance of the event occurring. A user might buy 50 YES tokens at $0.65 each on a given market and if the event occurs, each token pays $1, otherwise the tokens are worthless."

This provides context without overwhelming the reader, making the analysis accessible to those unfamiliar with prediction markets.

### 2. EDA Depth and Placement
**Original Issue:** The EDA section felt too deep for a writeup of this scope.  

**Revision:** Streamlined the EDA section while preserving key insights:

- Combined three separate histograms into a single **Figure 1** with subplots, reducing visual clutter while maintaining the core message about distributional skew.  
- Accompanying text now focuses on key takeaways rather than walking through each plot in exhaustive detail.

### 3. Figure 5: Net USD vs Maker Ratio by Cluster
**Original Issue:** The scatterplot was difficult to interpret due to overplotting and extreme skew.  

**Revision:** Replaced the scatterplot with a **hexbin density plot (Figure 3)** showing the relationship between maker ratio and log-transformed net USD:

- Handles overplotting effectively by showing density.  
- Uses log scaling to reveal patterns across the full profit spectrum.  
- Includes a colorbar showing user density on a log scale.  
- Clearly shows concentration of users at low maker ratios and the upward trend toward higher profits.

This makes the relationship between maker activity and profitability visually apparent while honestly representing the data's structure.

### 4. Figure 6: Net USD vs Low Probability Fraction
**Original Issue:** Similar clarity problems as Figure 5.  

**Revision:** Removed this figure from the main text. Relationship is now addressed through:

- Welch t-test comparing high vs. low risk engagement.  
- Robust regression model, including `low_prob_fraction` and its interaction with `maker_ratio`.  
- Clear textual explanation of the negative association.

Some relationships are better communicated through statistical summaries than noisy scatterplots, especially given extreme skew.

### 5. Predicted vs Actual Chart and Trend Line
**Original Issue:** The predicted vs actual scatterplot was unclear, and the trend line's value was questionable.  

**Revision:** Removed the figure entirely and added:

- **Figure 4:** Lorenz Curve showing profit concentration.  
- **Figure 5:** Pareto Plot highlighting the disproportionate impact of top users.  
- **Gini coefficient calculation (0.934)** quantifying inequality.  
- Cluster summary table providing clear numerical comparisons.  

Regression results are now communicated through a structured coefficient table with interpretations, more appropriate for a technical audience. The removal acknowledges that the model is explanatory (behavioral relationships) rather than predictive, a distinction now clarified in the text.

### 6. Additional Improvements
- **Elbow Method:** Added to justify the choice of 4 clusters empirically.  
- **Effect Size:** Included with ANOVA results to quantify practical significance.  
- **Cluster Summary Table:** Provides clear, interpretable comparisons.  
- **Log Scaling Consistently Applied:** All profit visualizations now use log scaling where appropriate.  
- **More Precise Language:** Revised interpretations to acknowledge observational limitations and potential confounders.