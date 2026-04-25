CREATE TABLE rol (
  id_rol INT PRIMARY KEY AUTO_INCREMENT,
  nombre_rol VARCHAR(50) NOT NULL,
  permisos VARCHAR(255) NOT NULL
)ENGINE=InnoDB;
CREATE TABLE categoria (
  id_categoria INT PRIMARY KEY AUTO_INCREMENT,
  nombre_categoria VARCHAR(50) NOT NULL,
  descripcion TEXT NOT NULL
)ENGINE=InnoDB;
CREATE TABLE usuario (
  id_usuario INT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(50) NOT NULL,
  contrasena VARCHAR(256) NOT NULL,
  direccion VARCHAR(50) NOT NULL,
  telefono VARCHAR(15),
  celular VARCHAR(15) NOT NULL,
  email VARCHAR(80) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  id_rol INT NOT NULL,
  FOREIGN KEY (id_rol) REFERENCES rol(id_rol)
)ENGINE=InnoDB;
CREATE TABLE producto (
  id_producto INT PRIMARY KEY AUTO_INCREMENT,
  nombre_producto VARCHAR(150) NOT NULL,
  descripcion TEXT,
  precio DECIMAL(10,2) NOT NULL,
  stock INT NOT NULL,
  id_categoria INT NOT NULL,
  FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria)
)ENGINE=InnoDB;
CREATE TABLE pedido (
  id_pedido INT PRIMARY KEY AUTO_INCREMENT,
  fecha_pedido DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estado_pedido ENUM('pendiente', 'pagado', 'cancelado') DEFAULT 'pendiente',
  subtotal DECIMAL(10,2) NOT NULL,
  id_usuario INT NOT NULL,
  FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
)ENGINE=InnoDB;
CREATE TABLE factura (
  id_factura INT PRIMARY KEY AUTO_INCREMENT,
  id_pedido INT NOT NULL UNIQUE,
  fecha_factura DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  subtotal DECIMAL(10,2) NOT NULL,
  total DECIMAL(10,2) NOT NULL,
  metodo_pago ENUM('efectivo', 'transferencia', 'tarjeta') NOT NULL,
  FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido)
)ENGINE=InnoDB;
CREATE TABLE domicilio (
  id_domicilio INT PRIMARY KEY AUTO_INCREMENT,
  id_pedido INT NOT NULL,
  direccion_entrega VARCHAR(50) NOT NULL,
  ciudad VARCHAR(50) NOT NULL,
  telefono_contacto VARCHAR(15) NOT NULL,
  costo_envio DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  estado_envio ENUM('pendiente','en camino','entregado','cancelado') NOT NULL,
  FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido)
)ENGINE=InnoDB;
CREATE TABLE detalle_pedido (
  id_detalle INT PRIMARY KEY AUTO_INCREMENT,
  id_pedido INT NOT NULL,
  id_producto INT NOT NULL,
  cantidad INT NOT NULL,
  precio_unitario DECIMAL(10,2) NOT NULL,
  subtotal DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (id_pedido) REFERENCES pedido(id_pedido),
  FOREIGN KEY (id_producto) REFERENCES producto(id_producto)
)ENGINE=InnoDB;