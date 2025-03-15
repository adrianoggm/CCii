
# Realización del Escenario 1

## Usando Docker

A continuación se detallan los pasos seguidos para realizar el despliegue del escenario 1 utilizando Docker.

### Paso 1: Configuración del servicio LDAP

Primero se desplegó el servidor LDAP usando Docker para garantizar la persistencia de datos en caso de que el contenedor se elimine:

```bash
docker run -p 20273:389 -p 20274:636 volume /home/adrianoggm/data/slapd/database:/var/lib/ldap --volume /home/adrianoggm/data/slapd/config:/etc/ldap/slapd.d --name openldap-server --detach osixia/openldap:1.5.0
```
### Paso 2: Configuración de la estructura LDAP (`base_dn.ldif`)

Se creó un archivo `base_dn.ldif` con la siguiente estructura organizativa:

```ldif
dn: dc=example,dc=com
objectClass: top
objectClass: dcObject
objectClass: organization
o: Example Organization
dc: example

dn: ou=users,dc=example,dc=com
objectClass: top
objectClass: organizationalUnit
ou: users

dn: ou=groups,dc=example,dc=com
objectClass: top
objectClass: organizationalUnit
ou: groups
```
Posteriormente, se añadió esta estructura al servidor LDAP con el comando:

```bash
ldapadd -x -H ldap://localhost:20273 -D "cn=admin,dc=example,dc=com" -w admin -c -f base_dn.ldif
  ```
### Paso 3: Añadir usuarios al servidor LDAP

Se añadieron dos usuarios, `adrianoggm` y `juanitoggm`, utilizando definiciones LDIF (`usuarios.ldif`):

```ldif
dn: uid=adrianoggm,ou=users,dc=example,dc=com
objectClass: top
objectClass: posixAccount
objectClass: inetOrgPerson
cn: Adrian Oggm
sn: Oggm
uid: adrianoggm
uidNumber: 501
gidNumber: 20
homeDirectory: /home/adrianoggm
loginShell: /bin/bash
gecos: Adrian Oggm
userPassword: {crypt}x
mail: adrianoggm@example.com

dn: uid=juanitoggm,ou=users,dc=example,dc=com
objectClass: top
objectClass: posixAccount
objectClass: inetOrgPerson
cn: Juanitoggm
sn: Toggm
uid: juanitoggm
uidNumber: 502
gidNumber: 20
homeDirectory: /home/juanitoggm
loginShell: /bin/bash
gecos: Juanitoggm
userPassword: {crypt}x
mail: juanitoggm@example.com
```
Para añadir estos usuarios al servidor LDAP se utilizó el comando adaptandolo a cada usuario respectivamente:

```bash
ldapadd -x -H ldap://localhost:20273 -D "cn=admin,dc=example,dc=com" -w admin  -c -f usuarios.ldif
  ```
Finalmente, para asignar contraseñas a los usuarios se ejecutó el siguiente comando Docker:

```bash

docker exec owncloud_ldap_server ldapmodify -x \
  -H ldap://localhost:20273 \
  -D "cn=admin,dc=example,dc=com" \
  -w admin \
  -c -f /tmp/ldap_password_adrianoggm.ldif
```
### Paso 4: Añadir servicio MariaDB

Para desplegar MariaDB, primero aseguramos que tenemos disponible la imagen más reciente descargándola desde Docker Hub:

```bash
docker pull mariadb:latest
A continuación ejecutamos el siguiente comando para lanzar el contenedor MariaDB con persistencia de datos y variables de entorno necesarias para definir la base de datos, el usuario y su contraseña:

```bash
docker run --detach \
  --name mariadb \
  -p 20262:3306 \
  -v /home/adrianoggm/mariadbdirectory:/var/lib/mysql \
  --env MARIADB_DATABASE=test \
  --env MARIADB_USER=usuario \
  --env MARIADB_PASSWORD=contraseña \
  mariadb:latest
```
Nota: Recuerda sustituir usuario y contraseña por los valores que deseas usar.

Finalmente, conectamos los contenedores LDAP y MariaDB a la misma red Docker (owncloud-net) para que puedan comunicarse entre sí:

```bash
docker network connect owncloud-net mariadb
docker network connect owncloud-net openldap-server
```
### Paso 5: Conectar el servicio OwnCloud

Finalmente, añadimos el servicio web OwnCloud usando el siguiente comando Docker, asegurando que esté conectado a la red Docker previamente creada (`owncloud-net`) para permitir la comunicación con LDAP y MariaDB:

```bash
 docker run -d --name owncloud --network owncloud-net -p 20270:8080 -p 20271:443
```
### Paso 6 Redis
Añadimos el servicio Redis en el puerto 20272 con persistencia de datos, utilizando el siguiente comando:

```bash
docker run --detach \
  --name redis \
  --network owncloud-net \
  -p 20272:6379 \
  --volume /home/adrianoggm/redisdata:/data \
  redis:latest
```
Una vez completada la instalación, podemos configurar LDAP en OwnCloud siguiendo estos pasos:

1. **Iniciar sesión:**  
   Accedemos a OwnCloud con el usuario `admin` y la contraseña definida (en este ejemplo, `adminpassword`).  
   > *Nota*: En algunas imágenes de OwnCloud, el módulo de LDAP viene preinstalado. Si no es tu caso, instálalo desde el *Marketplace* de OwnCloud.

2. **Acceder a la configuración de LDAP:**  
   Desde el perfil de administrador, navegamos a **Settings** (Configuración) > **User Authentication** (Autenticación de usuarios) y seleccionamos la opción **LDAP**.

3. **Configurar OpenLDAP:**  
   Rellenamos los campos correspondientes a nuestro servidor LDAP (dirección, DN base, credenciales de administrador, etc.).  
   Cuando aparezca la marca verde (*check*), significa que la comunicación entre OwnCloud y OpenLDAP se ha establecido correctamente.

**Vista de la cuenta de OwnCloud de `admin` configurando LDAP:**  
![Owncloud](/P1/images/Ldapconfig.png)

4. **Probar el acceso con usuarios LDAP:**  
   Tras la configuración, podemos iniciar sesión con los usuarios creados en LDAP, por ejemplo, `juanitoggm`. Para verificar la persistencia y el correcto funcionamiento de la integración, subimos una imagen de la armadura de Zinogre a su espacio de OwnCloud.

**Vista de la cuenta de OwnCloud de `juanitoggm`:**  
![Owncloud](/P1/images/owncloudpesc1.png)

Con estos pasos, tu entorno OwnCloud conectado a OpenLDAP estará completamente operativo.

## Usando Docker-compose
Para simplificar el proceso anterior, se preparó un archivo docker-compose (docker-compose1.yml) ubicado en el directorio Escenario1. Docker Compose facilita la configuración y gestión simultánea de múltiples contenedores.

A continuación, se presenta dicho archivo, donde se definen claramente todos los servicios anteriormente desplegados de forma individual con Docker, así como las redes y volúmenes para persistencia de datos:
Observaremos que hay variables que vienen dadas por el fichero .env que contiene algunas variables de entorno.

``` docker-compose
    version: "3.8"

# Definición de volúmenes locales para persistencia de datos
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

networks:
  owncloud_net:
    driver: bridge

services:
  owncloud:
    image: owncloud/server:${OWNCLOUD_VERSION}
    container_name: owncloud_server
    restart: always
    ports:
      - "20270:8080"    # HTTP (OwnCloud en 20270)
      - "20271:443"     # HTTPS (OwnCloud en 20271)
    depends_on:
      - mariadb
      - redis
      - ldap
    environment:
      - OWNCLOUD_DOMAIN=${OWNCLOUD_DOMAIN}
      - OWNCLOUD_TRUSTED_DOMAINS=${OWNCLOUD_TRUSTED_DOMAINS}
      - OWNCLOUD_DB_TYPE=mysql
      - OWNCLOUD_DB_NAME=${MYSQL_DATABASE}
      - OWNCLOUD_DB_USERNAME=${MYSQL_USER}
      - OWNCLOUD_DB_PASSWORD=${MYSQL_PASSWORD}
      - OWNCLOUD_DB_HOST=owncloud_mariadb
      - OWNCLOUD_ADMIN_USERNAME=${ADMIN_USERNAME}
      - OWNCLOUD_ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - OWNCLOUD_MYSQL_UTF8MB4=true
      - OWNCLOUD_REDIS_ENABLED=true
      - OWNCLOUD_REDIS_HOST=redis
    healthcheck:
      test: ["CMD", "/usr/bin/healthcheck"]
      interval: 30s
      timeout: 10s
      retries: 5
    volumes:
      - files:/mnt/data
    networks:
      - owncloud_net

  mariadb:
    image: mariadb:${MARIADB_VERSION}
    container_name: owncloud_mariadb
    restart: always
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DATABASE}
    command: ["--max-allowed-packet=128M", "--innodb-log-file-size=64M"]
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-u", "root", "--password=${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - mysql:/var/lib/mysql
    networks:
      - owncloud_net

  redis:
    image: redis:${REDIS_VERSION}
    container_name: owncloud_redis
    restart: always
    command: ["--databases", "1"]
    ports:
      - "20272:6379"   # Redis en 20272
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - redis:/data
    networks:
      - owncloud_net

  ldap:
    image: osixia/openldap:1.5.0
    container_name: owncloud_ldap_server
    restart: always
    command: "--copy-service"
    environment:
      - LDAP_TLS_VERIFY_CLIENT=never
      - LDAP_DOMAIN=${LDAP_DOMAIN}
      - LDAP_BASE_DN=${LDAP_BASE_DN}
      - LDAP_ADMIN_PASSWORD=${LDAP_ADMIN_PASSWORD}
      - LDAP_CONFIG_PASSWORD=${LDAP_CONFIG_PASSWORD}
      - LDAP_READONLY_USER=true
      - LDAP_READONLY_USER_USERNAME=readonly
      - LDAP_READONLY_USER_PASSWORD=readonly-password
    ports:
      - "20273:389"   # LDAP sin cifrar en 20273
      - "20274:636"   # LDAP cifrado en 20274
    volumes:
      - ldap-data:/var/lib/ldap
      - ldap-config:/etc/ldap/slapd.d
      - ./ldap/ldif:/container/service/slapd/assets/config/bootstrap/ldif/custom
    networks:
      - owncloud_net
```
Adicionalmente, he creado un **Makefile** que permite gestionar cómodamente diferentes acciones sobre los servicios desplegados. Este archivo automatiza y simplifica tareas como iniciar y detener los contenedores, gestionar múltiples escenarios con Docker Compose (`docker-compose1.yml` para el Escenario 1, `docker-compose2.yml` para el Escenario 2), así como tareas específicas relacionadas con LDAP (inicialización de la base, adición de usuarios, búsqueda y actualización de contraseñas).

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
Tras ejecutar los comandos del make como start1 o restart1 y configurado los servicios de ldap con su init y ldap-add y su change-passwords podremos ver el siguiente despliegue de contenedores realizando un docker ps.

**Vista de los contenedores desplegados:**  
![Docker ps](/P1/images/escenario1dockerps.png)  

Con esto podemos entrar mediante la  ip designada del servidor en el puerto 20270 el servicio owncloud  y si entramos en la cuenta juanitoggm con contraseña juanito podremos ver una imagen subida de una armudura de zinogre que comprueba la presistencia de todo.

**Vista de la cuenta de OwnCloud de `juanitoggm`:**  
![Owncloud](/P1/images/owncloudpesc1.png)  