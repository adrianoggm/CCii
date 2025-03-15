.PHONY: help start stop rm restart ldap-init ldap-add ldap-search ldap-init2 ldap-add2 ldap-search2 start1 start2 stop1 stop2 restart1 restart2 ldap-update-passwords

help:
        @echo "Uso: make <target>"
        @echo ""
        @echo "Targets disponibles:"
        @echo "  start        - Inicia Docker Compose en modo detach."
        @echo "  stop         - Detiene los contenedores de Docker Compose."
        @echo "  rm           - Detiene y remueve los contenedores."
        @echo "  restart      - Reinicia los contenedores."
        @echo "  start1       - Inicia docker-compose1.yml en modo detach."
        @echo "  start2       - Inicia docker-compose2.yml en modo detach."
        @echo "  stop1        - Detiene los contenedores de docker-compose1.yml."
        @echo "  stop2        - Detiene los contenedores de docker-compose2.yml."
        @echo "  restart1     - Reinicia los contenedores de docker-compose1.yml."
        @echo "  restart2     - Reinicia los contenedores de docker-compose2.yml."
        @echo "  ldap-init    - Inicializa LDAP usando base_dn.ldif (Escenario 1)."
        @echo "  ldap-add     - Agrega entradas LDAP para el Escenario 1."
        @echo "  ldap-search  - Realiza búsquedas LDAP en el Escenario 1."
        @echo "  ldap-update-passwords - Cambia las contraseñas de adrianoggm y juanitoggm en LDAP."
        @echo ""

start:
        @echo "Iniciando Docker Compose..."
        @docker compose up -d

stop:
        @echo "Deteniendo Docker Compose..."
        @docker compose stop

rm:
        @echo "Deteniendo y removiendo los contenedores de Docker Compose..."
        @docker compose stop
        @docker compose rm -f

restart:
        @echo "Reiniciando Docker Compose..."
        @docker compose stop
        @docker compose up -d

# Manejo de múltiples escenarios
start1:
        @echo "Iniciando Docker Compose para docker-compose1.yml..."
        @docker compose -f docker-compose1.yml up -d

start2:
        @echo "Iniciando Docker Compose para docker-compose2.yml..."
        @docker compose -f docker-compose2.yml up -d

stop1:
        @echo "Deteniendo Docker Compose para docker-compose1.yml..."
        @docker compose -f docker-compose1.yml stop

stop2:
        @echo "Deteniendo Docker Compose para docker-compose2.yml..."
        @docker compose -f docker-compose2.yml stop

restart1:
        @echo "Reiniciando Docker Compose para docker-compose1.yml..."
        @docker compose -f docker-compose1.yml stop
        @docker compose -f docker-compose1.yml up -d

restart2:
        @echo "Reiniciando Docker Compose para docker-compose2.yml..."
        @docker compose -f docker-compose2.yml stop
        @docker compose -f docker-compose2.yml up -d

# Escenario 1 - LDAP
ldap-init:
        @echo "Inicializando LDAP (Escenario 1 - base_dn.ldif)..."
        @ldapadd -x -H ldap://localhost:20273 -D "cn=admin,dc=example,dc=com" -w admin -c -f base_dn.ldif

ldap-add:
        @echo "Agregando entradas LDAP (Escenario 1)..."
        @ldapadd -x -H ldap://localhost:20273 -D "cn=admin,dc=example,dc=com" -w admin -c -f adrianoggm.ldif
        @ldapadd -x -H ldap://localhost:20273 -D "cn=admin,dc=example,dc=com" -w admin -c -f juanitoggm.ldif

ldap-search:
        @echo "Realizando búsqueda LDAP en Escenario 1..."
        @docker exec -it owncloud_ldap_server ldapsearch -x -H ldap://localhost:20273 -D "cn=admin,dc=example,dc=com" -w admin -b "dc=example,dc=com" "(objectClass=*)"

# 🔹 NUEVO: Actualizar contraseñas de usuarios en LDAP
ldap-update-passwords:
        @echo "Actualizando contraseña de adrianoggm en LDAP..."
        @docker exec owncloud_ldap_server ldapmodify -x -H ldap://localhost:20273 -D "cn=admin,dc=example,dc=com" -w admin -c -f /tmp/ldap_password_adrianoggm.ldif

        @echo "Actualizando contraseña de juanitoggm en LDAP..."
        @docker exec owncloud_ldap_server ldapmodify -x -H ldap://localhost:20273 -D "cn=admin,dc=example,dc=com" -w admin -c -f /tmp/ldap_password_juanitoggm.ldif

        @echo "Contraseñas actualizadas correctamente."

# Crear archivos LDIF antes de actualizar contraseñas
prepare-ldap-passwords:
        @echo "Creando archivos LDIF para cambiar contraseñas..."
        @echo "dn: uid=adrianoggm,ou=users,dc=example,dc=com" > /tmp/ldap_password_adrianoggm.ldif
        @echo "changetype: modify" >> /tmp/ldap_password_adrianoggm.ldif
        @echo "replace: userPassword" >> /tmp/ldap_password_adrianoggm.ldif
        @echo "userPassword: adriano" >> /tmp/ldap_password_adrianoggm.ldif

        @echo "dn: uid=juanitoggm,ou=users,dc=example,dc=com" > /tmp/ldap_password_juanitoggm.ldif
        @echo "changetype: modify" >> /tmp/ldap_password_juanitoggm.ldif
        @echo "replace: userPassword" >> /tmp/ldap_password_juanitoggm.ldif
        @echo "userPassword: juanito" >> /tmp/ldap_password_juanitoggm.ldif
        @echo "Archivos LDIF creados."

change-passwords:
        @echo "Cambiando la contraseña de adrianoggm en LDAP..."
        @docker exec owncloud_ldap_server ldappasswd -x -D "cn=admin,dc=example,dc=com" -w admin -s adriano "uid=adrianoggm,ou=users,dc=example,dc=com"

        @echo "Cambiando la contraseña de juanitoggm en LDAP..."
        @docker exec owncloud_ldap_server ldappasswd -x -D "cn=admin,dc=example,dc=com" -w admin -s juanito "uid=juanitoggm,ou=users,dc=example,dc=com"

        @echo "Contraseñas cambiadas correctamente."