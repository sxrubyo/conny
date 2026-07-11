with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

vars_to_add = """
var profileClinicName = document.getElementById('profile-clinic-name');
var profileClinicPhone = document.getElementById('profile-clinic-phone');
var clinicInitials = document.getElementById('clinic-initials');
var profileServicesList = document.getElementById('profile-services-list');
var chatsList = document.getElementById('chats-list');
var appointmentsList = document.getElementById('appointments-list');
var profileMetrics = document.getElementById('profile-metrics');
"""

js = vars_to_add + "\n" + js

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
