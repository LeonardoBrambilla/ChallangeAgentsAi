CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    cidade TEXT NOT NULL,
    criado_em DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    produto TEXT NOT NULL,
    valor NUMERIC(10, 2) NOT NULL,
    status TEXT NOT NULL,
    criado_em DATE NOT NULL DEFAULT CURRENT_DATE
);

INSERT INTO clientes (nome, cidade, criado_em) VALUES
    ('Ana Souza', 'São Paulo', '2025-01-10'),
    ('Bruno Lima', 'Rio de Janeiro', '2025-02-15'),
    ('Carla Dias', 'Belo Horizonte', '2025-03-02'),
    ('Diego Alves', 'Curitiba', '2025-04-20'),
    ('Elaine Costa', 'São Paulo', '2025-05-05')
ON CONFLICT DO NOTHING;

INSERT INTO pedidos (cliente_id, produto, valor, status, criado_em) VALUES
    (1, 'Notebook', 3500.00, 'entregue', '2025-01-15'),
    (1, 'Mouse', 80.00, 'entregue', '2025-02-01'),
    (2, 'Teclado Mecânico', 450.00, 'processando', '2025-06-10'),
    (3, 'Monitor', 1200.00, 'enviado', '2025-06-20'),
    (4, 'Headset', 300.00, 'cancelado', '2025-05-01'),
    (5, 'Notebook', 3800.00, 'entregue', '2025-05-10'),
    (5, 'Webcam', 150.00, 'processando', '2025-07-01')
ON CONFLICT DO NOTHING;
