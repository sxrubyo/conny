import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

old_greetings = """    const morningGreetings = [
      "¡Buenos días, Santiago!",
      "Hola Santiago, excelente mañana.",
      "Bienvenido, Santiago. ¿Listo para hoy?",
      "Santiago, que tengas un gran día.",
      "Buenos días, Santiago. Tu panel te espera.",
      "¡Hola Santiago! Iniciemos la jornada.",
      "Buen día, Santiago. Todo bajo control.",
      "Santiago, momento de revisar las métricas.",
      "Hola Santiago. Las estadísticas amanecieron bien.",
      "¡Excelente mañana, Santiago!"
    ];

    const afternoonGreetings = [
      "¡Buenas tardes, Santiago!",
      "Hola Santiago, ¿cómo va el día?",
      "Santiago, excelente tarde para revisar números.",
      "Buenas tardes, Santiago. Aquí está tu resumen.",
      "Hola Santiago, el panel está actualizado.",
      "Santiago, los datos de hoy lucen prometedores.",
      "¡Buenas tardes! Seguimos optimizando, Santiago.",
      "Hola Santiago. Es momento del corte de la tarde.",
      "Bienvenido de nuevo esta tarde, Santiago.",
      "Santiago, espero estés teniendo un día productivo."
    ];

    const eveningGreetings = [
      "¡Buenas noches, Santiago!",
      "Hola Santiago, terminando la jornada.",
      "Santiago, un vistazo final antes de descansar.",
      "Buenas noches, Santiago. Así cerramos hoy.",
      "Hola Santiago. Las métricas nocturnas están listas.",
      "Santiago, buen trabajo el de hoy.",
      "¡Buenas noches! Los servidores siguen trabajando, Santiago.",
      "Hola Santiago. Resumen nocturno preparado.",
      "Santiago, hora de ver los resultados del día.",
      "Cerremos el día con excelentes números, Santiago."
    ];

    const generalGreetings = [
      "Bienvenido a tu centro de control, Santiago.",
      "Santiago, aquí tienes el panorama actual.",
      "Hola Santiago, todo está en orden.",
      "¡Qué gusto verte de nuevo, Santiago!",
      "Santiago, tu entorno de gestión.",
    ];"""

new_greetings = """    const userName = "Santiago";
    
    const morningGreetings = [
      `¡Buenos días, ${userName}!`,
      `Hola, ${userName}`,
      `Buen día, ${userName}`,
      `Excelente mañana, ${userName}`,
      `¿Qué tal, ${userName}?`,
      `Feliz mañana, ${userName}`,
      `Bienvenido, ${userName}`,
      `¡Hola de nuevo, ${userName}!`,
      `Saludos, ${userName}`,
      `Muy buenos días, ${userName}`
    ];

    const afternoonGreetings = [
      `¡Buenas tardes, ${userName}!`,
      `Hola, ${userName}`,
      `Buena tarde, ${userName}`,
      `Excelente tarde, ${userName}`,
      `¿Qué tal, ${userName}?`,
      `Feliz tarde, ${userName}`,
      `Bienvenido, ${userName}`,
      `¡Hola de nuevo, ${userName}!`,
      `Saludos, ${userName}`,
      `Muy buenas tardes, ${userName}`
    ];

    const eveningGreetings = [
      `¡Buenas noches, ${userName}!`,
      `Hola, ${userName}`,
      `Buena noche, ${userName}`,
      `Excelente noche, ${userName}`,
      `¿Qué tal, ${userName}?`,
      `Feliz noche, ${userName}`,
      `Bienvenido, ${userName}`,
      `¡Hola de nuevo, ${userName}!`,
      `Saludos, ${userName}`,
      `Muy buenas noches, ${userName}`
    ];

    const generalGreetings = [
      `Hola, ${userName}`,
      `Bienvenido de vuelta`,
      `Bienvenido, ${userName}`,
      `Hola de nuevo`,
      `¡Qué tal, ${userName}!`
    ];"""

content = content.replace(old_greetings, new_greetings)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
