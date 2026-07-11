import re

filepath = "/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx"
with open(filepath, "r") as f:
    content = f.read()

# Add the greetings and state
greetings_code = """
  const [greeting, setGreeting] = useState("Dashboard");

  useEffect(() => {
    const hour = new Date().getHours();
    
    const morningGreetings = [
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
    ];

    let possibleGreetings = [];
    if (hour >= 5 && hour < 12) {
      possibleGreetings = [...morningGreetings, ...generalGreetings];
    } else if (hour >= 12 && hour < 19) {
      possibleGreetings = [...afternoonGreetings, ...generalGreetings];
    } else {
      possibleGreetings = [...eveningGreetings, ...generalGreetings];
    }

    const randomGreeting = possibleGreetings[Math.floor(Math.random() * possibleGreetings.length)];
    setGreeting(randomGreeting);
  }, []);
"""

# Find where to insert it (after setIsDark state)
content = content.replace('const [isDark, setIsDark] = useState(true);', 'const [isDark, setIsDark] = useState(true);\n' + greetings_code)

# Replace the h1 and p tags
content = content.replace(
    '<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">Dashboard</h1>',
    '<h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">{greeting}</h1>'
).replace(
    '<p className="text-neutral-500 mt-1">Bienvenido a tu panel de control</p>',
    '<p className="text-neutral-500 mt-1">Resumen general de rendimiento</p>'
)

with open(filepath, "w") as f:
    f.write(content)
