-- Banco SQLite do estudo "A Metamorfose do Poder em Alfredo Chaves" (2004-2024).
-- Todas as tabelas cobrem as SEIS eleicoes municipais; a coluna "ano" separa uma da outra.
-- Carregado por scripts/build_database.py a partir dos extratos do TSE em data/.
--
-- Convencoes:
--   * cargo esta normalizado para 'Prefeito' ou 'Vereador' (o TSE grafa 'PREFEITO' em 2016).
--   * nr_votavel 95 = voto branco e 96 = voto nulo (o TSE os grava como "candidatos").
--     "Votos validos" (Tabela 0.1 e o restante do estudo) EXCLUEM 95 e 96.
--   * zona 12 e a unica zona eleitoral do municipio; secao e o numero da secao dentro da zona.

DROP VIEW IF EXISTS v_votos_prefeito;
DROP VIEW IF EXISTS v_prefeito_secao;
DROP TABLE IF EXISTS votos_secao;
DROP TABLE IF EXISTS candidatos;
DROP TABLE IF EXISTS detalhe_votacao;
DROP TABLE IF EXISTS local_secao;
DROP TABLE IF EXISTS grupo_eleicao;

-- Votos por secao eleitoral, um registro por (ano, secao, cargo, votavel).
CREATE TABLE votos_secao (
    ano                 INTEGER NOT NULL,
    zona                INTEGER NOT NULL,
    secao               INTEGER NOT NULL,
    cargo               TEXT    NOT NULL CHECK (cargo IN ('Prefeito', 'Vereador')),
    nr_votavel          INTEGER NOT NULL,
    nm_votavel          TEXT    NOT NULL,
    qt_votos            INTEGER NOT NULL CHECK (qt_votos >= 0),
    nr_local_votacao    INTEGER
);
CREATE INDEX ix_votos_ano_cargo ON votos_secao (ano, cargo, secao);

-- Candidaturas registradas, um registro por (ano, cargo, candidato).
CREATE TABLE candidatos (
    ano                 INTEGER NOT NULL,
    cargo               TEXT    NOT NULL,
    sq_candidato        TEXT,
    nr_candidato        INTEGER,
    nm_candidato        TEXT,
    nm_urna             TEXT,
    sg_partido          TEXT,
    nm_coligacao        TEXT,
    ds_composicao       TEXT,
    ds_situacao_turno   TEXT
);
CREATE INDEX ix_candidatos_ano_cargo ON candidatos (ano, cargo);

-- Comparecimento e votos nao validos do municipio, um registro por (ano, cargo).
CREATE TABLE detalhe_votacao (
    ano                 INTEGER NOT NULL,
    cargo               TEXT    NOT NULL,
    qt_aptos            INTEGER NOT NULL,
    qt_comparecimento   INTEGER NOT NULL,
    qt_abstencoes       INTEGER NOT NULL,
    qt_brancos          INTEGER NOT NULL,
    qt_nulos            INTEGER NOT NULL,
    qt_secoes           INTEGER
);

-- Secao -> local de votacao -> distrito. O local e o de 2024 (unico ano com o nome do local no
-- extrato do TSE por secao); o estudo aplica essa atribuicao a todas as eleicoes.
CREATE TABLE local_secao (
    secao               INTEGER PRIMARY KEY,
    local_votacao       TEXT NOT NULL,
    distrito            TEXT
);

-- Quem e "o grupo" em cada eleicao: o candidato a prefeito da base politica do autor.
CREATE TABLE grupo_eleicao (
    ano                 INTEGER PRIMARY KEY,
    nm_votavel          TEXT NOT NULL
);

-- Votos nominais para prefeito (sem brancos e nulos) com a marca "e_grupo".
CREATE VIEW v_votos_prefeito AS
SELECT v.ano, v.secao, v.nr_votavel, v.nm_votavel, v.qt_votos,
       CASE WHEN v.nm_votavel = g.nm_votavel THEN 1 ELSE 0 END AS e_grupo
FROM votos_secao v
JOIN grupo_eleicao g ON g.ano = v.ano
WHERE v.cargo = 'Prefeito' AND v.nr_votavel NOT IN (95, 96);

-- Uma linha por (ano, secao) com os votos do grupo e os votos validos da secao.
CREATE VIEW v_prefeito_secao AS
SELECT ano, secao,
       SUM(CASE WHEN e_grupo = 1 THEN qt_votos ELSE 0 END) AS votos_grupo,
       SUM(qt_votos)                                       AS votos_validos,
       MAX(CASE WHEN e_grupo = 1 THEN qt_votos ELSE 0 END) AS max_grupo,
       MAX(qt_votos)                                       AS max_secao
FROM v_votos_prefeito
GROUP BY ano, secao;
