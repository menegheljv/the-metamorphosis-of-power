# Public Data Intelligence — análise inteiramente demonstrativa.
# install.packages(c("tidyverse", "shiny", "DT")) # uma única vez
library(tidyverse)
library(ggplot2)

dados <- read_csv("../data/synthetic_public_data.csv", show_col_types = FALSE) |>
  pivot_longer(c(participacao, acesso_digital, transparencia),
               names_to = "indicador", values_to = "valor")

resumo <- dados |> group_by(indicador, period) |>
  summarise(media = mean(valor), .groups = "drop")
print(resumo)

grafico <- ggplot(dados, aes(period, valor, colour = region, group = region)) +
  geom_line(linewidth = 1) + geom_point() + facet_wrap(~indicador) +
  labs(title = "Indicadores sintéticos por região", x = NULL, y = "Valor") +
  theme_minimal()
ggsave("analysis/indicadores.png", grafico, width = 10, height = 6)

# Execute com: shiny::runApp("analysis")
