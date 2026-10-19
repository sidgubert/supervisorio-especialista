CREATE SCHEMA IF NOT EXISTS plantaview;

CREATE TABLE plantaview.equipamentos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100),
    tipo VARCHAR(50),
    localizacao VARCHAR(100)
);

CREATE TABLE plantaview.alarmes (
    id SERIAL PRIMARY KEY,
    equipamento_id INT REFERENCES plantaview.equipamentos(id),
    grandeza VARCHAR(20),
    valor_lido NUMERIC(10,2),
    setpoint NUMERIC(10,2),
    severidade VARCHAR(20) CHECK (severidade IN ('baixa','media','alta','critica')),
    status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo','reconhecido','encerrado')),
    criado_em TIMESTAMP DEFAULT NOW(),
    reconhecido_em TIMESTAMP,
    encerrado_em TIMESTAMP
);

CREATE VIEW plantaview.vw_alarmes_detalhados AS
SELECT 
    a.id AS alarme_id,
    e.id AS equipamento_id,
    e.nome AS equipamento_nome,
    e.tipo AS equipamento_tipo,
    a.grandeza,
    a.valor_lido,
    a.setpoint,
    a.severidade,
    a.status,
    a.criado_em,
    a.reconhecido_em,
    a.encerrado_em
FROM plantaview.alarmes a
JOIN plantaview.equipamentos e ON a.equipamento_id = e.id;

CREATE VIEW plantaview.vw_alarmes_por_equipamento AS
SELECT 
    e.id AS equipamento_id,
    e.nome AS equipamento_nome,
    a.severidade,
    COUNT(*) as total_alarmes
FROM plantaview.alarmes a
JOIN plantaview.equipamentos e ON a.equipamento_id = e.id
GROUP BY e.id, e.nome, a.severidade
ORDER BY total_alarmes DESC;

CREATE INDEX idx_alarmes_equip ON plantaview.alarmes(equipamento_id);
CREATE INDEX idx_alarmes_status ON plantaview.alarmes(status);
CREATE INDEX idx_alarmes_severidade ON plantaview.alarmes(severidade);
CREATE INDEX idx_alarmes_criado ON plantaview.alarmes(criado_em DESC);

-- Seed Data Determinístico
INSERT INTO plantaview.equipamentos (id, nome, tipo, localizacao) VALUES
(1, 'Bomba 1', 'bomba', 'Sala de Bombas'),
(2, 'Bomba 2', 'bomba', 'Sala de Bombas'),
(3, 'Compressor 1', 'compressor', 'Utilidades'),
(4, 'Compressor 2', 'compressor', 'Utilidades'),
(5, 'Compressor 3', 'compressor', 'Utilidades'),
(6, 'Motor 1', 'motor', 'Linha de Produção'),
(7, 'Motor 2', 'motor', 'Linha de Produção'),
(8, 'Caldeira 1', 'caldeira', 'Casa de Caldeiras');
SELECT setval('plantaview.equipamentos_id_seq', 8);

-- Alarmes Determinísticos
INSERT INTO plantaview.alarmes (equipamento_id, grandeza, valor_lido, setpoint, severidade, status, criado_em, reconhecido_em, encerrado_em) VALUES
(8, 'pressao', 27.5, 25.0, 'critica', 'ativo', '2026-09-20 09:15:00', NULL, NULL),
(8, 'temperatura', 210.0, 200.0, 'alta', 'ativo', '2026-09-20 08:30:00', NULL, NULL),
(8, 'vibracao', 6.2, 5.0, 'media', 'reconhecido', '2026-09-19 14:00:00', '2026-09-19 14:15:00', NULL),
(5, 'temperatura', 85.0, 80.0, 'critica', 'ativo', '2026-09-20 10:00:00', NULL, NULL),
(5, 'pressao', 13.5, 12.0, 'alta', 'ativo', '2026-09-20 09:50:00', NULL, NULL),
(5, 'vibracao', 16.0, 15.0, 'media', 'reconhecido', '2026-09-18 10:20:00', '2026-09-18 10:30:00', NULL),
(1, 'temperatura', 62.0, 60.0, 'baixa', 'encerrado', '2026-09-17 11:00:00', '2026-09-17 11:10:00', '2026-09-17 12:00:00'),
(2, 'vibracao', 11.0, 10.0, 'media', 'encerrado', '2026-09-16 08:00:00', '2026-09-16 08:05:00', '2026-09-16 09:00:00'),
(3, 'pressao', 12.5, 12.0, 'baixa', 'ativo', '2026-09-20 07:00:00', NULL, NULL),
(4, 'temperatura', 82.0, 80.0, 'alta', 'reconhecido', '2026-09-19 16:45:00', '2026-09-19 17:00:00', NULL),
(6, 'vibracao', 22.0, 20.0, 'alta', 'ativo', '2026-09-20 06:30:00', NULL, NULL),
(7, 'temperatura', 95.0, 90.0, 'critica', 'encerrado', '2026-09-15 10:00:00', '2026-09-15 10:05:00', '2026-09-15 11:30:00');
