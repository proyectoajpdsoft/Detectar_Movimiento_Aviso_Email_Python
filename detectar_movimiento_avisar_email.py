import cv2
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Carpeta donde se guardarán las imágenes cuando se detecta movimiento
carpetaImagenes = r"D:\Mis documentos\ProyectoA\Python\detectar_movimiento_webcam\imagenes"

# Última fecha de envío de mail avisando de la detección de movimiento
fechaEnvioMail = datetime.now()
enviar = False

def enviarEmailConAdjunto(imagen):
    hora = datetime.now().strftime("%H:%M:%S")
    contenidoMensaje = f"Se ha detectado un movimiento a las: {hora} horas.\n\nPor https://proyectoa.com"
    emailEmisor = "email@email.com"
    usuarioEmail = "email@email.com"
    contrasenaEmail = "contraseña"
    emailDestinatario = "destinatario@destinatario.com"
    asunto = f"Detección de movimiento a las {hora}"
    servidorMail = "smtp.gmail.com"
    puertoServidorMail = 587

    # Creamos el mensaje
    mensaje = MIMEMultipart()
    mensaje["From"] = emailEmisor
    mensaje["To"] = emailDestinatario
    mensaje["subject"] = asunto
    mensaje.attach(MIMEText(contenidoMensaje, "plain"))
    
    # Adjuntamos la imagen capturada al correo electrónico    
    adjunto = open(imagen, "rb")
    # Creamos una instancia de MIMEBase
    partBase = MIMEBase("application", "octet-stream")
    # Para cambiar a formato codificado
    partBase.set_payload((adjunto).read())
    # Codificamos en base base64
    encoders.encode_base64(partBase)
    partBase.add_header("Content-Disposition", f"attachment; filename= {imagen}")
    # Adjuntamos la instancia partBase al mensaje
    mensaje.attach(partBase)
    print(f"{datetime.now()} Conectando con el servidor de correo electrónico...")
    # Creamos la sesión SMTP para el envío del mail
    servidorMail = smtplib.SMTP(servidorMail, puertoServidorMail)
    servidorMail.starttls() # Habilitamos la seguridad (casi todos los servidores requieren de TLS)
    servidorMail.login(usuarioEmail, contrasenaEmail)
    print(f"{datetime.now()} Enviando el mensaje de correo electrónico...")
    mensajeTexto = mensaje.as_string()
    servidorMail.sendmail(emailEmisor, emailDestinatario, mensajeTexto)
    servidorMail.quit()
    print(f"{datetime.now()} El correo electrónico ha sido enviado")

# Iniciamos la captura de vídeo desde la webcam
capturaVideo = cv2.VideoCapture(0)

# Leemos el primer frame de la captura de la webcam
videoIniciado, primerFrame = capturaVideo.read()
# Transformamos a escla de grises
imagenTransformada = cv2.cvtColor(primerFrame, cv2.COLOR_BGR2GRAY)
# Aplicamos filtro Gaussiano para quitar ruido de la imagen
imagenTransformada = cv2.GaussianBlur(imagenTransformada, (21, 21), 0)

# Vamos comprobando cada frame de la webcam
numFrame = 0
numDetecciones = 0
while capturaVideo.isOpened():
    # Leemos el siguiente frame
    videoIniciado, siguienteFrame = capturaVideo.read()
    # Si no hay más frames en el vídeo, salimos del bucle
    if not videoIniciado:
        print("No se ha encontrado imagen en la entrada de WebCam.")
        exit()
    numFrame = numFrame + 1
    # No tenemos en cuenta los primeros frames
    if numFrame > 10:
        # Realizamos las mismas transformaciones que para el primer frame (escala de grise, filtro gaussiano)
        imagenTransformadaSiguiente = cv2.cvtColor(siguienteFrame, cv2.COLOR_BGR2GRAY)
        imagenTransformadaSiguiente = cv2.GaussianBlur(imagenTransformadaSiguiente, (21, 21), 0)

        # Calculamos la diferencia entre los dos frames
        diferenciaImagenes = cv2.absdiff(imagenTransformada, imagenTransformadaSiguiente)
        # Transformamos la imagen en escala de grises a binaria
        _, imagenBinaria = cv2.threshold(diferenciaImagenes, 25, 255, cv2.THRESH_BINARY)
        #cv2.imshow("Depurar - Frame con imagen binaria", imagenBinaria)
        # Realizar la operación de dilatación de la imagen para aumentar el área y acentuar las características
        imagenDilatada = cv2.dilate(imagenBinaria, None, iterations=2)
        # Detectamos los contornos de la imagen binaria
        # Las curvas de nivel son curvas que unen todos los puntos continuos a lo largo de un límite con el mismo color o intensidad
        contornosImagen, _ = cv2.findContours(imagenDilatada, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # Recorremos todos los contornos detectados para recuadrarlos    
        for contorno in contornosImagen:
            # Descartamos los contornos con área inferior a 600
            if cv2.contourArea(contorno) < 600:
                continue
            numDetecciones += 1
            # Si es la segunda detección no la tenemos en cuenta (a partir de la tercera)
            if numDetecciones > 2:
                # Obtenemos la fecha y hora actuales para el nombre del fichero
                fechaHora = datetime.now().strftime("%Y%m%d_%H%M%S")
                nombreFichero = "img_.png"
                # Obtenemos un nombre de fichero con el año, mes, dia, hora, minuto y segundo
                # En formato img_aaaammdd_hhmmss_numframe.png
                nombreFichero = f"{nombreFichero.split(".")[0]}_{fechaHora}_{numFrame}.{nombreFichero.split(".")[-1]}"            
                # Guardamos la imagen en fichero para revisión
                nombreFichero = f"{carpetaImagenes}\\{nombreFichero}"
                cv2.imwrite(filename=nombreFichero, img=siguienteFrame)
                # Obtenemos las coordenadas del contorno para dibujar un recuadro
                x, y, w, h = cv2.boundingRect(contorno)
                # Dibujamos un recuadro alrededor del contorno para mostrarlo en el vídeo
                cv2.rectangle(siguienteFrame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                fechaDeteccionMovimiento = datetime.now()
                # Si han pasado 3 minutos desde que se envió el último mail de aviso de detección
                # de movimiento y se vuelve a detectar movimiento, se vuelve a enviar con nueva imagen capturada
                # Hacemos esta comprobación para evitar enviar muchos mail por minuto en caso de movimiento
                # Calcular la diferencia entre la hora actual y la de último envío de email
                diferenciaFechas = datetime.now() - fechaEnvioMail
                # Convertir la diferencia a minutos
                minutosDiferencia = diferenciaFechas.total_seconds() / 60
                # Si es la cuarta detección o si han pasado 3 minutos, se envía el email
                # Esta comprobación se hace para que no envíe email al abrir el programa
                # Puede que se tenga que ajustar el valor de numDetecciones
                # según la WebCam y el lugar donde se coloque
                # Así como el número de minutos a partir de cuando volvería a enviar email si detecta movimiento
                if numDetecciones == 4 or minutosDiferencia >= 3:
                    fechaEnvioMail = datetime.now()
                    enviar = False
                    enviarEmailConAdjunto(nombreFichero)
                else:
                    print(f"{datetime.now()} Se detecta movimiento. Faltan {3 - minutosDiferencia:.1f} minutos para nuevo envío email")
       
        # Mostramos la ventana con el vídeo capturado de la webcam
        cv2.imshow("ProyectoA - Deteccion de movimiento", siguienteFrame)

        # Cerramos la aplicación si se pulsa "s"
        if cv2.waitKey(1) & 0xFF == ord("s"):
            break
        # Reemplazamos la imagen inicial con la siguiente para "limpiar" los movimientos
        imagenTransformada = imagenTransformadaSiguiente

# Liberamos los recursos
capturaVideo.release()
cv2.destroyAllWindows()