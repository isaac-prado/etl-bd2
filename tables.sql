CREATE TYPE tipo_nutri_eco AS ENUM ('A', 'B', 'C', 'D', 'E');
CREATE TYPE tipo_nova AS ENUM ('1', '2', '3', '4');
CREATE TYPE tipo_tag AS ENUM ('allergen', 'additive');

SELECT * FROM produto

CREATE TABLE Produto (
    codigo VARCHAR(255) PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    nutriscore tipo_nutri_eco,
    ecoscore tipo_nutri_eco,
    novascore tipo_nova
);

-- Tabela Nutriente
CREATE TABLE nutriente (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    unidade VARCHAR(10) NOT NULL
);
-- Tabela Produto_Nutriente
CREATE TABLE Produto_Nutriente (
    id SERIAL PRIMARY KEY,
    produto_id VARCHAR(255) NOT NULL REFERENCES Produto(codigo) ON DELETE CASCADE,
    nutriente_id INT NOT NULL REFERENCES Nutriente(id) ON DELETE RESTRICT,
    quantidade_100g DECIMAL(6,2)
);

-- Tabela Ingrediente
CREATE TABLE Ingrediente (
    id INT PRIMARY KEY, -- Baseado no ciqual_food_code
    nome VARCHAR(100) NOT NULL UNIQUE,
    vegano BOOLEAN,
    vegetariano BOOLEAN
);
-- Tabela Produto_Ingrediente
CREATE TABLE Produto_Ingrediente (
    id SERIAL PRIMARY KEY,
    produto_id VARCHAR(255) NOT NULL REFERENCES Produto(codigo) ON DELETE CASCADE,
    ingrediente_id INT NOT NULL REFERENCES Ingrediente(id) ON DELETE RESTRICT,
    quantidade_estimada DECIMAL(5,2)
);

-- Tabela Tag
CREATE TABLE Tag (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    tipo tipo_tag NOT NULL, -- Ex.: 'allergen', 'additive'
    CONSTRAINT uq_tag_nome_tipo UNIQUE (nome, tipo) -- A combinação de nome e tipo da tag deve ser única
);
-- Tabela Produto_Tag
CREATE TABLE Produto_Tag (
    id SERIAL PRIMARY KEY,
    produto_id VARCHAR(255) NOT NULL REFERENCES Produto(codigo) ON DELETE CASCADE,
    tag_id INT NOT NULL REFERENCES Tag(id) ON DELETE RESTRICT
);

-- Tabela Categoria
CREATE TABLE Categoria (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE -- Nome da categoria é único
);
-- Tabela Produto_Categoria
CREATE TABLE Produto_Categoria (
    id SERIAL PRIMARY KEY,
    produto_id VARCHAR(255) NOT NULL REFERENCES Produto(codigo) ON DELETE CASCADE,
    categoria_id INT NOT NULL REFERENCES Categoria(id) ON DELETE RESTRICT
);

-- Tabela Marca
CREATE TABLE Marca (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE -- Nome da marca é único
);
-- Tabela Produto_Marca
CREATE TABLE Produto_Marca (
    id SERIAL PRIMARY KEY,
    produto_id VARCHAR(255) NOT NULL REFERENCES Produto(codigo) ON DELETE CASCADE,
    marca_id INT NOT NULL REFERENCES Marca(id) ON DELETE RESTRICT
);

ALTER TABLE ingrediente ADD CONSTRAINT ingrediente_nome_key UNIQUE(nome)