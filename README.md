# androidpark
Aplicación para la solicitud de plazas de parking en el Edificio Bilma

# Salvedades
* Esto es un desarrollo experimental y como tal se ofrece con el único objetivo o esperanza de que sea útil, 
pero sin ningún tipo de garantías de que la aplicación no cause problemas en el funcionamiento normal del teléfono,
incremente el consumo de datos, cause la liberación de todas las plazas asignadas o que se coma al perro. 
* La aplicación no tiene ninguna relación ni con la empresa gestora del aparcamiento, ni con la gestión del edificio Bilma, 
ni con Alcatel-Lucent España. Únicamente hace uso del interfaz web ofrecido a los empleados para la gestión de sus plazas 
de parking

# Instalación
1. Utilizar el navegador del móvil para [descarga el archivo APK](https://github.com/j-santander/androidpark/releases/latest)
2. Abrir la carpeta de descargas del móvil y hacer click en el archivo descargado.
3. Permitir la instalación de aplicaciones desde orígenes desconocidos (temporalmente, una vez instalada se puede volver 
a la configuración de fábrica)

# Funcionamiento.
La aplicación consta de dos componentes lógicos:

1. El *Servicio*. Se ejecuta en segundo plano y es el encargado de realizar las peticiones hacia la página web. Cuando 
está funcionando un icono de ALU aparecerá en el área de notificación del teléfono. 
    * El Servicio arranca la primera vez que se ejecuta la aplicación y se puede arrancar y parar desde la aplicación.
    * El Servicio mantiene información (dinámica) de las peticiones realizadas, de forma que es capaz de periódicamente 
    de reactivar las peticiones (cuando la web las borra). La frecuencia de reactivación es cada 2 horas (por defecto) y 
    cada 5 minutos en el periodo de repesca (15:00-17:30) (pero sólo si hay una petición para el día siguiente)-
    * También hay un intento de reactivación (*last-call*) a las 14:50
    * Si el usuario ha configurado un *patrón de reserva*, el día 1 del mes, a las 11:00 se añadirán peticiones para el
    mes siguiente conforme al patrón. El tendrá la forma una lista separada por comas de *tokens*, siendo los tokens:
    ``todo`` (seleccionará todos los días del mes), ``L|M|X|J|V`` (seleccionará respectivamente todos los *Lunes*, 
    *Martes*, *Miércoles*, *Jueves* o *Viernes*)
2. La *Aplicación*. Se lanza con el icono de la aplicación o pulsando en la notificación cuando el Servicio está activo.
La Aplicación permite visualizar las plazas asignadas y realizar nuevas peticiones:
    * Los controles son:
        * Click en un día: Marca el día para que se solicite su cambio (para liberar/no-solicitar/solicitar). La marca se 
        represeta por una banda diagonal del color del estado objetivo.
        * Click en un día de la semana (L,X,M,J,V): Marca esos días de ese día de la semana, pero únicamente para solicitar.
        * Click en el mes: Marca todos los días, de nuevo, únicamente para solicitar.
        * Botón de Configuración: Abre el panel de configuración, permite cambiar:
          * el nombre de usuario
          * la contraseña
          * dirección del servidor web.
          * El patrón de reserva (e.g. ``"L,X,J,V"``)
          * Frecuencia de refresco de datos en la aplicación (defecto 5 min) [0-1440]. El valor ``0`` indica que el 
          refresco estará desactivado.
          * Frecuencia de reactivación de solicitudes desde el servidor (defecto 2 horas) [0-1440]. El valor ``0`` 
          indica que la reactivación estará desactivada.
          * Frecuencia de reactivación de solicitudes durante el periodo de respeca desde el servidor (defecto 5 min) 
          [0-1440]. El valor ``0`` indica que la reactivación en repesca estará desactivada.
          * Temporizador en la comunicación entre el Servicio y la Aplicación (defecto 15 segundos) [1-60]
        * Botón de Envío de solicitudes: Envía los días marcados como solicitudes al servicio. El Servicio reemplazará 
        las solicitudes anteriores con estas nuevas y tratará de enviarlas al servidor. Cuando concluya este primer
        intento (nota: puede tardar un tiempo para un número elevado de solicitudes), se refrescará automáticamente
        la vista.
        * Botón de refresco manual: Envía una solicitud al servicio para que relea la página web y actualice el estado
        de los días (y de las solicitudes pendientes)
        * Botón de control del servicio: Indica el estado del servicio (cuadrado: servicio en ejecución, triángulo:
        servicio parado) y permite solicitar el arranque (triángulo) o la parada (cuadrado).

Si no hay datos de usuario, el panel de configuración se mostrará al arrancar la configuración.
