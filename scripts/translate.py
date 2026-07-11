with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    c = f.read()

c = c.replace(">Features<", ">Características<")
c = c.replace(">How it Works<", ">Cómo Funciona<")
c = c.replace(">Pricing<", ">Precios<")
c = c.replace(">Sign In<", ">Iniciar Sesión<")
c = c.replace(">Get Started<", ">Comenzar<")
c = c.replace(">See the business model &rarr;<", ">Ver el modelo de negocio &rarr;<")
c = c.replace(">Calculate Your MRR<", ">Calcula tus Ingresos (MRR)<")
c = c.replace(">Active Clients<", ">Clientes Activos<")
c = c.replace(">Average Monthly Charge<", ">Cobro Mensual Promedio<")
c = c.replace(">Monthly Revenue<", ">Ingreso Mensual<")
c = c.replace(">API Cost<", ">Costo de API<")
c = c.replace(">Annual Projection<", ">Proyección Anual<")

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(c)
