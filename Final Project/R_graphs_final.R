library(ggplot2)

# Five-number summary
five_num <- data.frame(
  x = 1,
  ymin = 1,
  lower = 9,
  middle = 24,
  upper = 58,
  ymax = 5390134
)

# Create the boxplot
ggplot(five_num, aes(x = factor(x))) +
  geom_boxplot(aes(
    ymin = ymin,
    lower = lower,
    middle = middle,
    upper = upper,
    ymax = ymax
  ), stat = "identity", fill = "skyblue", color = "black", width = 0.3) +
  
  # Add numerical labels above the box, slightly lower than before
  geom_text(aes(x = factor(x), y = ymin, label = ymin), color = "black", vjust = -8) +
  geom_text(aes(x = factor(x), y = lower, label = lower), color = "black", vjust = -8) +
  geom_text(aes(x = factor(x), y = middle, label = middle), color = "black", vjust = -8) +
  geom_text(aes(x = factor(x), y = upper, label = upper), color = "black", vjust = -8) +
  geom_text(aes(x = factor(x), y = ymax, label = ymax), color = "black", vjust = -8) +
  
  scale_y_log10() +
  coord_flip() +
  labs(title = "Trades Per User Summary",
       x = "",
       y = "Number of Trades (log scale)") +
  theme_minimal()

#######################################################################################
# Five-number summary for net positions
five_num_net <- data.frame(
  x = 1,
  ymin = 0,
  lower = 2.9,
  middle = 16.67,
  upper = 111.11,
  ymax = 2.947307e+07
)

# Create the boxplot
ggplot(five_num_net, aes(x = factor(x))) +
  geom_boxplot(aes(
    ymin = ymin,
    lower = lower,
    middle = middle,
    upper = upper,
    ymax = ymax
  ), stat = "identity", fill = "lightgreen", color = "black", width = 0.3) +
  
  # Add numerical labels above the box
  geom_text(aes(x = factor(x), y = ymin, label = ymin), color = "black", vjust = -8) +
  geom_text(aes(x = factor(x), y = lower, label = lower), color = "black", vjust = -8) +
  geom_text(aes(x = factor(x), y = middle, label = middle), color = "black", vjust = -8) +
  geom_text(aes(x = factor(x), y = upper, label = upper), color = "black", vjust = -8) +
  geom_text(aes(x = factor(x), y = ymax, label = ymax), color = "black", vjust = -8) +
  
  scale_y_log10() +
  coord_flip() +
  labs(title = "Net Positive Positions Summary",
       x = "",
       y = "Token Amount (log scale)") +
  theme_minimal()


#######################################################################################
library(ggplot2)

# Five-number summary for negative positions
five_num_neg <- data.frame(
  x = 1,
  ymin = -2.940751e+07,
  lower = -66.66,
  middle = -10,
  upper = -1.37,
  ymax = 0
)

# Create the boxplot
ggplot(five_num_neg, aes(x = factor(x))) +
  geom_boxplot(aes(
    ymin = ymin,
    lower = lower,
    middle = middle,
    upper = upper,
    ymax = ymax
  ), stat = "identity", fill = "salmon", color = "black", width = 0.3) +
  
  # Add numerical labels above the box
  geom_text(aes(x = factor(x), y = ymin, label = ymin), color = "black", vjust = -8) +
  geom_text(aes(x = factor(x), y = lower, label = lower), color = "black", vjust = -8) +
  geom_text(aes(x = factor(x), y = middle, label = middle), color = "black", vjust = -8) +
  geom_text(aes(x = factor(x), y = upper, label = upper), color = "black", vjust = -8) +
  geom_text(aes(x = factor(x), y = ymax, label = ymax), color = "black", vjust = -8) +
  
  # Pseudo-log transformation keeps negative values visible
  scale_y_continuous(trans = "pseudo_log") +
  coord_flip() +
  labs(title = "Net Negative Positions Summary",
       x = "",
       y = "Token Amount (pseudo-log scale)") +
  theme_minimal()


