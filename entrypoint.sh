#!/bin/sh
set -e

# Esperar a que el servicio de PostgreSQL esté completamente listo para aceptar conexiones
# Usamos un bucle con un retardo para evitar fallos por conexiones prematuras.
# El flag -d "authdb" es crucial para verificar que la base de datos existe.
echo "Esperando a la base de datos de PostgreSQL..."
until PGPASSWORD=supersecretpassword pg_isready -h postgres-kanban -p 5432 -U kanbanuser -d kanbandb; do
  >&2 echo "PostgreSQL no está disponible - esperando..."
  sleep 1
done

echo "PostgreSQL está listo. Aplicando migraciones..."

flask --app app:create_app db migrate -m "create users table"

flask --app app:create_app db upgrade

echo "Iniciando el servidor Flask..."

# Iniciar el servidor Flask. El comando 'exec' reemplaza el proceso de shell
# por el proceso del servidor Flask, lo que permite a Docker manejar las señales de forma correcta.
exec flask --app app:create_app run --host=0.0.0.0 --port=5001
