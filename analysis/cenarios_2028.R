# Cenários para a eleição municipal de 2028 em Alfredo Chaves (ES).
#
# ATENÇÃO: isto é um exercício de CENÁRIOS ("e se..."), não uma previsão. Só há seis eleições
# na série (2004-2024); nenhuma projeção estatística com tão poucos pontos é confiável. Cada
# cenário deixa explícita a hipótese usada. Tudo em R base (não precisa instalar pacotes).
#
# Uso (a partir da raiz do repositório):   Rscript analysis/cenarios_2028.R
# Saídas: output/r_cenarios_2028_*.csv  (lidos por scripts/export_frontend_data.py)

resumo   <- read.csv("output/resumo_prefeito_2004_2024.csv", stringsAsFactors = FALSE)
compar   <- read.csv("output/comparecimento_historico.csv")
distr    <- read.csv("output/distritos_votos_abs.csv", stringsAsFactors = FALSE, fileEncoding = "UTF-8")

# ---------------------------------------------------------------------------
# 1) Eleitorado, comparecimento e votos válidos em 2028
# ---------------------------------------------------------------------------
# Eleitores aptos: tendência linear 2004-2024 (6 pontos) projetada para 2028.
m_aptos <- lm(aptos ~ ano, data = compar)
pred    <- predict(m_aptos, newdata = data.frame(ano = 2028), interval = "prediction", level = 0.80)

# Votos válidos como fração dos aptos = comparecimento x (válidos / comparecimento).
# Hipótese: comparecimento e proporção de válidos ficam entre os valores de 2020 e 2024.
valid_ratio <- resumo$total_votos_validos / compar$comparecimento[match(resumo$ano, compar$ano)]
cmp_2020_24 <- compar$pct_comparecimento[compar$ano %in% c(2020, 2024)] / 100
vr_2020_24  <- valid_ratio[resumo$ano %in% c(2020, 2024)]

cen_eleit <- data.frame(
  cenario         = c("baixo", "base", "alto"),
  aptos           = round(c(pred[, "lwr"], pred[, "fit"], pred[, "upr"])),
  comparecimento  = c(min(cmp_2020_24), mean(cmp_2020_24), max(cmp_2020_24)),
  validos_sobre_comp = c(min(vr_2020_24), mean(vr_2020_24), max(vr_2020_24))
)
cen_eleit$votos_validos <- round(cen_eleit$aptos * cen_eleit$comparecimento * cen_eleit$validos_sobre_comp)
write.csv(cen_eleit, "output/r_cenarios_2028_eleitorado.csv", row.names = FALSE)

# Série histórica de votos válidos + cenário base, para o gráfico
hist <- data.frame(ano = resumo$ano, votos_validos = resumo$total_votos_validos)
base_2028 <- cen_eleit$votos_validos[cen_eleit$cenario == "base"]
write.csv(rbind(hist, data.frame(ano = 2028, votos_validos = base_2028)),
          "output/r_cenarios_2028_serie.csv", row.names = FALSE)

# ---------------------------------------------------------------------------
# 2) O que cada oscilação de votos significa em votos absolutos
# ---------------------------------------------------------------------------
# Hipótese: o candidato do grupo repete o desempenho de 2024 (58,1%) mais uma oscilação uniforme
# de -20 a +5 pontos percentuais. Nas eleições da cidade vence quem tem mais votos (não há 2º turno
# em município com menos de 200 mil eleitores); um terceiro candidato tira votos dos dois lados.
share_2024 <- resumo$pct_candidato_do_grupo[resumo$ano == 2024]
oscilacao  <- c(-20, -15, -10, -5, 0, 5)
terceiro   <- c(0, 5, 10)   # % dos votos válidos de um eventual terceiro candidato

grade <- expand.grid(oscilacao = oscilacao, terceiro = terceiro)
grade$share_grupo <- pmin(share_2024 + grade$oscilacao, 100 - grade$terceiro)
grade$share_oposicao <- 100 - grade$share_grupo - grade$terceiro
grade$votos_grupo    <- round(base_2028 * grade$share_grupo / 100)
grade$votos_oposicao <- round(base_2028 * grade$share_oposicao / 100)
grade$margem_votos   <- grade$votos_grupo - grade$votos_oposicao
grade$vence          <- grade$margem_votos > 0
write.csv(grade, "output/r_cenarios_2028_grade.csv", row.names = FALSE)

# Oscilação máxima que o grupo suporta antes de perder a liderança, para cada terceiro candidato
ponto_de_virada <- data.frame(
  terceiro = terceiro,
  share_minimo_para_vencer = (100 - terceiro) / 2,
  oscilacao_maxima = (100 - terceiro) / 2 - share_2024
)
write.csv(ponto_de_virada, "output/r_cenarios_2028_virada.csv", row.names = FALSE)

# ---------------------------------------------------------------------------
# 3) Faixa histórica de oscilação (ilustrativa)
# ---------------------------------------------------------------------------
# Oscilações do % do grupo entre eleições consecutivas: só cinco observações.
osc_hist <- diff(resumo$pct_candidato_do_grupo)
faixa <- data.frame(
  n_oscilacoes = length(osc_hist),
  media = mean(osc_hist), desvio = sd(osc_hist),
  minimo = min(osc_hist), maximo = max(osc_hist),
  # faixa 10-90% se a oscilação seguisse uma normal com o desvio histórico e média zero
  p10 = share_2024 + qnorm(0.10) * sd(osc_hist),
  p90 = share_2024 + qnorm(0.90) * sd(osc_hist)
)
write.csv(faixa, "output/r_cenarios_2028_faixa.csv", row.names = FALSE)

# ---------------------------------------------------------------------------
# 4) Distritos: oscilação uniforme aplicada ao desempenho de 2024
# ---------------------------------------------------------------------------
d24 <- subset(distr, ano == 2024)
d24$share_2024 <- 100 * d24$votos_grupo / d24$votos_validos
dist_cen <- do.call(rbind, lapply(oscilacao, function(o) {
  data.frame(oscilacao = o, distrito = d24$distrito, share = d24$share_2024 + o,
             vence = d24$share_2024 + o > 50)
}))
write.csv(dist_cen, "output/r_cenarios_2028_distritos.csv", row.names = FALSE, fileEncoding = "UTF-8")

cat("Cenarios de 2028 gravados em output/r_cenarios_2028_*.csv\n")
print(cen_eleit)
print(ponto_de_virada)
print(faixa)
