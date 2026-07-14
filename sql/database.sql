CREATE DATABASE IF NOT EXISTS impostor_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE impostor_db;

CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE words (
    id INT AUTO_INCREMENT PRIMARY KEY,
    word VARCHAR(100) NOT NULL,
    category_id INT NOT NULL,
    UNIQUE KEY uq_word_category (word, category_id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Categorias
INSERT INTO categories (name) VALUES
('Lugar'),
('Objeto'),
('Comida'),
('Animal');

-- Lugares
INSERT INTO words (word, category_id) VALUES
('obra en construcción',1),
('estacionamiento',1),
('playa',1),
('hospital',1),
('cine',1),
('aeropuerto',1),
('circo',1),
('escuela',1),
('biblioteca',1),
('estadio',1),
('restaurante',1),
('supermercado',1),
('parque',1),
('museo',1),
('teatro',1),
('gimnasio',1),
('oficina',1),
('hotel',1),
('estación de tren',1),
('subte',1),
('plaza',1),
('discoteca',1),
('piscina',1),
('zoológico',1),
('acuario',1),
('feria',1),
('comisaría',1),
('bomberos',1),
('banco',1),
('farmacia',1);

-- Objetos
INSERT INTO words (word, category_id) VALUES
('guitarra',2),
('teléfono',2),
('auto',2),
('televisor',2),
('heladera',2),
('microondas',2),
('bicicleta',2),
('teclado',2),
('martillo',2),
('lámpara',2),
('mochila',2),
('drone',2),
('reloj',2),
('paraguas',2),
('cuchillo',2),
('libro',2),
('cámara',2),
('lavarropas',2),
('balón',2),
('silla',2),
('mesa',2),
('tijera',2),
('auriculares',2);

-- Comida
INSERT INTO words (word, category_id) VALUES
('pizza',3),
('empanadas',3),
('asado',3),
('hamburguesa',3),
('tacos',3),
('sushi',3),
('ensalada',3),
('milanesa',3),
('fideos',3),
('ravioles',3),
('helado',3),
('torta',3),
('choripán',3),
('lomito',3),
('tarta',3),
('pancakes',3),
('arepas',3),
('paella',3),
('cazuela',3),
('ramen',3),
('guiso',3);

-- Animales
INSERT INTO words (word, category_id) VALUES
('perro',4),
('gato',4),
('tiburón',4),
('águila',4),
('león',4),
('elefante',4),
('jirafa',4),
('panda',4),
('ballena',4),
('delfín',4),
('conejo',4),
('caballo',4),
('vaca',4),
('oveja',4),
('mono',4),
('pingüino',4),
('cocodrilo',4),
('zorro',4);
