import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# I need to change:
#         const dayAppointments = globalAppointmentsList.filter(apt => {
#             if (!apt.datetime_slot) return false;
#             return apt.datetime_slot.startsWith(dateString);
#         });
# To:
#         const dayAppointments = globalAppointmentsList.filter(apt => {
#             if (!apt.datetime_slot) return false;
#             const d = new Date(apt.datetime_slot);
#             return d.getFullYear() === year && d.getMonth() === month && d.getDate() === day;
#         });

js = re.sub(
    r"const dayAppointments = globalAppointmentsList\.filter\(apt => \{.*?return apt\.datetime_slot\.startsWith\(dateString\);\s*\}\);",
    """const dayAppointments = globalAppointmentsList.filter(apt => {
            if (!apt.datetime_slot) return false;
            const d = new Date(apt.datetime_slot);
            return d.getFullYear() === year && d.getMonth() === month && d.getDate() === day;
        });""",
    js, flags=re.DOTALL
)

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
