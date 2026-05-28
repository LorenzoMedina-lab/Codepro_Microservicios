# 🐧 Penguin Clash - Ecosistema de Microservicios (V2)

Este proyecto consiste en una arquitectura distribuida basada en microservicios desarrollados con **Flask**, contenerizados mediante **Docker** y persistidos en bases de datos aisladas utilizando **PostgreSQL** (*Database per Service*). El ecosistema implementa una arquitectura orientada a la consistencia transaccional mediante procesos sincrónicos / orquestados.

## 🏗️ Arquitectura del Sistema

El clúster está compuesto por 4 microservicios funcionales protegidos mediante autenticación criptográfica **JWT (JSON Web Tokens)**:

1. **Auth Service (Puerto 5001):** Gestión de usuarios, registro, login y emisión de credenciales seguras.
2. **Inventory Service (Puerto 5002):** Control de existencias, catálogo de productos y mutación de stock.
3. **Orders Service (Puerto 5003):** Orquestador central encargado de recibir compras, verificar stock y gatillar despachos.
4. **Delivery Service (Puerto 5004):** Logística y asignación de transportistas aleatorios para los envíos.

---

## ⚙️ Configuración del Entorno (Variables de Entorno)

Cumpliendo con las buenas prácticas de diseño de software, ninguna credencial ni cadena de conexión se encuentra hardcodeada en el código fuente. Toda la configuración es dinámica y se inyecta en tiempo de ejecución a través del archivo `docker-compose.yml` mediante las siguientes variables:

- `DB_HOST`: Nombre del host o contenedor de la base de datos correspondiente.
- `DB_USER` / `DB_PASSWORD` / `DB_NAME`: Credenciales de acceso a PostgreSQL.
- `JWT_SECRET`: Clave simétrica utilizada para firmar y verificar la integridad de los tokens de autenticación.

---

## 🛠️ Endpoints Disponibles (API REST)

### 🔑 1. Autenticación (Auth)
- `POST /auth/register` - Registrar un nuevo usuario (Roles: `admin`, `user`).
- `POST /auth/login` - Autenticar credenciales y obtener el Bearer Token.
- `GET /auth/usuarios` - Listar todos los usuarios del sistema `[Protegido]`.

### 📦 2. Inventario (Inventory)
- `POST /productos` - Agregar un producto nuevo al catálogo `[Protegido]`.
- `GET /productos` - Listar todos los productos disponibles y sus existencias.
- `PUT /productos/<id>` - Modificar el nombre o el precio de un producto específico `[Protegido]`.
- `GET /productos/<id>` - Ver el detalle individual de un producto.

### 🛒 3. Pedidos (Orders)
- `POST /pedidos` - Crear un pedido orquestado (Dispara flujo automático de stock y logística) `[Protegido]`.
- `GET /pedidos` - Listar el historial de órdenes registradas `[Protegido]`.
- `DELETE /pedidos/<id>` - Eliminar físicamente un pedido de la base de datos `[Protegido]`.

### 🚛 4. Logística (Delivery)
- `GET /envios` - Consultar el historial de entregas y repartidores asignados `[Protegido]`.

---

## 🚀 Instrucciones para Despliegue Rápido

Para romper la caché anterior, compilar el nuevo mapa de rutas y levantar el clúster completo en segundo plano, ejecute el siguiente comando en la terminal principal:

```bash
docker compose up --build -d