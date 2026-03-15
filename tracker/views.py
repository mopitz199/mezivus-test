from django.db import connection
from django.http import JsonResponse


def database_health(request):
	try:
		with connection.cursor() as cursor:
			cursor.execute("SELECT 1")
			cursor.fetchone()

		return JsonResponse({"database": "ok"}, status=200)
	except Exception as exc:
		return JsonResponse(
			{"database": "error", "detail": str(exc)},
			status=500,
		)
