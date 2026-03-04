
try:
	import pymysql

	pymysql.install_as_MySQLdb()
except Exception:
	# Si PyMySQL no está instalado o falla, Django usará el backend por defecto.
	pass
