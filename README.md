# 🐧 Penguin Clash: Arquitectura Distribuida

Solución modular y desacoplada para el backend de Penguin Academy. Transición del monolito "El Mamut" a un ecosistema de microservicios autónomos con persistencia aislada (*Database per Service*) y seguridad criptográfica.



---

## 🏛️ Topología del Sistema

| Microservicio | Puerto | Base de Datos | Responsabilidad Principal |
| :--- | :--- | :--- | :--- |
| **`auth-service`** | `5001` | `db_auth` | Registro, roles y emisión de tokens JWT. |
| **`inventory-service`** | `5002` | `db_inventory` | Control de stock físico con bloqueo transaccional. |
| **`orders-service`** | `5003` | `db_orders` | Orquestador de compras con política de reintentos (*Retry*). |

---

## 🚀 Despliegue Rápido

1. Ubicate en la raíz del proyecto:
   ```bash
   cd penguin_clash