CREATE SCHEMA IF NOT EXISTS plantaview;

CREATE TABLE plantaview.equipamentos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100),
    tipo VARCHAR(50),
    localizacao VARCHAR(100)
);

CREATE TABLE plantaview.sensores (
    id SERIAL PRIMARY KEY,
    equipamento_id INT REFERENCES plantaview.equipamentos(id),
    grandeza VARCHAR(20),
    unidade VARCHAR(10),
    setpoint_min NUMERIC(10,2),
    setpoint_max NUMERIC(10,2)
);

CREATE TABLE plantaview.leituras (
    id SERIAL PRIMARY KEY,
    sensor_id INT REFERENCES plantaview.sensores(id),
    valor NUMERIC(10,2),
    unidade VARCHAR(10),
    registrado_em TIMESTAMP DEFAULT NOW()
);

CREATE VIEW plantaview.vw_leituras_detalhadas AS
SELECT 
    l.id AS leitura_id,
    e.id AS equipamento_id,
    e.nome AS equipamento_nome,
    e.tipo AS equipamento_tipo,
    s.grandeza,
    l.valor,
    l.unidade,
    s.setpoint_min,
    s.setpoint_max,
    l.registrado_em
FROM plantaview.leituras l
JOIN plantaview.sensores s ON l.sensor_id = s.id
JOIN plantaview.equipamentos e ON s.equipamento_id = e.id;

CREATE VIEW plantaview.vw_ultima_leitura AS
SELECT DISTINCT ON (s.id)
    s.id AS sensor_id,
    e.id AS equipamento_id,
    e.nome AS equipamento_nome,
    s.grandeza,
    l.valor,
    l.unidade,
    s.setpoint_min,
    s.setpoint_max,
    l.registrado_em
FROM plantaview.sensores s
JOIN plantaview.equipamentos e ON s.equipamento_id = e.id
LEFT JOIN plantaview.leituras l ON s.id = l.sensor_id
ORDER BY s.id, l.registrado_em DESC;

CREATE INDEX idx_leituras_sensor_data ON plantaview.leituras (sensor_id, registrado_em DESC);
CREATE INDEX idx_leituras_data ON plantaview.leituras (registrado_em DESC);

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

-- Sensores (IDs 1 a 24)
INSERT INTO plantaview.sensores (id, equipamento_id, grandeza, unidade, setpoint_min, setpoint_max) VALUES
(1,  1, 'temperatura', '°C',   20.00, 60.00),
(2,  1, 'pressao',     'bar',   1.00,  5.00),
(3,  1, 'vibracao',    'mm/s',  0.00, 10.00),
(4,  2, 'temperatura', '°C',   20.00, 60.00),
(5,  2, 'pressao',     'bar',   1.00,  5.00),
(6,  2, 'vibracao',    'mm/s',  0.00, 10.00),
(7,  3, 'temperatura', '°C',   30.00, 80.00),
(8,  3, 'pressao',     'bar',   5.00, 12.00),
(9,  3, 'vibracao',    'mm/s',  0.00, 15.00),
(10, 4, 'temperatura', '°C',   30.00, 80.00),
(11, 4, 'pressao',     'bar',   5.00, 12.00),
(12, 4, 'vibracao',    'mm/s',  0.00, 15.00),
(13, 5, 'temperatura', '°C',   30.00, 80.00),
(14, 5, 'pressao',     'bar',   5.00, 12.00),
(15, 5, 'vibracao',    'mm/s',  0.00, 15.00),
(16, 6, 'temperatura', '°C',   40.00, 90.00),
(17, 6, 'pressao',     'bar',   0.00,  0.00),
(18, 6, 'vibracao',    'mm/s',  0.00, 20.00),
(19, 7, 'temperatura', '°C',   40.00, 90.00),
(20, 7, 'pressao',     'bar',   0.00,  0.00),
(21, 7, 'vibracao',    'mm/s',  0.00, 20.00),
(22, 8, 'temperatura', '°C',  100.00, 200.00),
(23, 8, 'pressao',     'bar',  10.00, 25.00),
(24, 8, 'vibracao',    'mm/s',  0.00,  5.00);
SELECT setval('plantaview.sensores_id_seq', 24);

-- Leituras Determinísticas Recentes
INSERT INTO plantaview.leituras (sensor_id, valor, unidade, registrado_em) VALUES
(1,  45.20, '°C',   '2026-09-20 10:00:00'),
(2,   3.40, 'bar',  '2026-09-20 10:00:00'),
(3,   4.10, 'mm/s', '2026-09-20 10:00:00'),
(4,  54.00, '°C',   '2026-09-20 10:00:00'),
(5,   3.80, 'bar',  '2026-09-20 10:00:00'),
(6,   6.50, 'mm/s', '2026-09-20 10:00:00'),
(7,  68.00, '°C',   '2026-09-20 10:00:00'),
(8,  12.50, 'bar',  '2026-09-20 10:00:00'),
(9,   8.20, 'mm/s', '2026-09-20 10:00:00'),
(10, 82.00, '°C',   '2026-09-20 10:00:00'),
(11,  9.50, 'bar',  '2026-09-20 10:00:00'),
(12, 11.00, 'mm/s', '2026-09-20 10:00:00'),
(13, 85.00, '°C',   '2026-09-20 10:00:00'),
(14, 13.50, 'bar',  '2026-09-20 10:00:00'),
(15, 16.00, 'mm/s', '2026-09-20 10:00:00'),
(16, 74.00, '°C',   '2026-09-20 10:00:00'),
(17,  0.00, 'bar',  '2026-09-20 10:00:00'),
(18, 22.00, 'mm/s', '2026-09-20 10:00:00'),
(19, 71.00, '°C',   '2026-09-20 10:00:00'),
(20,  0.00, 'bar',  '2026-09-20 10:00:00'),
(21, 12.00, 'mm/s', '2026-09-20 10:00:00'),
(22, 210.00, '°C',  '2026-09-20 10:00:00'),
(23,  27.50, 'bar', '2026-09-20 10:00:00'),
(24,   6.20, 'mm/s','2026-09-20 10:00:00');
