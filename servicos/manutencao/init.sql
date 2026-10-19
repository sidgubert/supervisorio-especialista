CREATE SCHEMA IF NOT EXISTS plantaview;

CREATE TABLE plantaview.equipamentos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100),
    tipo VARCHAR(50),
    localizacao VARCHAR(100)
);

CREATE TABLE plantaview.ordens_servico (
    id SERIAL PRIMARY KEY,
    equipamento_id INT REFERENCES plantaview.equipamentos(id),
    tipo_manutencao VARCHAR(30) CHECK (tipo_manutencao IN ('preventiva','corretiva','preditiva')),
    descricao TEXT,
    status VARCHAR(20) DEFAULT 'aberta' CHECK (status IN ('aberta','em_andamento','concluida','cancelada')),
    prioridade VARCHAR(20) DEFAULT 'normal' CHECK (prioridade IN ('baixa','normal','alta','urgente')),
    criada_em TIMESTAMP DEFAULT NOW(),
    concluida_em TIMESTAMP,
    tecnico_responsavel VARCHAR(100),
    observacoes TEXT
);

CREATE VIEW plantaview.vw_ordens_detalhadas AS
SELECT 
    o.id AS ordem_id,
    e.id AS equipamento_id,
    e.nome AS equipamento_nome,
    e.tipo AS equipamento_tipo,
    o.tipo_manutencao,
    o.descricao,
    o.status,
    o.prioridade,
    o.criada_em,
    o.concluida_em,
    o.tecnico_responsavel,
    o.observacoes
FROM plantaview.ordens_servico o
JOIN plantaview.equipamentos e ON o.equipamento_id = e.id;

CREATE VIEW plantaview.vw_manutencao_por_equipamento AS
SELECT 
    e.id AS equipamento_id,
    e.nome AS equipamento_nome,
    COUNT(o.id) AS total_ordens,
    COUNT(o.id) FILTER (WHERE o.status = 'aberta') AS abertas,
    COUNT(o.id) FILTER (WHERE o.status = 'em_andamento') AS em_andamento,
    COUNT(o.id) FILTER (WHERE o.status = 'concluida') AS concluidas
FROM plantaview.equipamentos e
LEFT JOIN plantaview.ordens_servico o ON e.id = o.equipamento_id
GROUP BY e.id, e.nome;

CREATE INDEX idx_os_equip ON plantaview.ordens_servico(equipamento_id);
CREATE INDEX idx_os_status ON plantaview.ordens_servico(status);
CREATE INDEX idx_os_criada ON plantaview.ordens_servico(criada_em DESC);

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

-- Ordens de Serviço Determinísticas
INSERT INTO plantaview.ordens_servico (equipamento_id, tipo_manutencao, descricao, status, prioridade, criada_em, concluida_em, tecnico_responsavel, observacoes) VALUES
(5, 'corretiva', 'Falha no sistema de refrigeração', 'aberta', 'urgente', '2026-09-20 08:00:00', NULL, 'Carlos Silva', 'Equipamento apresentando superaquecimento constante.'),
(5, 'preventiva', 'Troca de filtros e óleo', 'em_andamento', 'normal', '2026-09-19 14:00:00', NULL, 'Ana Santos', 'Aguardando chegada do óleo específico.'),
(8, 'corretiva', 'Vazamento na válvula de segurança', 'aberta', 'alta', '2026-09-19 16:30:00', NULL, 'Pedro Lima', 'Risco de perda de pressão.'),
(1, 'preventiva', 'Inspeção mensal', 'concluida', 'normal', '2026-09-10 09:00:00', '2026-09-10 11:30:00', 'Maria Oliveira', 'Tudo ok, lubrificação realizada.'),
(2, 'preditiva', 'Análise de vibração', 'concluida', 'baixa', '2026-09-05 10:00:00', '2026-09-05 12:00:00', 'Carlos Silva', 'Níveis dentro do aceitável.'),
(3, 'preventiva', 'Limpeza do condensador', 'cancelada', 'normal', '2026-09-15 08:00:00', NULL, 'Ana Santos', 'Cancelada por falta de tempo na parada geral.'),
(4, 'corretiva', 'Ruído anormal no rotor', 'em_andamento', 'alta', '2026-09-18 13:00:00', NULL, 'Pedro Lima', 'Desmontagem iniciada.'),
(6, 'preventiva', 'Reaperto de conexões elétricas', 'concluida', 'normal', '2026-09-01 14:00:00', '2026-09-01 16:00:00', 'Maria Oliveira', 'Cabos oxidados trocados.'),
(7, 'preditiva', 'Termografia do painel', 'aberta', 'normal', '2026-09-19 09:00:00', NULL, 'Carlos Silva', 'Agendado para próxima semana.');
