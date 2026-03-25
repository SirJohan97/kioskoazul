# Documentacion Oficial de Kiosko Azul (v2.0)
Fase de Escala Comercial y Ecommerce Gastronomico

Este documento engloba todas las capacidades, modulos y caracteristicas que posee actualmente el ecosistema de "Kiosko Azul" desarrolladas durante la ultima sesion de implementacion. El proyecto ha evolucionado de un simple landing page a una plataforma completa de comercio electronico gastronomico con logistica automatizada, seguridad y administracion en tiempo real.

---

## 1. Sistema de Usuarios y Autenticacion Restringida
El flujo de compras ha sido rediseñado para forzar la creacion de perfiles, garantizando seguridad y seguimiento preciso de operaciones.

* Registro e Inicio de Sesion Obligatorio: Ningun usuario puede agregar items al carrito como invitado y proceder a la pasarela de pagos sin haberse registrado o iniciado sesion. El sistema bloquea el avance hacia el checkout si el perfil no esta activo.
* Recuperacion de Contrasenas via Correo Electronico (SMTP): Si un cliente olvida su clave, la plataforma despliega una ventana modal pidiendo su correo. El backend escrito en Python emite un codigo algebraico de 6 digitos generado aleatoriamente que es enviado a su bandeja de entrada real mediante el protocolo SMTP. Este codigo caduca en 15 minutos exactos y desbloquea en pantalla el reseteo de la contraseña del cliente.
* Aislamiento de Data: Elimincion y control de antiguas entidades, dejando la base de usuarios pre-comerciales en cero, lista para migracion al nuevo formato de tablas con correos obligatorios.

---

## 2. Flujo de Logistica de Entregas (Pick-Up y Delivery)
La plataforma ahora soporta logistica fisica avanzada para despachos de motorizados.

* Selector de Tipo de Entrega: En la zona de checkout, el sistema le instruye al usuario declarar su tipo de retiro: "Pick-Up" o "Delivery". Si elije Pick-Up, la orden asume cero cargos extras. Si elije Delivery, se expanderá el formulario pidiendo direcciones.
* Zonas Tarifarias de Delivery Dinamicas: El administrador puede crear "Zonas Geo" desde su panel de ajustes (Ej. Zona Centro, Zona Residencias Norte) y asignarle libremenente a cada una un costo en dolares u otra moneda base. En el carrito del cliente, se le fuerza a seleccionar en cual de estas zonas vive, sumandose matematicamente y en tiempo real el monto de la "Zona X" al precio final de su factura.
* Libreta Multidirecciones Intelige: Al momento del pedir su factura, el framework web rescata a traves de la API Rest las ultimas direcciones usadas por ese cliente. El cliente podra seleccionar una de sus locaciones preguardadas (ej: "Oficina", "Hogar") con un solo toque autocompletando todo el checkout para una experiencia rapida, asi como tambien guardar nuevas locaciones.

---

## 3. Restriccion de Horarios Comerciales y Pagos Controlados
* Cierre y Apertura Automatica (08:00 AM a 08:00 PM): El sistema blinda y valida la hora del cronometro local e internacional asegurando rigidez operativa. Si algun cliente desvela intentar abrir compras pasadas las 8 pm o antes de las 8 am, la interface despliega una alerta de horarios cerrados, bloqueando por defecto la generacion de ordenes desde los endpoints de back-end.
* Metodos de Pago Clasificados: Integracion categorizada y ampliada de pasarelas de recoleccion, permitiendole al cliente certificar si pago por "Pago Movil Provincial", "Pago Movil BDV", "Mercantil", "Binance Pay - Tether", "Zelle". Estos a su vez exigen como valor no-nulo el ingreso finalitario de un numero de comprobante o referencia estricto en el formulario antes de crear la orden.

---

## 4. Perfil Historico y Monitor De Rastreo "Mis Pedidos"
* Modulo Extendido "Mis Pedidos": Eliminacion oficial del modulo generico basico "Escribir tracking reference". Se inyecto un nuevo segmento en el portal, atado y privado directamente al usuario activo. Renderizando esteticamente en tarjetas y listados historicos "Todas sus compras pasadas o presentes" en Kiosko Azul detalladas por Total, Fechas ISO y Lista de Platos.
* Estado Auto-Refrescante Asincrono: En la misma bandeja, el cliente percibe con colores visuales la operacion de la cocina sobre su pedido: Pendiente de Confirmacion, Preparando, Listo en Barra o Entregado Totalmente. Eliminando interrogantes tras pagar.

---

## 5. Panel Administrativo Mejorado y Dashboards
Ampliacion profunda y visual en el panel secreto o de "Backoffice" en propiedad de la empresa, agregando control a estas nuevas variantes.

* Configuador Administrativo Central (admin-config): Nuevo modulo agregado en el menu lateral de los administradores que permite en caliente registrar, editar precios o suprimir temporalmente las mencionadas "Tarifas de Delivery Zonal" mostradas dinamicamente en la URL de los clientes.
* Enrutamiento Logistico en Telegram: El script que dispara actas a Telegram fue modificado. Ademas de alertar pago y referencia, provee el dictamen crucial al chef advirtiendole verbalmente la modalidad de Entrega del cliente, incrustando la Direccion Exacta y Monto Flete.
* Graficas Financieras Analiticas y Arrays (Chart.js): Creacion de un End-Point especificamente configurado en Python para atrapar variables brutas de todos las ventas historicas. Integrandolo a un lienzo dinamico alimentado por de la famosa libreria "Chart.js" que grafica el espectro de ventas y acumulacion financiera en formato lineal, reflejado y sumurizado de las ventas completadas o preparadas por cada uno de los ultimos 7 Dias operacionales sin requerir uso de aplicaciones terceras de facturacion. Exluyendo ordenes Canceladas.
