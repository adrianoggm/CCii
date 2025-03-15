# Escenario2
## Usando Docker-compose
Debido a la complejidad de este escenario, se preparó un archivo docker-compose(docker-compose2.yml) ubicado en el directorio Escenario2 directamente en vez de realizar todo el proceso mediante dockerdirectamente. Docker Compose facilita la configuración y gestión simultánea de múltiples contenedores.

A continuación, se presenta dicho archivo, donde se definen claramente todos los servicios necesarios para este escenario hemos elegido las direcciones desde 20260-20269 para su despliegue para evitar posibles conflictos o configuraciones erroneas del anterior despliegue.

Además reutilizaremos los archivos de configuracion de LDAP y las carpetas sobre las que se montan LDAP y MARIA_DB para asegurar la persistencia.

``` docker-compose
version: "3.8"


volumes:
  files:
    driver: local
  mysql:
    driver: local
  redis:
    driver: local
  ldap-data:
    driver: local
  ldap-config:
    driver: local
  haproxy-certs:
    driver: local  # Volumen para los certificados de HAProxy

services:
  haproxy:
    image: haproxy:latest
    container_name: owncloud_haproxy
    restart: always
    ports:
      - "20268:80"   # HTTP
      - "20269:443"  # HTTPS
      - "20267:20267" # HAProxy stats
    volumes:
      - ./haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
      - ./haproxy/certs/haproxy.pem:/etc/ssl/certs/haproxy.pem:ro  # Certificado SSL
    depends_on:
      - owncloud1
      - owncloud2
    networks:
      - owncloud_net_docker

  owncloud1:
    image: owncloud/server:${OWNCLOUD_VERSION}
    container_name: owncloud1
    restart: always
    ports:
      - "20262:8080"  # HTTP OwnCloud (acceso directo, opcional)
    depends_on:
      - mariadb
      - redis
      - ldap
    environment:
      - OWNCLOUD_DB_TYPE=mysql
      - OWNCLOUD_DB_HOST=owncloud_mariadb
      - OWNCLOUD_DB_NAME=${MYSQL_DATABASE}
      - OWNCLOUD_DB_USERNAME=${MYSQL_USER}
      - OWNCLOUD_DB_PASSWORD=${MYSQL_PASSWORD}
      - OWNCLOUD_ADMIN_USERNAME=${ADMIN_USERNAME}
      - OWNCLOUD_ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - OWNCLOUD_REDIS_HOST=owncloud_redis
      - OWNCLOUD_LDAP_BASE_DN=${LDAP_BASE_DN}
      - OWNCLOUD_LDAP_ADMIN_PASSWORD=${LDAP_ADMIN_PASSWORD}

      # Ajustes para evitar bucles de redirección y forzar que OwnCloud
      # confíe en HAProxy en http://localhost:20260 (cambiado a 20268)
      - OWNCLOUD_DOMAIN=localhost
      - OWNCLOUD_TRUSTED_DOMAINS=localhost,127.0.0.1,localhost:20260,localhost:20268,localhost:20269,150.214.191.160:20267,150.214.191.160:20262,150.214.191.160:20268

      - OWNCLOUD_OVERWRITEHOST=localhost:20268
      - OWNCLOUD_OVERWRITEPROTOCOL=http
      - OWNCLOUD_OVERWRITEWEBROOT=
      - OWNCLOUD_OVERWRITECLIURL=http://localhost:20268

    networks:
      - owncloud_net_docker
    volumes:
      - files:/mnt/data

  owncloud2:
    image: owncloud/server:${OWNCLOUD_VERSION}
    container_name: owncloud2
    restart: always
    ports:
      - "20263:8080"  # HTTP OwnCloud (acceso directo, opcional)
    depends_on:
      - mariadb
      - redis
      - ldap
    environment:
      - OWNCLOUD_DB_TYPE=mysql
      - OWNCLOUD_DB_HOST=owncloud_mariadb
      - OWNCLOUD_DB_NAME=${MYSQL_DATABASE}
      - OWNCLOUD_DB_USERNAME=${MYSQL_USER}
      - OWNCLOUD_DB_PASSWORD=${MYSQL_PASSWORD}
      - OWNCLOUD_ADMIN_USERNAME=${ADMIN_USERNAME}
      - OWNCLOUD_ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - OWNCLOUD_REDIS_HOST=owncloud_redis
      - OWNCLOUD_LDAP_BASE_DN=${LDAP_BASE_DN}
      - OWNCLOUD_LDAP_ADMIN_PASSWORD=${LDAP_ADMIN_PASSWORD}

      # Mismos ajustes para OwnCloud2.
      - OWNCLOUD_DOMAIN=localhost
      - OWNCLOUD_TRUSTED_DOMAINS=localhost,127.0.0.1,localhost:20260,localhost:20268,localhost:20269,150.214.191.160:20263,150.214.191.160:20268
      - OWNCLOUD_OVERWRITEHOST=localhost:20268
      - OWNCLOUD_OVERWRITEPROTOCOL=http
      - OWNCLOUD_OVERWRITEWEBROOT=
      - OWNCLOUD_OVERWRITECLIURL=http://localhost:20268

    networks:
      - owncloud_net_docker
    volumes:
      - files:/mnt/data

  mariadb:
    image: mariadb:${MARIADB_VERSION}
    container_name: owncloud_mariadb
    restart: always
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DATABASE}
      - MYSQL_REPLICATION_MODE=master
      - MYSQL_REPLICATION_USER=repl_user
      - MYSQL_REPLICATION_PASSWORD=repl_password
    command: ["--max-allowed-packet=128M", "--innodb-log-file-size=64M"]
    volumes:
      - mysql:/var/lib/mysql
    networks:
      - owncloud_net_docker

  mariadb_slave:
    image: mariadb:${MARIADB_VERSION}
    container_name: owncloud_mariadb_slave
    restart: always
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DATABASE}
      - MYSQL_REPLICATION_MODE=slave
      - MYSQL_REPLICATION_USER=repl_user
      - MYSQL_REPLICATION_PASSWORD=repl_password
      - MYSQL_MASTER_HOST=owncloud_mariadb
    command: ["--max-allowed-packet=128M", "--innodb-log-file-size=64M"]
    depends_on:
      - mariadb
    volumes:
      - mysql:/var/lib/mysql_slave
    networks:
      - owncloud_net_docker

  redis:
    image: redis:${REDIS_VERSION}
    container_name: owncloud_redis
    restart: always
    command: ["--databases", "1"]
    ports:
      - "20266:6379"
    volumes:
      - redis:/data
    networks:
      - owncloud_net_docker

  ldap:
    image: osixia/openldap:1.5.0
    container_name: owncloud_ldap_server
    restart: always
    command: "--copy-service"
    environment:
      - LDAP_DOMAIN=${LDAP_DOMAIN}
      - LDAP_BASE_DN=${LDAP_BASE_DN}
      - LDAP_ADMIN_PASSWORD=${LDAP_ADMIN_PASSWORD}
    ports:
      - "20264:389"  # LDAP sin cifrar
      - "20265:636"  # LDAP cifrado
    volumes:
      - ldap-data:/var/lib/ldap
      - ldap-config:/etc/ldap/slapd.d
    networks:
      - owncloud_net_docker
networks:
  owncloud_net_docker:
    driver: bridge
    name: owncloud_net_docker
```
Observarmos como duplicamos el servicio de owncloud y el de mariadb para tener una copia de seguridad. Adicionalmente se usamos HaProxy para distribuir la carga. Mediante el siguiente fichero de configuración configuramos la distribución de la carga entre los diversos servicios owncloud esta se hace mediante la configuración fron-end y se distribuye el puerto 20268 hacia el :8080 el cual esta internamente mapeado por los dos servicios owncloud para escuchar de ahí. Y en el puerto 20267 podremos ver un desglose de las estadísticas que hemos ido recopilando en el servicio.

```haconfig
global
  log stdout format raw local0 info

# Configuración por defecto
defaults
  mode http
  log global
  timeout connect 15s
  timeout client 20s
  timeout server 20s
  timeout http-request 20s
  option httplog

# Interfaz de estadísticas de HAProxy
frontend stats
  bind *:20267
  stats enable
  stats uri /
  stats refresh 10s

# Frontend principal para OwnCloud
frontend owncloud_frontend
  bind *:20268  # HTTP
  bind *:20269 ssl crt /etc/ssl/certs/haproxy.pem  # HTTPS
  default_backend owncloud_backend

# Backend con balanceo roundrobin entre las 2 réplicas
backend owncloud_backend
  balance roundrobin
  server owncloud1 owncloud1:8080 check inter 2s fall 3 rise 2
  server owncloud2 owncloud2:8080 check inter 2s fall 3 rise 2

```
AL igual que el escenario 1 podemos usar el make para realizar las fases del despliegue de una manera mas automatizada. Este archivo automatiza y simplifica tareas como iniciar y detener los contenedores, gestionar múltiples escenarios con Docker Compose (`docker-compose1.yml` para el Escenario 1, `docker-compose2.yml` para el Escenario 2), así como tareas específicas relacionadas con LDAP (inicialización de la base, adición de usuarios, búsqueda y actualización de contraseñas).

Los comandos (`targets`) del Makefile están claramente diferenciados según su función:

- **start/stop/restart**: Control general de los servicios mediante Docker Compose.
- **start1/stop1/restart1**: Gestión específica del Escenario 1.
- **start2/stop2/restart2**: Gestión específica del Escenario 2.
- **ldap-init**: Inicializa LDAP con la estructura base definida en `base_dn.ldif`.
- **ldap-add**: Agrega usuarios y grupos definidos previamente en archivos LDIF.
- **ldap-search**: Facilita búsquedas LDAP desde la terminal.
- **ldap-update-passwords**: Permite actualizar fácilmente las contraseñas de los usuarios creados.

Este enfoque con `make` mejora notablemente la eficiencia del despliegue, asegurando que todas las acciones sean rápidas, repetibles y menos propensas a errores.

```
makefile
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

```
## Resultado

Al finalizar la configuración, podemos acceder al servicio OwnCloud a través de la **IP del servidor** en el **puerto 20268**, donde **HAProxy** se encarga de redirigir el tráfico a las diferentes réplicas de OwnCloud.  
Si iniciamos sesión con el usuario `juanitoggm` y la contraseña `juanito`, comprobaremos la persistencia de datos visualizando una imagen previamente subida (en este caso, una armadura de Zinogre).

**Vista de la cuenta de OwnCloud de `juanitoggm`:**  
![Owncloud](/P1/images/owncloudpesc2.png)

Paralelamente, podemos consultar las **estadísticas de HAProxy** accediendo al **puerto 20267**, donde se muestra información en tiempo real acerca del balanceo y estado de los distintos contenedores:

**Estadísticas de HAProxy en el puerto 20267:**  
![HaproxyStats](/P1/images/haproxystats.png)

