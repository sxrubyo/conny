module.exports = {
  apps: [
    {
      name: "conny",
      script: "/home/ubuntu/conny/run.sh",
      cwd: "/home/ubuntu/conny",
      restart_delay: 3000,
      max_restarts: 10,
      out_file: "/home/ubuntu/conny/logs/conny.log",
      error_file: "/home/ubuntu/conny/logs/conny-error.log",
      watch: false,
    },
    {
      name: "whatsapp-bridge",
      script: "/home/ubuntu/whatsapp-bridge/start.sh",
      cwd: "/home/ubuntu/whatsapp-bridge",
      restart_delay: 3000,
      max_restarts: 10,
      out_file: "/home/ubuntu/whatsapp-bridge/logs/bridge.log",
      error_file: "/home/ubuntu/whatsapp-bridge/logs/bridge-error.log",
      watch: false,
    },
    {
      name: "conny-clinica-de-las-americas",
      script: "/home/ubuntu/conny-instances/clinica-de-las-americas/run.sh",
      cwd: "/home/ubuntu/conny-instances/clinica-de-las-americas",
      restart_delay: 3000,
      max_restarts: 10,
      out_file: "/home/ubuntu/conny-instances/clinica-de-las-americas/logs/conny.log",
      error_file: "/home/ubuntu/conny-instances/clinica-de-las-americas/logs/error.log",
      watch: false,
    }
  ]
};
