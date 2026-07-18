-- Equivalente T-SQL do init.sql, para uso com Azure SQL Database (bônus Azure Foundry).
-- Rode manualmente contra o seu Azure SQL (ex. via `sqlcmd` ou Azure Data Studio) antes de
-- apontar DATABASE_URL/SQL_DIALECT=mssql para ele — Azure SQL não suporta scripts de
-- inicialização automática via volume como o container Postgres.

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'clientes')
BEGIN
    CREATE TABLE clientes (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nome NVARCHAR(200) NOT NULL,
        cidade NVARCHAR(200) NOT NULL,
        criado_em DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE)
    );
END;

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'pedidos')
BEGIN
    CREATE TABLE pedidos (
        id INT IDENTITY(1,1) PRIMARY KEY,
        cliente_id INT NOT NULL REFERENCES clientes(id),
        produto NVARCHAR(200) NOT NULL,
        valor DECIMAL(10, 2) NOT NULL,
        status NVARCHAR(50) NOT NULL,
        criado_em DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE)
    );
END;

IF NOT EXISTS (SELECT 1 FROM clientes)
BEGIN
    INSERT INTO clientes (nome, cidade, criado_em) VALUES
        ('Ana Souza', 'São Paulo', '2025-01-10'),
        ('Bruno Lima', 'Rio de Janeiro', '2025-02-15'),
        ('Carla Dias', 'Belo Horizonte', '2025-03-02'),
        ('Diego Alves', 'Curitiba', '2025-04-20'),
        ('Elaine Costa', 'São Paulo', '2025-05-05');
END;

IF NOT EXISTS (SELECT 1 FROM pedidos)
BEGIN
    INSERT INTO pedidos (cliente_id, produto, valor, status, criado_em) VALUES
        (1, 'Notebook', 3500.00, 'entregue', '2025-01-15'),
        (1, 'Mouse', 80.00, 'entregue', '2025-02-01'),
        (2, 'Teclado Mecânico', 450.00, 'processando', '2025-06-10'),
        (3, 'Monitor', 1200.00, 'enviado', '2025-06-20'),
        (4, 'Headset', 300.00, 'cancelado', '2025-05-01'),
        (5, 'Notebook', 3800.00, 'entregue', '2025-05-10'),
        (5, 'Webcam', 150.00, 'processando', '2025-07-01');
END;
