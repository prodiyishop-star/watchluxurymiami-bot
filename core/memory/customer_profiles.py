"""
Gestión de perfiles de clientes.
Permite actualizar notas, etiquetas y compras de los clientes.
"""

from typing import List, Optional
from database.manager import DatabaseManager


class CustomerProfileManager:
    """Maneja los perfiles y datos de los clientes."""

    def __init__(self):
        self.db = DatabaseManager()

    async def update_notes(self, customer_id: str, notes: str):
        """Actualiza las notas de un cliente."""
        await self.db.update_customer_notes(customer_id, notes)

    async def add_tag(self, customer_id: str, tag: str):
        """Agrega una etiqueta a un cliente (ej: 'comprador_frecuente', 'interesado_producto_x')."""
        await self.db.add_customer_tag(customer_id, tag)

    async def record_purchase(self, customer_id: str, product: str, amount: float):
        """Registra una compra en el historial del cliente."""
        from database.models import Customer
        from sqlalchemy import select
        from datetime import datetime

        async with self.db.session() as db:
            result = await db.execute(select(Customer).where(Customer.id == customer_id))
            customer = result.scalar_one_or_none()
            if customer:
                history = customer.purchase_history or []
                history.append({
                    "product": product,
                    "amount": amount,
                    "date": datetime.utcnow().isoformat(),
                })
                customer.purchase_history = history

    async def get_vip_customers(self, min_purchases: int = 3):
        """Obtiene clientes VIP (con muchas compras)."""
        from database.models import Customer
        from sqlalchemy import select
        from sqlalchemy import func

        async with self.db.session() as db:
            result = await db.execute(
                select(Customer).where(
                    Customer.total_messages >= min_purchases * 5
                )
            )
            return result.scalars().all()
