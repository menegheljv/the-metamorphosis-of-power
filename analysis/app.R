library(shiny)
library(tidyverse)

dados <- read_csv("../data/synthetic_public_data.csv", show_col_types = FALSE) |>
  pivot_longer(c(participacao, acesso_digital, transparencia),
               names_to = "indicador", values_to = "valor")
ui <- fluidPage(
  titlePanel("Public Data Intelligence · análise sintética"),
  p("Demonstração educacional: valores fictícios, sem alegações eleitorais."),
  sidebarLayout(
    sidebarPanel(selectInput("indicador", "Indicador", choices = unique(dados$indicador))),
    mainPanel(plotOutput("serie"))
  )
)
server <- function(input, output) {
  output$serie <- renderPlot({
    dados |> filter(indicador == input$indicador) |>
      ggplot(aes(period, valor, colour = region, group = region)) +
      geom_line(linewidth = 1) + geom_point() + theme_minimal() +
      labs(x = NULL, y = "Valor")
  })
}
shinyApp(ui, server)
