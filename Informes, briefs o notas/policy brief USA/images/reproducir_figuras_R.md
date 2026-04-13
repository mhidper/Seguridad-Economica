# Reproduction of Figures in R

This document provides R code to reproduce the figures for the Policy Brief USA using the processed data in the `images/` directory.

## Prerequisites
You will need the following R libraries installed:
```r
install.packages(c("ggplot2", "dplyr", "tidyr", "readr", "forcats"))
```

---

## 1. Figure 2: U.S. Trade Dependency by Sector
Reproduces the stacked bar chart of U.S. dependency on other countries.

```r
library(ggplot2)
library(dplyr)
library(tidyr)
library(readr)

# Load data
df <- read_csv("figura2.csv")

# Sector translation
sector_mapping <- c(
  "manufacturas" = "Manufacturing", 
  "agricultura" = "Agriculture", 
  "servicios" = "Services", 
  "minería y energía" = "Mining & Energy"
)

# Country translation
country_mapping <- c(
  "China" = "China", "México" = "Mexico", "Vietnam" = "Vietnam", 
  "Canadá" = "Canada", "Japón" = "Japan", "RUS" = "Russia", 
  "Taiwán" = "Taiwan", "Alemania" = "Germany", "Irlanda" = "Ireland", 
  "Corea del Sur" = "South Korea", "India" = "India", "Tailandia" = "Thailand", 
  "Malasia" = "Malaysia", "Suiza" = "Switzerland", "Francia" = "France", 
  "Brasil" = "Brazil", "Italia" = "Italy", "Reino Unido" = "United Kingdom", 
  "Países Bajos" = "Netherlands", "Bermudas" = "Bermuda", "Singapur" = "Singapore"
)

# Reshape data to long format for ggplot (Sectors)
sectors <- c("manufacturas", "agricultura", "servicios", "minería y energía")

df_long <- df %>%
  pivot_longer(
    cols = starts_with(sectors),
    names_to = "sector_metric",
    values_to = "value"
  ) %>%
  mutate(
    sector = str_split(sector_metric, "_", simplify = TRUE)[,1],
    type = case_when(
      grepl("direct", sector_metric) ~ "Direct",
      grepl("indirect", sector_metric) ~ "Indirect",
      TRUE ~ "Total"
    )
  ) %>%
  filter(type != "Total") %>%
  mutate(
    sector_en = sector_mapping[sector],
    country_en = factor(country_mapping[country_name], levels = country_mapping[df$country_name])
  )

# Totals for dots
df_totals <- df %>%
  pivot_longer(
    cols = ends_with("_weighted_dependency"),
    names_to = "sector",
    values_to = "total_val"
  ) %>%
  filter(sector %in% paste0(sectors, "_weighted_dependency")) %>%
  mutate(
    sector = gsub("_weighted_dependency", "", sector),
    country_en = country_mapping[country_name]
  )

# Plot
ggplot() +
  geom_bar(data = df_long, aes(x = sector_en, y = value * 100, fill = type), stat = "identity") +
  geom_point(data = df_totals, aes(x = sector_mapping[sector], y = total_val * 100), color = "black", size = 2) +
  facet_wrap(~country_en, scales = "free_x", nrow = 4) +
  scale_fill_manual(values = c("Direct" = "#4C51BF", "Indirect" = "#9FA8DA")) +
  labs(
    title = "U.S. Trade Dependency by Sector",
    subtitle = "Weighted by Trade Value / Import Value",
    x = "Sector",
    y = "Dependency (%)",
    fill = "Dependency Type"
  ) +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
```

---

## 2. Figure 3: U.S. Sectoral Dependencies on China
Reproduces the horizontal bar chart for top sectors.

```r
# Load data (sep = ";")
df3 <- read_delim("figura3.csv", delim = ";")

# Reorder industries by dependency value
df3 <- df3 %>%
  mutate(short_industry = reorder(short_industry, dependency_value))

# Reshape
df3_long <- df3 %>%
  pivot_longer(
    cols = c(direct_dependency, indirect_dependency),
    names_to = "type",
    values_to = "val"
  ) %>%
  mutate(type = ifelse(type == "direct_dependency", "Direct", "Indirect"))

# Plot
ggplot(df3_long) +
  geom_bar(aes(y = short_industry, x = val, fill = type), stat = "identity", alpha = 0.8) +
  geom_point(data = df3, aes(y = short_industry, x = dependency_value + 0.03, size = trade_value), color = "#d62728", alpha = 0.7) +
  geom_text(data = df3, aes(y = short_industry, x = dependency_value + 0.1, label = sprintf("%.1f%% | %.1fB", dependency_value*100, trade_value/1000)), size = 3, hjust = 0) +
  scale_fill_manual(values = c("Direct" = "#82ca9d", "Indirect" = "#ffc658")) +
  scale_x_continuous(labels = scales::percent, limits = c(0, 1.2)) +
  labs(
    title = "U.S. Sectoral Dependencies on China",
    x = "Dependency Index (%)",
    y = "Industry",
    fill = "Dependency",
    size = "Trade Value"
  ) +
  theme_minimal()
```

---

## 3. Figure 6: Trade Dependency on the United States by Sector
Reproduces the multi-country dependency comparison.

```r
# Load data (sep = ";")
df6 <- read_delim("figura6.csv", delim = ";")

# Translation and Ordering
country_order <- df6 %>%
  group_by(dependent_country) %>%
  summarize(avg = mean(dependency_value)) %>%
  arrange(desc(avg)) %>%
  pull(dependent_country)

sector_translation <- c(
  'manufacturas' = 'Manufacturing', 'agricultura' = 'Agriculture',
  'servicios' = 'Services', 'minería y energía' = 'Mining & Energy'
)

df6_plot <- df6 %>%
  pivot_longer(
    cols = c(direct_dependency, indirect_dependency),
    names_to = "type",
    values_to = "val"
  ) %>%
  mutate(
    type = ifelse(type == "direct_dependency", "Direct", "Indirect"),
    sector_en = sector_translation[sector],
    dependent_country = factor(dependent_country, levels = country_order)
  )

# Plot
ggplot() +
  geom_bar(data = df6_plot, aes(x = sector_en, y = val * 100, fill = type), stat = "identity") +
  geom_point(data = df6, aes(x = sector_translation[sector], y = dependency_value * 100), color = "black") +
  geom_text(data = df6 %>% filter(dependency_value > 0.01), 
            aes(x = sector_translation[sector], y = dependency_value * 100 + 2, label = sprintf("%.1f%%", dependency_value*100)), 
            angle = 90, size = 3) +
  facet_wrap(~dependent_country, scales = "free_x", nrow = 2) +
  scale_fill_manual(values = c("Direct" = "#4C51BF", "Indirect" = "#9FA8DA")) +
  labs(
    title = "Trade Dependency on the United States by Sector",
    x = "Sector",
    y = "Dependency (%)",
    fill = "Type"
  ) +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
```

---
*Generated by Antigravity assistant*
