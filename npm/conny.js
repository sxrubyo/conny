#!/usr/bin/env node

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const chalk = require("chalk");
const ora = require("ora");

const packageRoot = path.resolve(__dirname, "..");
const metadata = JSON.parse(fs.readFileSync(path.join(packageRoot, "package.json"), "utf8"));
const packageVersion = String(metadata.version || "").trim();
const connyHome = process.env.CONNY_HOME || path.join(os.homedir(), ".conny");
const repoDir = path.join(connyHome, "repo");
const runtimeDir = path.join(connyHome, "runtime");
const workspaceConfigPath = path.join(connyHome, "config.json");
const sharedTelegramRoutesPath = path.join(connyHome, "shared_telegram_routes.json");
const entrypoint = path.join(repoDir, "conny_app.py");
const legacyEntrypoint = path.join(repoDir, "conny_cli.py");
const criticalPythonPackages = [
  "rich>=13.0.0",
  "deep-translator>=1.11.0",
  "httpx==0.27.0",
  "python-dotenv==1.0.1",
  "fastapi==0.115.0",
  "pydantic>=2.0",
  "questionary>=2.0.0",
];

const SKIP_NAMES = new Set([
  ".git",
  ".github",
  ".nova",
  ".pytest_cache",
  ".ruff_cache",
  ".venv",
  "__pycache__",
  "backups",
  "docs",
  "logs",
  "node_modules",
  "output",
  "screenshots",
  "tests",
  "tmp",
]);

const commandGroups = [
  {
    category: "Gestión",
    cmds: [
      ["init", "Primer setup guiado del producto"],
      ["new [nombre]", "Crear instancia para un cliente (wizard)"],
      ["list / ls", "Ver todas las instancias"],
      ["dashboard", "Panel en tiempo real"],
      ["template [sector]", "Ver/crear desde plantilla"],
      ["interactive", "Modo interactivo (shell)"],
      ["zero [n]", "Entregar instancia a nuevo cliente (borra todo)"],
    ]
  },
  {
    category: "Monitoreo",
    cmds: [
      ["status [n]", "Estado detallado de la instancia"],
      ["health", "Health check rápido de los servicios"],
      ["metrics [n]", "Métricas de uso y rendimiento"],
      ["analytics [n]", "Análisis de conversaciones y datos"],
      ["logs [n]", "Logs en tiempo real"],
      ["alerts", "Sistema de alertas y notificaciones"],
    ]
  },
  {
    category: "Operaciones",
    cmds: [
      ["config [n]", "Editar configuración y variables de entorno"],
      ["restart [n]", "Reiniciar procesos de la instancia (o 'all')"],
      ["stop [n]", "Detener procesos de la instancia"],
      ["scale [n] [num]", "Escalar workers de mensajería"],
      ["clone [n]", "Clonar configuración e instancia"],
      ["reset [n]", "Resetear base de datos/sesión de testing"],
      ["delete [n]", "Eliminar instancia permanentemente"],
      ["batch", "Operaciones en lote sobre múltiples instancias"],
    ]
  },
  {
    category: "Datos & Testing",
    cmds: [
      ["backup [n]", "Crear snapshot de seguridad de la instancia"],
      ["restore [file]", "Restaurar instancia desde un snapshot"],
      ["export [n]", "Exportar conversaciones a JSON/CSV"],
      ["import [file]", "Importar configuración o base de datos"],
      ["search [query]", "Buscar términos en logs/mensajes"],
      ["test [n]", "Probar respuestas y flujos conversacionales"],
    ]
  },
  {
    category: "Sistema & Seguridad",
    cmds: [
      ["doctor", "Diagnóstico completo del sistema y dependencias"],
      ["audit", "Auditoría de seguridad y chequeo de vulnerabilidades"],
      ["benchmark", "Test de rendimiento de CPU/DB/Red"],
      ["secure", "Guía y validación de seguridad de endpoints"],
      ["rotate-keys", "Rotar claves de API y tokens de acceso"],
      ["upgrade", "Actualizar código base de Conny"],
      ["cleanup", "Limpiar archivos de log y caché temporal"],
      ["diff", "Comparar diferencias entre dos instancias"],
      ["guide", "Guía interactiva de operación de Conny"],
    ]
  },
  {
    category: "Black Boss (Personalización)",
    cmds: [
      ["bb config [n]", "Crear y ajustar agente, prompt y personalidad"],
      ["bb chat [n]", "Abrir chat operativo directo con el agente"],
      ["bb doctor", "Diagnóstico rápido del Black Boss Engine"],
      ["bb sync", "Propagar runtime exacto a todas las instancias"],
      ["bb new", "Crear nueva instancia bajo el Black Boss Engine"],
      ["bb guide", "Abrir guía operativa avanzada"],
    ]
  },
  {
    category: "Modelo & Calidad V8",
    cmds: [
      ["modelo [n]", "Ver/cambiar el LLM de una instancia en caliente"],
      ["simular [n]", "Simular 10 conversaciones para detectar alucinaciones"],
      ["v8 [n]", "Estado de los 15 sistemas inteligentes V8"],
      ["quality [n]", "Score de humanidad de las últimas respuestas"],
      ["briefing [n]", "Briefing diario con leads calientes detectados"],
      ["campana [n]", "Campañas de seguimiento y reactivación saliente"],
      ["latency [n]", "Test de latencia HTTP + LLM en tiempo real"],
      ["cost [n]", "Estimación de costos mensuales del LLM"],
      ["warmup [n]", "Pre-calentar la instancia antes de lanzar a prod"],
      ["watchdog", "Monitor continuo con auto-restart inteligente"],
    ]
  },
  {
    category: "Canales & Activación V7",
    cmds: [
      ["token [n]", "Generar código de activación"],
      ["tokens [n]", "Listar tokens de activación generados"],
      ["activar [n]", "Activar instancia directamente (sin token)"],
      ["bridge", "Estado y monitoreo del WhatsApp Bridge"],
      ["bridge fix", "Fix de configuración del bridge de WhatsApp"],
      ["bridge qr", "Ver código QR para enlazar número de WhatsApp"],
      ["instagram [n]", "Conectar y monitorear Instagram DMs"],
      ["pagos [n]", "Configurar/monitorear pagos desde el chat"],
    ]
  }
];

function printBanner() {
  console.log();
  console.log(chalk.hex('#EC4899').bold('  conny-agent') + 
              chalk.hex('#8B5CF6').dim(` · v${packageVersion} · innvisor.ai`));
  console.log(chalk.hex('#444')('  ─────────────────────────'));
  console.log();
}

function printCommands() {
  for (const group of commandGroups) {
    console.log(`  ${chalk.hex('#8B5CF6').bold(group.category)}`);
    for (const [cmd, desc] of group.cmds) {
      const formattedCmd = `conny ${cmd}`;
      console.log(`    ${chalk.white.bold(formattedCmd.padEnd(25))} ${chalk.dim(desc)}`);
    }
    console.log();
  }
  
  console.log(`  ${chalk.hex('#8B5CF6').bold("Sectores disponibles")}`);
  console.log(`    ${chalk.dim("salud, inmobiliario, e-commerce, educacion, legal, finanzas, turismo, gastronomia, belleza, automotriz, gimnasios, soporte, otro")}\n`);
}

function ensureDir(target) {
  fs.mkdirSync(target, { recursive: true });
}

function fail(message) {
  console.error(chalk.red(`ERR ${message}`));
  process.exit(1);
}

function runtimeCandidates() {
  return [
    path.join(runtimeDir, "bin", "python"),
    path.join(runtimeDir, "bin", "python3"),
    path.join(runtimeDir, "Scripts", "python.exe"),
  ];
}

function resolveRuntime() {
  for (const candidate of runtimeCandidates()) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return "";
}

function runAndReturn(command, args, extraEnv = {}, options = {}) {
  return spawnSync(command, args, {
    stdio: "inherit",
    env: { ...process.env, ...extraEnv },
    ...options,
  });
}

function syncTree(sourceDir, targetDir) {
  ensureDir(targetDir);
  for (const entry of fs.readdirSync(sourceDir, { withFileTypes: true })) {
    if (SKIP_NAMES.has(entry.name)) {
      continue;
    }
    const sourcePath = path.join(sourceDir, entry.name);
    const targetPath = path.join(targetDir, entry.name);
    if (entry.isDirectory()) {
      syncTree(sourcePath, targetPath);
      continue;
    }
    ensureDir(path.dirname(targetPath));
    fs.copyFileSync(sourcePath, targetPath);
  }
}

function readInstalledVersion() {
  const installedPackage = path.join(repoDir, "package.json");
  if (!fs.existsSync(installedPackage)) {
    return "";
  }
  try {
    const payload = JSON.parse(fs.readFileSync(installedPackage, "utf8"));
    return String(payload.version || "").trim();
  } catch (_err) {
    return "";
  }
}

function findSystemPython() {
  const candidates =
    process.platform === "win32"
      ? [
          ["py", ["-3"]],
          ["python", []],
          ["python3", []],
        ]
      : [
          ["python3", []],
          ["python", []],
        ];
  for (const [command, prefixArgs] of candidates) {
    const probe = spawnSync(command, [...prefixArgs, "-c", "import json,sys; print(json.dumps({'exe': sys.executable, 'ver': list(sys.version_info[:3])}))"], {
      stdio: ["ignore", "pipe", "pipe"],
      encoding: "utf8",
      env: process.env,
    });
    if (probe.status === 0) {
      try {
        const payload = JSON.parse(String(probe.stdout || "").trim());
        const version = payload.ver || [];
        if (version.length >= 2 && (version[0] > 3 || (version[0] === 3 && version[1] >= 9))) {
          return { command, prefixArgs, executable: payload.exe, version };
        }
      } catch (_err) {
        // ignore and continue
      }
    }
  }
  return null;
}

function runtimeLooksHealthy(runtime) {
  if (!runtime || !fs.existsSync(runtime)) {
    return false;
  }
  const probe = spawnSync(
    runtime,
    ["-c", "import rich,deep_translator,fastapi,httpx,dotenv,pydantic,questionary; print('ok')"],
    { stdio: ["ignore", "pipe", "pipe"], encoding: "utf8", env: process.env }
  );
  return probe.status === 0;
}

function installRuntimeDependencies(runtime, spinner, allowFullFailure = true) {
  let result;
  if (spinner) {
    spinner.text = chalk.hex('#8B5CF6')("Installing Conny CLI runtime dependencies...");
  }
  result = spawnSync(
    runtime,
    ["-m", "pip", "install", "--disable-pip-version-check", ...criticalPythonPackages],
    { stdio: ["ignore", "pipe", "pipe"], env: process.env }
  );
  if (result.status !== 0) {
    if (spinner) spinner.fail(chalk.red("✕ Could not install Conny's required Python packages."));
    if (result.stderr) console.error(chalk.red(result.stderr.toString()));
    process.exit(1);
  }

  const requirementsPath = path.join(repoDir, "requirements.txt");
  if (fs.existsSync(requirementsPath)) {
    if (spinner) {
      spinner.text = chalk.hex('#8B5CF6')("Installing optional production dependencies...");
    }
    result = spawnSync(
      runtime,
      ["-m", "pip", "install", "--disable-pip-version-check", "-r", requirementsPath],
      { stdio: ["ignore", "pipe", "pipe"], env: process.env }
    );
    if (result.status !== 0 && !allowFullFailure) {
      if (spinner) spinner.fail(chalk.red("✕ Could not install requirements.txt."));
      if (result.stderr) console.error(chalk.red(result.stderr.toString()));
      process.exit(1);
    }
    if (result.status !== 0 && spinner) {
      spinner.text = chalk.hex('#8B5CF6')("Optional dependencies skipped; CLI runtime is ready.");
    }
  }

  if (!runtimeLooksHealthy(runtime)) {
    if (spinner) spinner.fail(chalk.red("✕ Runtime verification failed after dependency installation."));
    process.exit(1);
  }
}

function ensureRuntime(spinner) {
  let runtime = resolveRuntime();
  if (runtime && runtimeLooksHealthy(runtime)) {
    return runtime;
  }
  if (runtime && !runtimeLooksHealthy(runtime)) {
    try {
      fs.rmSync(runtimeDir, { recursive: true, force: true });
    } catch (_err) {
      // ignore
    }
    runtime = "";
  }

  let localSpinner = spinner;
  if (!localSpinner) {
    localSpinner = ora({
      text: chalk.hex('#8B5CF6')("Iniciando Conny..."),
      color: "magenta"
    }).start();
  }

  const python = findSystemPython();
  if (!python) {
    const errMsg = process.platform === "win32"
      ? "✕ No encontré Python 3.9+ en este host. Instálalo y vuelve a ejecutar `conny`."
      : "✕ No encontré python3/python 3.9+ en este host. Instálalo y vuelve a ejecutar `conny`.";
    localSpinner.fail(chalk.red(errMsg));
    process.exit(1);
  }

  localSpinner.text = chalk.hex('#8B5CF6')("Creando entorno virtual de Python...");
  let result = spawnSync(python.command, [...python.prefixArgs, "-m", "venv", runtimeDir], {
    stdio: ["ignore", "pipe", "pipe"],
    env: process.env,
  });
  if (result.status !== 0) {
    localSpinner.fail(chalk.red("✕ No se pudo crear el entorno virtual de Python."));
    if (result.stderr) console.error(chalk.red(result.stderr.toString()));
    process.exit(1);
  }

  runtime = resolveRuntime();
  if (!runtime) {
    localSpinner.fail(chalk.red(`✕ No pude crear el runtime aislado en ${runtimeDir}`));
    process.exit(1);
  }

  localSpinner.text = chalk.hex('#8B5CF6')("Actualizando pip...");
  result = spawnSync(runtime, ["-m", "pip", "install", "--disable-pip-version-check", "--upgrade", "pip"], {
    stdio: ["ignore", "pipe", "pipe"],
    env: process.env,
  });
  if (result.status !== 0) {
    localSpinner.fail(chalk.red("✕ Falló la actualización de pip."));
    if (result.stderr) console.error(chalk.red(result.stderr.toString()));
    process.exit(1);
  }

  installRuntimeDependencies(runtime, localSpinner, true);

  if (!spinner) {
    localSpinner.succeed(chalk.green("✓ Lista."));
  }

  return runtime;
}

function bootstrapFromPackage() {
  const spinner = ora({
    text: chalk.hex('#8B5CF6')("Iniciando Conny..."),
    color: "magenta"
  }).start();

  try {
    ensureDir(connyHome);
    syncTree(packageRoot, repoDir);
    if (!fs.existsSync(workspaceConfigPath)) {
      fs.writeFileSync(
        workspaceConfigPath,
        JSON.stringify(
          {
            owner_name: "",
            default_business_name: "",
            default_sector: "",
            default_platform: "telegram",
            public_base_url: "",
            telegram_token: "",
            telegram_shared: false,
            llm_keys: {},
            search_keys: {},
            meta: {},
            nova: {},
            omni: {},
            agent: {
              display_name: "Conny",
              role: "asesora virtual",
              prompt_master: "",
            },
          },
          null,
          2
        )
      );
    }
    console.log(chalk.hex("#8B5CF6")("Verifying Python dependencies..."));
    const runtime = resolveRuntime() || ensureRuntime(spinner);
    installRuntimeDependencies(runtime, spinner, true);

    if (!fs.existsSync(sharedTelegramRoutesPath)) {
      fs.writeFileSync(sharedTelegramRoutesPath, JSON.stringify({ default_instance: "", routes: {} }, null, 2));
    }
    ensureDir(path.join(connyHome, "instances"));
    ensureRuntime(spinner);
    spinner.succeed(chalk.green("✓ Lista."));
  } catch (err) {
    spinner.fail(chalk.red(`✕ Error durante el onboarding: ${err.message}`));
    process.exit(1);
  }
}

function needsBootstrap() {
  if (!fs.existsSync(entrypoint)) {
    return true;
  }
  const runtime = resolveRuntime();
  if (!runtime) {
    return true;
  }
  if (!runtimeLooksHealthy(runtime)) {
    return true;
  }
  if (readInstalledVersion() !== packageVersion) {
    return true;
  }
  return process.env.CONNY_FORCE_SYNC === "1";
}

function execConny(argv) {
  const runtime = resolveRuntime();
  if (!runtime || !fs.existsSync(entrypoint)) {
    return false;
  }
  const result = runAndReturn(
    runtime,
    [entrypoint, ...argv],
    {
      CONNY_HOME: connyHome,
      CONNY_DIR: repoDir,
      INSTANCES_DIR: process.env.INSTANCES_DIR || path.join(connyHome, "instances"),
      CONNY_BACKUPS: process.env.CONNY_BACKUPS || path.join(connyHome, "backups"),
      CONNY_SHARED_TELEGRAM_ROUTES:
        process.env.CONNY_SHARED_TELEGRAM_ROUTES || sharedTelegramRoutesPath,
      CONNY_WORKSPACE_CONFIG: process.env.CONNY_WORKSPACE_CONFIG || workspaceConfigPath,
    }
  );
  if (typeof result.status === "number") {
    process.exit(result.status);
  }
  process.exit(1);
}

const args = process.argv.slice(2);
const isHelp = args.length === 0 || args.includes("-h") || args.includes("--help") || args.includes("help");
const isVersion = args.includes("-v") || args.includes("--version") || args.includes("version");
const isBootstrapCheck = args.includes("--bootstrap-check");
const isJson = args.includes("--json");

if (isVersion) {
  if (isJson) {
    console.log(JSON.stringify({ version: packageVersion }));
  } else {
    console.log(`conny ${packageVersion}`);
  }
  process.exit(0);
}

if (needsBootstrap()) {
  bootstrapFromPackage();
}

if (isBootstrapCheck) {
  const runtime = resolveRuntime();
  if (!runtime || !runtimeLooksHealthy(runtime)) {
    fail(`Conny runtime is not ready in ${connyHome}`);
  }
  console.log(`conny runtime ok ${packageVersion}`);
  process.exit(0);
}

if (isHelp) {
  printBanner();
  printCommands();
  process.exit(0);
}

if (!isJson && process.stdout.isTTY) {
  printBanner();
}

if (!execConny(args)) {
  fail(`No pude iniciar Conny desde ${connyHome}`);
}
